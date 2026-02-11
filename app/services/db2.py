import pyodbc
from app.config import DB2_CONNECTION_STRING


def get_connection():
    return pyodbc.connect(DB2_CONNECTION_STRING)


def _strip_row(columns, row):
    return {
        col: val.strip() if isinstance(val, str) else val
        for col, val in zip(columns, row)
    }


def _is_upc(term):
    """Check if search term looks like a UPC barcode (8-14 digits)."""
    return term.isdigit() and 8 <= len(term) <= 14


def _build_fuzzy_where(words):
    """Build WHERE clause that matches all words against description or brand.

    Each word must appear in either DESCRIPTION or BRAND.
    Returns (clause_string, params_list).
    """
    conditions = []
    params = []
    for word in words:
        like = f"%{word.upper()}%"
        conditions.append(
            "(UPPER(i.DESCRIPTION) LIKE ? OR UPPER(e.BRAND) LIKE ? "
            "OR UPPER(i.MFG_NO) LIKE ?)"
        )
        params.extend([like, like, like])
    return " AND ".join(conditions), params


def search_items(term):
    """Fuzzy search items by description, brand, SKU, or MFG number.

    Splits search term into words — all words must match somewhere.
    Results ordered by average weekly movement (highest first).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if term.isdigit():
            like_term = f"%{term.upper()}%"
            cursor.execute(
                "SELECT i.SKU, i.DESCRIPTION, i.SIZE, i.QTY2, "
                "i.UPC1, i.MFG_NO, "
                "e.BRAND, "
                "b.QOH_2, "
                "TRIM(l.LOCATION) AS LOCATION, "
                "COALESCE(m.NEW_FORECAST, 0) AS AVG_MOVEMENT "
                "FROM longmod.VITEMS i "
                "LEFT JOIN longmod.VITEM_EXT e ON i.SKU = e.SKU "
                "LEFT JOIN longmod.VITEM_BALANCE b ON i.SKU = b.SKU "
                "LEFT JOIN longmod.VLOCATIONS l ON i.SKU = l.SKU "
                "LEFT JOIN longmod.VITEM_MOVEMENT m ON i.SKU = m.SKU "
                "WHERE i.SKU = ? OR UPPER(i.DESCRIPTION) LIKE ? "
                "ORDER BY COALESCE(m.NEW_FORECAST, 0) DESC "
                "FETCH FIRST 50 ROWS ONLY",
                (int(term), like_term),
            )
        else:
            words = term.split()
            if not words:
                return []
            where_clause, params = _build_fuzzy_where(words)
            cursor.execute(
                "SELECT i.SKU, i.DESCRIPTION, i.SIZE, i.QTY2, "
                "i.UPC1, i.MFG_NO, "
                "e.BRAND, "
                "b.QOH_2, "
                "TRIM(l.LOCATION) AS LOCATION, "
                "COALESCE(m.NEW_FORECAST, 0) AS AVG_MOVEMENT "
                "FROM longmod.VITEMS i "
                "LEFT JOIN longmod.VITEM_EXT e ON i.SKU = e.SKU "
                "LEFT JOIN longmod.VITEM_BALANCE b ON i.SKU = b.SKU "
                "LEFT JOIN longmod.VLOCATIONS l ON i.SKU = l.SKU "
                "LEFT JOIN longmod.VITEM_MOVEMENT m ON i.SKU = m.SKU "
                f"WHERE {where_clause} "
                "ORDER BY COALESCE(m.NEW_FORECAST, 0) DESC "
                "FETCH FIRST 50 ROWS ONLY",
                params,
            )

        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def search_by_upc(upc):
    """Search items by UPC barcode. Matches against UPC1, UPC2, UPC3.

    Results ordered by average weekly movement (highest first).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT i.SKU, i.DESCRIPTION, i.SIZE, i.QTY2, "
            "i.UPC1, i.UPC2, i.UPC3, i.MFG_NO, "
            "e.BRAND, "
            "b.QOH_2, "
            "TRIM(l.LOCATION) AS LOCATION, "
            "COALESCE(m.NEW_FORECAST, 0) AS AVG_MOVEMENT "
            "FROM longmod.VITEMS i "
            "LEFT JOIN longmod.VITEM_EXT e ON i.SKU = e.SKU "
            "LEFT JOIN longmod.VITEM_BALANCE b ON i.SKU = b.SKU "
            "LEFT JOIN longmod.VLOCATIONS l ON i.SKU = l.SKU "
            "LEFT JOIN longmod.VITEM_MOVEMENT m ON i.SKU = m.SKU "
            "WHERE TRIM(i.UPC1) = ? OR TRIM(i.UPC2) = ? OR TRIM(i.UPC3) = ? "
            "ORDER BY COALESCE(m.NEW_FORECAST, 0) DESC "
            "FETCH FIRST 50 ROWS ONLY",
            (upc, upc, upc),
        )

        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_item_detail(sku):
    """Get full item detail by SKU, including vendor info."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT i.SKU, i.STATUS, i.DESCRIPTION, i.SIZE, i.QTY2, "
            "i.UPC1, i.UPC2, i.UPC3, i.UPC4, "
            "i.MFG_NO, i.CATEGORY, i.SALES_CLASS, i.PRODUCT_CLASS, "
            "i.VENDOR_NO, i.DATEADDED, i.MSRP, "
            "i.WEIGHT1, i.WEIGHT2, "
            "e.BRAND, e.EXTENDED_DESCRIPTION, "
            "b.QOH_2, b.NET_COST, b.WHOLESALE_PRICE, "
            "b.LAST_RECEIPT_COST, b.AVG_INV_COST, "
            "b.DATE_LR, b.DATE_LA, b.LAST_SALE, "
            "b.QTY_UOM2_PTD, b.QTY_UOM2_YTD, "
            "TRIM(l.LOCATION) AS LOCATION, "
            "COALESCE(m.NEW_FORECAST, 0) AS AVG_MOVEMENT, "
            "TRIM(v.VENDOR_NAME) AS VENDOR_NAME, "
            "TRIM(v.VENDOR_CITY) AS VENDOR_CITY, "
            "TRIM(v.VENDOR_STATE) AS VENDOR_STATE, "
            "v.VENDOR_PHONE_NUMBER AS VENDOR_PHONE, "
            "TRIM(v.VENDOR_CONTACT_1) AS VENDOR_CONTACT "
            "FROM longmod.VITEMS i "
            "LEFT JOIN longmod.VITEM_EXT e ON i.SKU = e.SKU "
            "LEFT JOIN longmod.VITEM_BALANCE b ON i.SKU = b.SKU "
            "LEFT JOIN longmod.VLOCATIONS l ON i.SKU = l.SKU "
            "LEFT JOIN longmod.VITEM_MOVEMENT m ON i.SKU = m.SKU "
            "LEFT JOIN longmod.VVENDORS v ON i.VENDOR_NO = v.VENDOR_NUMBER "
            "WHERE i.SKU = ?",
            (sku,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        return _strip_row(columns, row)
    finally:
        conn.close()

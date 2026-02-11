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


def search_items(term):
    """Search items by description, brand, SKU, or MFG number.

    Returns list of dicts with item details + inventory info.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        like_term = f"%{term.upper()}%"

        if term.isdigit():
            # Numeric: search SKU exactly or description
            cursor.execute(
                "SELECT i.SKU, i.DESCRIPTION, i.SIZE, i.QTY2, "
                "i.UPC1, i.MFG_NO, "
                "e.BRAND, "
                "b.QOH_2 "
                "FROM longmod.VITEMS i "
                "LEFT JOIN longmod.VITEM_EXT e ON i.SKU = e.SKU "
                "LEFT JOIN longmod.VITEM_BALANCE b ON i.SKU = b.SKU "
                "WHERE i.SKU = ? OR UPPER(i.DESCRIPTION) LIKE ? "
                "ORDER BY i.DESCRIPTION "
                "FETCH FIRST 50 ROWS ONLY",
                (int(term), like_term),
            )
        else:
            cursor.execute(
                "SELECT i.SKU, i.DESCRIPTION, i.SIZE, i.QTY2, "
                "i.UPC1, i.MFG_NO, "
                "e.BRAND, "
                "b.QOH_2 "
                "FROM longmod.VITEMS i "
                "LEFT JOIN longmod.VITEM_EXT e ON i.SKU = e.SKU "
                "LEFT JOIN longmod.VITEM_BALANCE b ON i.SKU = b.SKU "
                "WHERE UPPER(i.DESCRIPTION) LIKE ? "
                "OR UPPER(e.BRAND) LIKE ? "
                "OR UPPER(i.MFG_NO) LIKE ? "
                "ORDER BY i.DESCRIPTION "
                "FETCH FIRST 50 ROWS ONLY",
                (like_term, like_term, like_term),
            )

        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def search_by_upc(upc):
    """Search items by UPC barcode. Matches against UPC1, UPC2, UPC3.

    Returns list of dicts with item details + inventory info.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Pad/trim UPC for matching — AS400 fields are padded
        cursor.execute(
            "SELECT i.SKU, i.DESCRIPTION, i.SIZE, i.QTY2, "
            "i.UPC1, i.UPC2, i.UPC3, i.MFG_NO, "
            "e.BRAND, "
            "b.QOH_2 "
            "FROM longmod.VITEMS i "
            "LEFT JOIN longmod.VITEM_EXT e ON i.SKU = e.SKU "
            "LEFT JOIN longmod.VITEM_BALANCE b ON i.SKU = b.SKU "
            "WHERE TRIM(i.UPC1) = ? OR TRIM(i.UPC2) = ? OR TRIM(i.UPC3) = ? "
            "FETCH FIRST 50 ROWS ONLY",
            (upc, upc, upc),
        )

        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()

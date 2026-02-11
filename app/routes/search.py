from flask import Blueprint, render_template, request, jsonify
from app.services.db2 import search_items, search_by_upc, get_item_detail, _is_upc

bp = Blueprint("search", __name__)


@bp.route("/")
def index():
    query = request.args.get("q", "").strip()
    results = []
    error = None
    search_type = None

    if query:
        try:
            if _is_upc(query):
                search_type = "upc"
                results = search_by_upc(query)
            else:
                search_type = "text"
                results = search_items(query)
        except Exception as e:
            error = str(e)

    return render_template(
        "search.html",
        query=query,
        results=results,
        error=error,
        search_type=search_type,
    )


@bp.route("/item/<int:sku>")
def item_detail(sku):
    error = None
    item = None

    try:
        item = get_item_detail(sku)
    except Exception as e:
        error = str(e)

    if not item and not error:
        error = "Item not found."

    return render_template("detail.html", item=item, error=error)


@bp.route("/api/search")
def api_search():
    """JSON endpoint for AJAX searches."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": [], "error": None})

    try:
        if _is_upc(query):
            results = search_by_upc(query)
        else:
            results = search_items(query)

        for r in results:
            for k, v in r.items():
                if hasattr(v, "as_tuple"):
                    r[k] = float(v)

        return jsonify({"results": results, "error": None})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

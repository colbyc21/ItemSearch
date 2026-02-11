document.addEventListener("DOMContentLoaded", function () {
    var searchInput = document.getElementById("searchInput");
    var searchForm = document.getElementById("searchForm");
    var resultsContainer = document.getElementById("resultsContainer");
    var debounceTimer = null;
    var currentRequest = null;

    // Keep focus on search input for physical barcode scanners
    searchInput.focus();

    // Prevent form submit — let live search handle it
    searchForm.addEventListener("submit", function (e) {
        e.preventDefault();
        doSearch(searchInput.value.trim());
    });

    // Debounced live search on keystroke
    searchInput.addEventListener("input", function () {
        var q = searchInput.value.trim();
        clearTimeout(debounceTimer);

        if (!q) {
            resultsContainer.innerHTML = "";
            updateUrl("");
            return;
        }

        debounceTimer = setTimeout(function () {
            doSearch(q);
        }, 250);
    });

    function doSearch(q) {
        if (!q) {
            resultsContainer.innerHTML = "";
            updateUrl("");
            return;
        }

        // Abort any in-flight request
        if (currentRequest) currentRequest.abort();

        var controller = new AbortController();
        currentRequest = controller;

        resultsContainer.innerHTML =
            '<div class="text-muted mt-3"><span class="spinner-border spinner-border-sm me-2"></span>Searching...</div>';

        fetch("/api/search?q=" + encodeURIComponent(q), { signal: controller.signal })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                currentRequest = null;
                updateUrl(q);
                renderResults(q, data);
            })
            .catch(function (err) {
                if (err.name !== "AbortError") {
                    currentRequest = null;
                    resultsContainer.innerHTML =
                        '<div class="alert alert-danger mt-3">Search failed: ' + err.message + "</div>";
                }
            });
    }

    function updateUrl(q) {
        var url = q ? "/?q=" + encodeURIComponent(q) : "/";
        history.replaceState(null, "", url);
    }

    function renderResults(query, data) {
        if (data.error) {
            resultsContainer.innerHTML =
                '<div class="alert alert-danger mt-3">Database error: ' + escapeHtml(data.error) + "</div>";
            return;
        }

        var results = data.results;
        var count = results.length;
        var html = "";

        html += '<div class="results-meta mt-3 mb-2"><span class="text-muted">' +
            count + " result" + (count !== 1 ? "s" : "") +
            ' for "' + escapeHtml(query) + '"</span></div>';

        if (count === 0) {
            html += '<div class="alert alert-warning mt-3">No items found.</div>';
            resultsContainer.innerHTML = html;
            return;
        }

        if (count === 1) {
            var item = results[0];
            var sku = parseInt(item.SKU, 10);
            html += renderItemCard(item, sku);
            resultsContainer.innerHTML = html;
            return;
        }

        html += '<div class="table-responsive"><table class="table data-table">' +
            "<thead><tr>" +
            "<th>SKU</th><th>Description</th><th>Size</th><th>Pack</th><th>Location</th><th>QOH</th>" +
            "</tr></thead><tbody>";

        for (var i = 0; i < results.length; i++) {
            var item = results[i];
            var sku = parseInt(item.SKU, 10);
            html += '<tr class="clickable-row" onclick="window.location=\'/item/' + sku + '\'">' +
                '<td class="fw-bold">' + sku + "</td>" +
                "<td>" + escapeHtml(item.DESCRIPTION || "") + "</td>" +
                "<td>" + escapeHtml(item.SIZE || "") + "</td>" +
                "<td>" + (item.QTY2 != null ? item.QTY2 : "") + "</td>" +
                '<td class="text-nowrap">' + escapeHtml(item.LOCATION || "") + "</td>" +
                "<td>" + (item.QOH_2 != null ? item.QOH_2 : "-") + "</td>" +
                "</tr>";
        }

        html += "</tbody></table></div>";
        resultsContainer.innerHTML = html;
    }

    function renderItemCard(item, sku) {
        return '<div class="item-card" onclick="window.location=\'/item/' + sku + '\'">' +
            '<div class="item-card-header">' +
                '<h5 class="item-card-title">' + escapeHtml(item.DESCRIPTION || "") + '</h5>' +
                '<span class="sku-badge">SKU ' + sku + '</span>' +
            '</div>' +
            '<div class="item-card-grid">' +
                '<div class="item-card-field">' +
                    '<div class="item-card-label">Size</div>' +
                    '<div class="item-card-value">' + escapeHtml(item.SIZE || "—") + '</div>' +
                '</div>' +
                '<div class="item-card-field">' +
                    '<div class="item-card-label">Pack</div>' +
                    '<div class="item-card-value">' + (item.QTY2 != null ? item.QTY2 : "—") + '</div>' +
                '</div>' +
                '<div class="item-card-field">' +
                    '<div class="item-card-label">Location</div>' +
                    '<div class="item-card-value">' + escapeHtml(item.LOCATION || "—") + '</div>' +
                '</div>' +
                '<div class="item-card-field">' +
                    '<div class="item-card-label">QOH</div>' +
                    '<div class="item-card-value">' + (item.QOH_2 != null ? item.QOH_2 : "—") + '</div>' +
                '</div>' +
            '</div>' +
            '<div class="item-card-tap">Tap for full details</div>' +
        '</div>';
    }

    function escapeHtml(str) {
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

});

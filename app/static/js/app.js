document.addEventListener("DOMContentLoaded", function () {
    var searchInput = document.getElementById("searchInput");
    var scanBtn = document.getElementById("scanBtn");
    var stopScanBtn = document.getElementById("stopScanBtn");
    var scannerContainer = document.getElementById("scannerContainer");
    var searchForm = document.getElementById("searchForm");
    var html5QrCode = null;

    // Keep focus on search input for physical barcode scanners
    searchInput.focus();

    scanBtn.addEventListener("click", function () {
        scannerContainer.classList.remove("d-none");
        scanBtn.disabled = true;

        html5QrCode = new Html5Qrcode("reader");
        html5QrCode.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: { width: 250, height: 150 } },
            function (decodedText) {
                // Barcode scanned — populate input and submit
                searchInput.value = decodedText;
                stopScanner();
                searchForm.submit();
            },
            function () {
                // Scan error (ignore, keep scanning)
            }
        ).catch(function (err) {
            scannerContainer.innerHTML =
                '<div class="alert alert-warning">Camera not available: ' + err + "</div>";
        });
    });

    stopScanBtn.addEventListener("click", stopScanner);

    function stopScanner() {
        if (html5QrCode) {
            html5QrCode.stop().then(function () {
                html5QrCode.clear();
                html5QrCode = null;
            }).catch(function () {});
        }
        scannerContainer.classList.add("d-none");
        scanBtn.disabled = false;
        searchInput.focus();
    }
});

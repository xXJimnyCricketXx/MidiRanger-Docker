(function () {
    var modal = document.getElementById('logsModal');
    if (!modal) return;

    var content = document.getElementById('logContent');
    var filterButtons = modal.querySelectorAll('[data-log-filter]');
    var currentFilter = 'NORMAL';

    function loadLog() {
        fetch('/logs/content?filter=' + encodeURIComponent(currentFilter))
            .then(function (res) { return res.text(); })
            .then(function (html) {
                content.innerHTML = html;
                content.scrollTop = content.scrollHeight;
            });
    }

    filterButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            filterButtons.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
            currentFilter = btn.getAttribute('data-log-filter');
            loadLog();
        });
    });

    document.querySelectorAll('[data-modal-target="#logsModal"]').forEach(function (trigger) {
        trigger.addEventListener('click', loadLog);
    });

    var refreshBtn = document.getElementById('logRefresh');
    if (refreshBtn) refreshBtn.addEventListener('click', loadLog);

    var openBtn = document.getElementById('logOpenExternal');
    if (openBtn) {
        openBtn.addEventListener('click', function () {
            window.open('/logs/raw', '_blank');
        });
    }
})();

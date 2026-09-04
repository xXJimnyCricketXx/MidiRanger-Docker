(function () {
    var startBtn = document.getElementById('backupStartBtn');
    if (!startBtn) return;

    var modal = document.getElementById('backupModal');
    var trigger = document.querySelector('[data-modal-target="#backupModal"]');
    var bar = document.getElementById('backupProgressBar');
    var percentLabel = document.getElementById('backupPercent');
    var label = document.getElementById('backupLabel');
    var downloadLink = document.getElementById('backupDownloadLink');

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    function setProgress(percent, text) {
        bar.style.width = percent + '%';
        percentLabel.textContent = percent + '%';
        if (text) label.textContent = text;
    }

    // Entspricht dem Original, wo jedes erneute Öffnen einen frischen
    // BackupDialog erzeugt statt den alten Zustand zu behalten.
    function resetState() {
        startBtn.disabled = false;
        downloadLink.style.display = 'none';
        bar.style.width = '0%';
        percentLabel.textContent = '0%';
        label.textContent = '';
    }

    if (trigger) trigger.addEventListener('click', resetState);

    // Entspricht on_finished(): im Original schließt sich der Dialog direkt
    // nach Abschluss - bei uns erst nachdem der Download tatsächlich
    // angestoßen wurde.
    downloadLink.addEventListener('click', function () {
        modal.classList.remove('open');
    });

    // Feste Mindestdauer für die Balken-Animation, unabhängig davon wie
    // schnell der Server tatsächlich antwortet (sonst überholt die echte
    // Antwort die setTimeout()-Zwischenschritte und der Balken springt
    // ohne sichtbaren Durchlauf direkt auf 100%).
    startBtn.addEventListener('click', function () {
        startBtn.disabled = true;
        downloadLink.style.display = 'none';
        setProgress(0, 'Initialisiere Backup…');

        var steps = [
            { percent: 30, text: 'Initialisiere Backup…', at: 250 },
            { percent: 65, text: 'Erstelle ZIP-Datei…', at: 550 }
        ];
        var timers = steps.map(function (step) {
            return setTimeout(function () { setProgress(step.percent, step.text); }, step.at);
        });
        var minDuration = new Promise(function (resolve) { setTimeout(resolve, 900); });

        var request = fetch('/backup/create', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        }).then(function (res) { return res.json(); });

        Promise.all([request, minDuration])
            .then(function (results) {
                var json = results[0];
                timers.forEach(clearTimeout);
                startBtn.disabled = false;
                if (json.error) {
                    setProgress(0, 'Fehler beim Backup: ' + json.error);
                    return;
                }
                setProgress(100, 'Backup abgeschlossen!');
                downloadLink.href = '/backup/download/' + encodeURIComponent(json.filename);
                downloadLink.style.display = '';
            })
            .catch(function () {
                timers.forEach(clearTimeout);
                startBtn.disabled = false;
                setProgress(0, 'Fehler beim Backup.');
            });
    });
})();

(function () {
    var startBtn = document.getElementById('exportStartBtn');
    if (!startBtn) return;

    var modal = document.getElementById('exportModal');
    var trigger = document.querySelector('[data-modal-target="#exportModal"]');
    var bar = document.getElementById('exportProgressBar');
    var percentLabel = document.getElementById('exportPercent');
    var label = document.getElementById('exportLabel');
    var downloadLink = document.getElementById('exportDownloadLink');

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
    // ExportDialog erzeugt statt den alten Zustand zu behalten.
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
        setProgress(0, 'Exportiere ausgewählte Songs…');

        var steps = [
            { percent: 30, text: 'Exportiere ausgewählte Songs…', at: 250 },
            { percent: 65, text: 'Erstelle ZIP-Datei…', at: 550 }
        ];
        var timers = steps.map(function (step) {
            return setTimeout(function () { setProgress(step.percent, step.text); }, step.at);
        });
        var minDuration = new Promise(function (resolve) { setTimeout(resolve, 900); });

        var request = fetch('/export/create', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        }).then(function (res) { return res.json(); });

        Promise.all([request, minDuration])
            .then(function (results) {
                var json = results[0];
                timers.forEach(clearTimeout);
                startBtn.disabled = false;
                if (json.error) {
                    setProgress(0, json.error);
                    return;
                }
                setProgress(100, json.count + ' Songs exportiert!');
                downloadLink.href = '/export/download/' + encodeURIComponent(json.filename);
                downloadLink.style.display = '';
            })
            .catch(function () {
                timers.forEach(clearTimeout);
                startBtn.disabled = false;
                setProgress(0, 'Fehler beim Export.');
            });
    });
})();

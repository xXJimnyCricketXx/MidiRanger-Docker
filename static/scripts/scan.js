(function () {
    var trigger = document.querySelector('[data-modal-target="#scanModal"]');
    if (!trigger) return;

    var label = document.getElementById('scanLabel');
    var bar = document.getElementById('scanProgressBar');
    var percentLabel = document.getElementById('scanPercent');
    var list = document.getElementById('scanList');
    var closeBtn = document.getElementById('scanCloseBtn');
    var closeRow = document.getElementById('scanCloseRow');
    var confirmRow = document.getElementById('scanConfirmRow');
    var declineBtn = document.getElementById('scanDeclineBtn');
    var importBtn = document.getElementById('scanImportBtn');

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    function setProgress(percent, text) {
        bar.style.width = percent + '%';
        percentLabel.textContent = percent + '%';
        label.textContent = text;
    }

    function pluralSongs(n) {
        return n === 1 ? 'Song' : 'Songs';
    }

    function wurde(n) {
        return n === 1 ? 'Es wurde' : 'Es wurden';
    }

    function postJson(url) {
        return fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        }).then(function (res) { return res.json(); });
    }

    // Läuft die Balken-Animation über eine feste Mindestdauer, unabhängig
    // davon wie schnell die Server-Antwort tatsächlich ankommt (sonst
    // überholt die Antwort die Zwischenschritte, siehe Metadaten-Analyse/
    // Datenbank prüfen).
    function runWithProgress(url, steps, onDone) {
        var timers = steps.map(function (step) {
            return setTimeout(function () { setProgress(step.percent, step.text); }, step.at);
        });
        var minDuration = new Promise(function (resolve) { setTimeout(resolve, 900); });

        Promise.all([postJson(url), minDuration])
            .then(function (results) {
                timers.forEach(clearTimeout);
                onDone(results[0]);
            })
            .catch(function () {
                timers.forEach(clearTimeout);
                setProgress(0, 'Fehler beim Scannen.');
                closeBtn.disabled = false;
            });
    }

    var needsReload = false;
    closeBtn.addEventListener('click', function () {
        if (needsReload) location.reload();
    });

    // Eigene Ja/Nein-Buttons statt confirm()/alert(), analog zu
    // "Datenbank prüfen".
    importBtn.addEventListener('click', function () {
        confirmRow.hidden = true;
        closeRow.hidden = false;
        list.innerHTML = '';
        setProgress(0, 'Importiere neue Songs …');

        runWithProgress('/tools/scan/import', [
            { percent: 30, text: 'Importiere neue Songs …', at: 250 },
            { percent: 65, text: 'Analysiere Dateien …', at: 550 }
        ], function (json) {
            setProgress(100, wurde(json.count) + ' ' + json.count + ' ' + pluralSongs(json.count) + ' zur Datenbank hinzugefügt.');
            closeBtn.disabled = false;
            needsReload = true;
        });
    });

    declineBtn.addEventListener('click', function () {
        confirmRow.hidden = true;
        closeRow.hidden = false;
        closeBtn.disabled = false;
    });

    // Entspricht ScannerDialog: der Scan startet sofort beim Öffnen (kein
    // eigener "Starten"-Button).
    trigger.addEventListener('click', function () {
        needsReload = false;
        closeBtn.disabled = true;
        confirmRow.hidden = true;
        closeRow.hidden = false;
        list.innerHTML = '';
        setProgress(0, 'Scanner gestartet:');

        runWithProgress('/tools/scan', [
            { percent: 30, text: 'Durchsuche midi/-Verzeichnis …', at: 250 },
            { percent: 65, text: 'Vergleiche mit der Datenbank …', at: 550 }
        ], function (json) {
            if (json.count === 0) {
                setProgress(100, 'Es wurden keine neuen MIDI-Dateien gefunden.');
                closeBtn.disabled = false;
                return;
            }

            json.new_files.forEach(function (name) {
                var row = document.createElement('div');
                row.className = 'mr-scan-row';
                row.textContent = name;
                list.appendChild(row);
            });

            setProgress(100, wurde(json.count) + ' ' + json.count + ' ' + pluralSongs(json.count) + ' gefunden. Möchtest du sie zur Datenbank hinzufügen?');

            closeRow.hidden = true;
            confirmRow.hidden = false;
        });
    });
})();

(function () {
    var trigger = document.querySelector('[data-modal-target="#dbCheckModal"]');
    if (!trigger) return;

    var label = document.getElementById('dbCheckLabel');
    var bar = document.getElementById('dbCheckProgressBar');
    var percentLabel = document.getElementById('dbCheckPercent');
    var list = document.getElementById('dbCheckList');
    var closeBtn = document.getElementById('dbCheckCloseBtn');
    var closeRow = document.getElementById('dbCheckCloseRow');
    var confirmRow = document.getElementById('dbCheckConfirmRow');
    var flagBtn = document.getElementById('dbCheckFlagBtn');
    var deleteBtn = document.getElementById('dbCheckDeleteBtn');

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    function setProgress(percent, text) {
        bar.style.width = percent + '%';
        percentLabel.textContent = percent + '%';
        label.textContent = text;
    }

    function pluralEntry(n) {
        return n === 1 ? 'Eintrag' : 'Einträge';
    }

    function postForm(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: body || ''
        });
    }

    // Reload erst beim Schließen, damit das Endergebnis-Label sichtbar
    // bleibt (kein alert(), analog zur Metadaten-Analyse).
    var needsReload = false;
    closeBtn.addEventListener('click', function () {
        if (needsReload) location.reload();
    });

    // Eigene Ja/Nein-Buttons statt confirm(): kein Browser-Dialog, und der
    // fertige 100%-Zustand bleibt vor der Rückfrage sichtbar (ein blockierendes
    // confirm() reißt den Browser sonst mitten aus dem Rendern der Balken-
    // Animation heraus).
    function resolveDbCheck(action) {
        confirmRow.hidden = true;
        closeRow.hidden = false;
        setProgress(100, action === 'delete' ? 'Lösche Einträge …' : 'Markiere Einträge …');

        postForm('/tools/db-check/resolve', 'action=' + action)
            .then(function (res) { return res.json(); })
            .then(function (resolveJson) {
                if (resolveJson.action === 'delete') {
                    setProgress(100, '🗑️ ' + resolveJson.count + ' ' + pluralEntry(resolveJson.count) + ' gelöscht.');
                } else {
                    setProgress(100, '🏷️ ' + resolveJson.count + ' ' + pluralEntry(resolveJson.count) + " auf 'fehlend' markiert.");
                }
                closeBtn.disabled = false;
                needsReload = true;
            });
    }

    deleteBtn.addEventListener('click', function () { resolveDbCheck('delete'); });
    flagBtn.addEventListener('click', function () { resolveDbCheck('flag'); });

    // Entspricht DatabaseCheckDialog: die Prüfung startet sofort beim
    // Öffnen (kein eigener "Starten"-Button).
    trigger.addEventListener('click', function () {
        needsReload = false;
        closeBtn.disabled = true;
        confirmRow.hidden = true;
        closeRow.hidden = false;
        list.innerHTML = '';
        setProgress(0, 'Prüfe Datenbankeinträge ...');

        var steps = [
            { percent: 30, text: 'Prüfe Datenbankeinträge ...', at: 250 },
            { percent: 65, text: 'Vergleiche mit vorhandenen Dateien ...', at: 550 }
        ];
        var timers = steps.map(function (step) {
            return setTimeout(function () { setProgress(step.percent, step.text); }, step.at);
        });
        var minDuration = new Promise(function (resolve) { setTimeout(resolve, 900); });

        var request = fetch('/tools/db-check', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        }).then(function (res) { return res.json(); });

        Promise.all([request, minDuration])
            .then(function (results) {
                var json = results[0];
                timers.forEach(clearTimeout);

                if (json.count === 0) {
                    setProgress(100, '✅ Alle Dateien vorhanden.');
                    closeBtn.disabled = false;
                    needsReload = true;
                    return;
                }

                json.filenames.forEach(function (name) {
                    var row = document.createElement('div');
                    row.className = 'mr-dbcheck-row';
                    row.textContent = '❗ Fehlt: ' + name;
                    list.appendChild(row);
                });

                setProgress(100, json.count + ' ' + pluralEntry(json.count) + ' gefunden, deren Dateien fehlen. Sollen diese aus der Datenbank gelöscht werden?');

                closeRow.hidden = true;
                confirmRow.hidden = false;
            })
            .catch(function () {
                timers.forEach(clearTimeout);
                setProgress(0, 'Fehler bei der Datenbankprüfung.');
                closeBtn.disabled = false;
            });
    });
})();

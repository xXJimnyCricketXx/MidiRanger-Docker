(function () {
    var trigger = document.querySelector('[data-modal-target="#metadataModal"]');
    if (!trigger) return;

    var label = document.getElementById('metadataLabel');
    var bar = document.getElementById('metadataProgressBar');
    var percentLabel = document.getElementById('metadataPercent');
    var closeBtn = document.getElementById('metadataCloseBtn');

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    function setProgress(percent, text) {
        bar.style.width = percent + '%';
        percentLabel.textContent = percent + '%';
        label.textContent = text;
    }

    // Kein alert(): die Original-QMessageBox wird bewusst NICHT übernommen,
    // das Modal-Label selbst ist die einzige Rückmeldung. Reload erst beim
    // Schließen, damit "✅ Analyse abgeschlossen!" auch sichtbar bleibt
    // (ein sofortiger Reload würde das Modal direkt wieder verschwinden
    // lassen, bevor der Nutzer das Ergebnis überhaupt sieht).
    var needsReload = false;

    closeBtn.addEventListener('click', function () {
        if (needsReload) location.reload();
    });

    // Entspricht MetadataAnalyzerDialog: die Analyse startet sofort beim
    // Öffnen des Dialogs (kein eigener "Starten"-Button wie bei Backup/Export).
    //
    // Die Analyse selbst ist server-seitig meist in Millisekunden fertig -
    // ein reiner setTimeout()-Zwischenschritt käme dann nie zur Anzeige,
    // weil die echte Antwort ihn überholt. Deshalb läuft die Balken-Animation
    // über eine feste Mindestdauer, unabhängig davon wie schnell der Server
    // tatsächlich antwortet (Promise.all statt reinem setTimeout+clearTimeout).
    trigger.addEventListener('click', function () {
        needsReload = false;
        closeBtn.textContent = 'Abbrechen';
        setProgress(0, 'Analysiere MIDI-Dateien…');

        var steps = [
            { percent: 30, text: 'Analysiere MIDI-Dateien…', at: 250 },
            { percent: 65, text: 'Aktualisiere Datenbank…', at: 550 }
        ];
        var timers = steps.map(function (step) {
            return setTimeout(function () { setProgress(step.percent, step.text); }, step.at);
        });
        var minDuration = new Promise(function (resolve) { setTimeout(resolve, 900); });

        var request = fetch('/tools/metadata-analyze', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        }).then(function (res) { return res.json(); });

        Promise.all([request, minDuration])
            .then(function (results) {
                var json = results[0];
                timers.forEach(clearTimeout);
                closeBtn.textContent = 'Schließen';

                if (json.error) {
                    setProgress(0, json.error);
                    return;
                }

                setProgress(100, '✅ Analyse abgeschlossen!');
                needsReload = true;
            })
            .catch(function () {
                timers.forEach(clearTimeout);
                closeBtn.textContent = 'Schließen';
                setProgress(0, 'Fehler bei der Analyse.');
            });
    });
})();

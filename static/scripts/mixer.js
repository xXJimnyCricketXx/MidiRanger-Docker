// Mixer als Modal (entspricht MixerDialog im Original - ein Dialog, keine
// eigene Seite). Inhalt wird bei jedem Öffnen per AJAX neu geladen (frische
// Analyse, genau wie ein neu erzeugter MixerService im Original) und in
// #mixerModalBody eingefügt; die Interaktions-Logik muss deshalb nach jedem
// Laden neu verdrahtet werden (wireContent()).
(function () {
    var modal = document.getElementById('mixerModal');
    var body = document.getElementById('mixerModalBody');
    if (!modal || !body) return;

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    function postForm(url, bodyStr) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: bodyStr || ''
        }).then(function (res) { return res.json(); });
    }

    function closeModal() { modal.classList.remove('open'); }

    // #mixerModal hat keinen [data-modal-target]-Trigger im Menü (wird nur
    // programmatisch geöffnet) - Schließen-Wiring hier separat, per
    // Event-Delegation, da der Inhalt (inkl. Schließen-Button) bei jedem
    // Öffnen neu eingefügt wird.
    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });
    body.addEventListener('click', function (e) {
        if (e.target.closest('[data-modal-close]')) closeModal();
    });

    function openMixer(songId) {
        fetch('/mixer/' + songId)
            .then(function (res) { return res.text(); })
            .then(function (html) {
                body.innerHTML = html;
                modal.classList.add('open');
                wireContent();
            });
    }

    window.MRMixer = { open: openMixer };

    // Tools > Mixer öffnen: ermittelt zuerst den per Checkbox markierten Song.
    var toolsBtn = document.getElementById('mixerOpenBtn');
    if (toolsBtn) {
        toolsBtn.addEventListener('click', function () {
            fetch('/mixer', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
                .then(function (res) { return res.json(); })
                .then(function (json) {
                    if (json.error) { alert(json.error); return; }
                    openMixer(json.song_id);
                });
        });
    }

    function wireContent() {
        var songIdInput = document.getElementById('mixerSongId');
        if (!songIdInput) return; // Fehler-Fragment ohne Kanäle geladen
        var songId = songIdInput.value;

        var playBtn = document.getElementById('mixerPlayBtn');
        var stopBtn = document.getElementById('mixerStopBtn');
        if (playBtn) {
            playBtn.addEventListener('click', function () {
                postForm('/player/play/' + songId).then(function (json) {
                    if (json.error) alert(json.error);
                });
            });
        }
        if (stopBtn) {
            stopBtn.addEventListener('click', function () {
                postForm('/player/stop');
            });
        }

        var actions = document.getElementById('mixerActions');
        var exportConfirm = document.getElementById('mixerExportConfirm');
        var exportBtn = document.getElementById('mixerExportBtn');
        var exportYes = document.getElementById('mixerExportYes');
        var exportNo = document.getElementById('mixerExportNo');
        var exportResult = document.getElementById('mixerExportResult');

        if (exportBtn) {
            exportBtn.addEventListener('click', function () {
                actions.hidden = true;
                exportConfirm.hidden = false;
            });
            exportNo.addEventListener('click', function () {
                exportConfirm.hidden = true;
                actions.hidden = false;
            });
            exportYes.addEventListener('click', function () {
                exportConfirm.hidden = true;
                actions.hidden = false;

                postForm('/mixer/' + songId + '/export').then(function (json) {
                    if (json.error) {
                        exportResult.textContent = 'Fehler beim Export: ' + json.error;
                        return;
                    }
                    exportResult.innerHTML = 'Mixer-Edit gespeichert: ' +
                        '<a href="/mixer/download/' + encodeURIComponent(json.filename) + '">' + json.filename + '</a>';
                });
            });
        }

        document.querySelectorAll('.mixer-strip').forEach(function (strip) {
            var channel = strip.dataset.channel;

            var panSlider = strip.querySelector('.mixer-pan-slider');
            var panValue = strip.querySelector('.mixer-pan-value-num');
            panSlider.addEventListener('input', function () {
                panValue.textContent = panSlider.value;
            });
            panSlider.addEventListener('change', function () {
                postForm('/mixer/' + songId + '/pan', 'channel=' + channel + '&pan=' + panSlider.value);
            });

            var volumeSlider = strip.querySelector('.mixer-volume-slider');
            var volumeValue = strip.querySelector('.mixer-volume-value-num');
            volumeSlider.addEventListener('input', function () {
                postForm('/mixer/' + songId + '/volume', 'channel=' + channel + '&value=' + volumeSlider.value)
                    .then(function (json) {
                        if (json.volume_db) volumeValue.textContent = json.volume_db;
                    });
            });

            var soloBtn = strip.querySelector('.mixer-solo-btn');
            soloBtn.addEventListener('click', function () {
                var active = !soloBtn.classList.contains('active');
                soloBtn.classList.toggle('active', active);
                postForm('/mixer/' + songId + '/solo', 'channel=' + channel + '&solo=' + active);
            });

            var muteBtn = strip.querySelector('.mixer-mute-btn');
            muteBtn.addEventListener('click', function () {
                var active = !muteBtn.classList.contains('active');
                muteBtn.classList.toggle('active', active);
                postForm('/mixer/' + songId + '/mute', 'channel=' + channel + '&muted=' + active);
            });
        });
    }
})();

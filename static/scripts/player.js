// Globaler Player-Kram, der auf jeder Seite verfügbar ist (Statusleiste wird
// überall per partials/statusbar.html eingebunden). songs.js ruft die
// window.MRPlayer-Helfer auf, damit Play/Stop in der Songtabelle die
// Statusleiste ohne Reload mitaktualisieren.
(function () {
    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    function postJson(url) {
        return fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        }).then(function (res) { return res.json(); });
    }

    var center = document.getElementById('statusbarCenter');
    var left = document.getElementById('statusbarLeft');
    var statusTimer = null;

    // Entspricht StatusManager.show()/show_text(): Meldung anzeigen und nach
    // 3s automatisch wieder leeren (bei jeder neuen Meldung neu gestartet).
    function showStatus(text) {
        if (!left) return;
        left.textContent = text || '';
        if (statusTimer) clearTimeout(statusTimer);
        if (text) {
            statusTimer = setTimeout(function () { left.textContent = ''; }, 3000);
        }
    }

    // Serverseitig gerenderte Meldung (z.B. nach einem Redirect) läuft mit
    // derselben 3s-Regel weiter, statt dauerhaft stehen zu bleiben.
    if (left && left.textContent.trim()) {
        statusTimer = setTimeout(function () { left.textContent = ''; }, 3000);
    }

    function showNowPlaying(title, artist) {
        if (!center) return;
        var text = title || '';
        if (artist) text += ' – ' + artist;
        center.innerHTML =
            '<span class="statusbar-title" id="statusbarTitle"></span>' +
            '<button type="button" class="statusbar-stop-btn" id="statusbarStopBtn" aria-label="Stop">' +
            '<img src="/static/ressources/icons/stop.png" alt="Stop"></button>';
        document.getElementById('statusbarTitle').textContent = text;
        wireStopButton();
    }

    function clearNowPlaying() {
        if (!center) return;
        center.innerHTML = '';
    }

    function wireStopButton() {
        var btn = document.getElementById('statusbarStopBtn');
        if (!btn) return;
        btn.addEventListener('click', function () {
            postJson('/player/stop').then(function () {
                clearNowPlaying();
                if (window.MRPlayer && window.MRPlayer.onStopped) window.MRPlayer.onStopped();
            });
        });
    }

    wireStopButton();

    window.MRPlayer = {
        showNowPlaying: showNowPlaying,
        clearNowPlaying: clearNowPlaying,
        showStatus: showStatus,
        postJson: postJson,
        onStopped: null,
        onStarted: null
    };

    // Ersetzt Qt's Cross-Thread-Signal-Zustellung an die UI: läuft ein Song
    // von selbst aus (kein Klick nötig), bekommt der Browser das nur über
    // diesen WebSocket mit, nicht über die Antwort auf einen Request.
    function connectPlayerSocket() {
        var proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
        var socket = new WebSocket(proto + location.host + '/ws/player/');

        socket.onmessage = function (e) {
            var data = JSON.parse(e.data);
            if (data.event === 'started') {
                showNowPlaying(data.title, data.artist);
                if (window.MRPlayer.onStarted) window.MRPlayer.onStarted(data.id);
            } else if (data.event === 'stopped') {
                clearNowPlaying();
                if (window.MRPlayer.onStopped) window.MRPlayer.onStopped();
            } else if (data.event === 'status') {
                showStatus(data.text);
            }
        };

        // Einfacher Reconnect, falls die Verbindung abbricht (z.B. Server-Neustart).
        socket.onclose = function () {
            setTimeout(connectPlayerSocket, 2000);
        };
    }

    connectPlayerSocket();
})();

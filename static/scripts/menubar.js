(function () {
    var menus = document.querySelectorAll('.menubar .menu');

    function closeAllMenus(except) {
        menus.forEach(function (m) {
            if (m !== except) m.removeAttribute('open');
        });
    }

    menus.forEach(function (menu) {
        menu.addEventListener('toggle', function () {
            if (menu.open) closeAllMenus(menu);
        });
    });

    document.addEventListener('click', function (e) {
        if (!e.target.closest('.menubar .menu')) closeAllMenus(null);
    });

    menus.forEach(function (menu) {
        menu.querySelectorAll('.menu-dropdown a, .menu-dropdown button').forEach(function (item) {
            item.addEventListener('click', function () {
                if (item.id !== 'fullscreenToggle' && !item.classList.contains('menu-submenu-trigger')) {
                    menu.removeAttribute('open');
                }
            });
        });
    });

    // ---------------------------------------------------------------
    // Seitlich aufklappendes Untermenü (Pendant zu QMenu.addMenu(), z.B.
    // "Meine Playlists") - Klick/Tap statt Hover, damit es auf dem Tablet
    // funktioniert.
    // ---------------------------------------------------------------
    function closeAllSubmenus() {
        document.querySelectorAll('.menu-has-submenu.open').forEach(function (w) {
            w.classList.remove('open');
        });
    }

    document.querySelectorAll('.menu-submenu-trigger').forEach(function (trigger) {
        var wrapper = trigger.closest('.menu-has-submenu');
        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = wrapper.classList.contains('open');
            closeAllSubmenus();
            if (!isOpen) wrapper.classList.add('open');
        });
    });

    document.addEventListener('click', function (e) {
        if (!e.target.closest('.menu-has-submenu')) closeAllSubmenus();
    });

    // ---------------------------------------------------------------
    // Modale Popups (z.B. Dokumentation, Tastenkürzel) - ein Trigger mit
    // [data-modal-target="#id"] öffnet das .mr-modal-overlay mit dieser id.
    // ---------------------------------------------------------------
    function openModal(modal) {
        var frame = modal.querySelector('iframe[data-src]');
        if (frame && (!frame.src || frame.src === 'about:blank')) frame.src = frame.dataset.src;
        modal.classList.add('open');
    }

    function closeModal(modal) {
        modal.classList.remove('open');
    }

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    // Entspricht den logger.info()-Aufrufen in navigation_controller.py: die
    // Aktion selbst ist rein clientseitig (Modal), erzeugt im Original aber
    // trotzdem Logzeilen - hier per Fire-and-Forget-Beacon nachgebildet.
    function logEvent(name, extra) {
        fetch('/logs/event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'event=' + encodeURIComponent(name) + (extra || '')
        });
    }

    // Generischer [data-log-event]-Klick-Logger, auch für echte Links (Alle
    // Songs/Favoriten/Dashboard/Playlist) statt nur für Modal-Trigger: die
    // "Ansicht geöffnet"-Statusmeldung darf nur beim tatsächlichen Klick
    // feuern (wie im Original), nicht bei jedem Server-Rendern der Seite
    // (z.B. wenn ein Formular-POST danach wieder hierher zurück-redirected).
    document.querySelectorAll('[data-log-event]').forEach(function (el) {
        el.addEventListener('click', function () {
            var extra = el.dataset.logEventId ? '&id=' + encodeURIComponent(el.dataset.logEventId) : '';
            logEvent(el.dataset.logEvent, extra);
        });
    });

    document.querySelectorAll('[data-modal-target]').forEach(function (trigger) {
        var modal = document.querySelector(trigger.getAttribute('data-modal-target'));
        if (!modal) return;

        trigger.addEventListener('click', function () {
            openModal(modal);
        });

        modal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
            btn.addEventListener('click', function () { closeModal(modal); });
        });

        // Nur schließen, wenn direkt aufs Overlay (nicht auf die Box selbst) geklickt wird.
        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModal(modal);
        });
    });

    function closeAllModals() {
        document.querySelectorAll('.mr-modal-overlay.open').forEach(closeModal);
    }

    // Nach einem Formular-POST (z.B. Quelle/Playlist hinzufügen) bleibt das
    // Original-Dialogfenster offen und aktualisiert nur seine Liste. Da wir
    // hier per Redirect auf eine neu geladene Seite gehen, signalisiert der
    // Server das per #modal-id im Redirect-Ziel, damit das Modal sofort
    // wieder aufgeht statt geschlossen zu bleiben.
    if (location.hash) {
        var reopenTarget = document.getElementById(location.hash.slice(1));
        if (reopenTarget && reopenTarget.classList.contains('mr-modal-overlay')) {
            openModal(reopenTarget);
            history.replaceState(null, '', location.pathname + location.search);
        }
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeAllMenus(null);
            closeAllSubmenus();
            closeAllModals();
        }
    });

    // ---------------------------------------------------------------
    // Tastenkürzel aus utils/shortcuts.py (APP_SHORTCUTS) - Kombination aus
    // data-shortcut-Attribut im Markup ableiten und den jeweiligen Link/
    // Button auslösen, statt die Aktionen hier zu duplizieren.
    // ---------------------------------------------------------------
    var shortcutTargets = {};
    document.querySelectorAll('[data-shortcut]').forEach(function (el) {
        shortcutTargets[el.getAttribute('data-shortcut')] = el;
    });

    document.addEventListener('keydown', function (e) {
        var tag = (e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'select' || tag === 'textarea') return;

        var parts = [];
        if (e.ctrlKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');

        var key = e.key.toLowerCase();
        if (!['control', 'alt', 'shift'].includes(key)) parts.push(key);

        var target = shortcutTargets[parts.join('+')];
        if (target) {
            e.preventDefault();
            target.click();
        }
    });

    var fsBtn = document.getElementById('fullscreenToggle');
    if (fsBtn) {
        fsBtn.addEventListener('click', function () {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(function () {});
            } else {
                document.exitFullscreen();
            }
        });
    }

    // ---------------------------------------------------------------
    // Bearbeiten: "Zur Playlist hinzufügen" (Untermenü-Klick postet an
    // die jeweilige Playlist-ID) und "Playlist leeren" (Rückfrage,
    // Pendant zu QMessageBox.question in clear_current_playlist()).
    // ---------------------------------------------------------------
    var addToPlaylistForm = document.getElementById('addToPlaylistForm');
    document.querySelectorAll('.add-to-playlist-item').forEach(function (item) {
        item.addEventListener('click', function () {
            addToPlaylistForm.action = '/bearbeiten/add-to-playlist/' + item.dataset.playlistId;
            addToPlaylistForm.submit();
        });
    });

    var clearPlaylistBtn = document.getElementById('clearPlaylistBtn');
    var clearPlaylistForm = document.getElementById('clearPlaylistForm');
    if (clearPlaylistBtn) {
        clearPlaylistBtn.addEventListener('click', function () {
            if (confirm('Alle Songs aus dieser Playlist entfernen?')) {
                clearPlaylistForm.submit();
            }
        });
    }
})();

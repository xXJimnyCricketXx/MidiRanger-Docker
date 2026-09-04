(function () {
    var table = document.querySelector('.mr-song-table');
    if (!table) return;

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
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

    // ---------------------------------------------------------------
    // Checkbox-Spalte (is_selected) - Entspricht CheckboxDelegate: nur
    // die eine Zeile aktualisieren, kein Neuladen der Seite.
    // ---------------------------------------------------------------
    table.addEventListener('click', function (e) {
        var box = e.target.closest('.mr-check-box');
        if (!box) return;
        var row = box.closest('tr');
        var songId = row.dataset.songId;

        postForm('/songs/' + songId + '/toggle-selected').then(function (res) {
            if (!res.ok) return;
            return res.json();
        }).then(function (data) {
            if (!data) return;
            box.classList.toggle('checked', data.is_selected);
        });
    });

    // ---------------------------------------------------------------
    // Favoriten-Spalte (is_favorite) - Entspricht FavDelegate.
    // ---------------------------------------------------------------
    table.addEventListener('click', function (e) {
        var star = e.target.closest('.mr-fav-toggle');
        if (!star) return;
        var row = star.closest('tr');
        var songId = row.dataset.songId;

        postForm('/songs/' + songId + '/toggle-favorite').then(function (res) {
            if (!res.ok) return;
            return res.json();
        }).then(function (data) {
            if (!data) return;

            // Entspricht nav.refresh_current_view() im Original: in der
            // Favoriten-Ansicht muss die Zeile beim Entfavorisieren
            // verschwinden, nicht nur das Icon wechseln.
            if (table.hasAttribute('data-favorites-view')) {
                location.reload();
                return;
            }

            var base = star.src.slice(0, star.src.lastIndexOf('/') + 1);
            star.src = base + (data.is_favorite ? 'fav_on.png' : 'fav_off.png');
        });
    });

    // ---------------------------------------------------------------
    // Play/Stop-Icon - entspricht BaseTableView.on_play_clicked(): Klick auf
    // "Play" startet die Wiedergabe (stoppt automatisch einen ggf. schon
    // laufenden anderen Song, da nur einer gleichzeitig spielt), Klick auf
    // "Stop" (im aktuell spielenden Song) stoppt.
    // ---------------------------------------------------------------
    function resetPlayIcon(icon) {
        var base = icon.src.slice(0, icon.src.lastIndexOf('/') + 1);
        icon.src = base + 'play.png';
        icon.alt = 'Play';
        icon.dataset.action = 'play';
    }

    function setPlayingIcon(songId) {
        table.querySelectorAll('[data-action="play"], [data-action="stop"]').forEach(function (icon) {
            var row = icon.closest('tr');
            var base = icon.src.slice(0, icon.src.lastIndexOf('/') + 1);
            var isThisSong = String(row.dataset.songId) === String(songId);
            icon.src = base + (isThisSong ? 'stop.png' : 'play.png');
            icon.alt = isThisSong ? 'Stop' : 'Play';
            icon.dataset.action = isThisSong ? 'stop' : 'play';
        });
    }

    table.addEventListener('click', function (e) {
        var icon = e.target.closest('[data-action="play"], [data-action="stop"]');
        if (!icon) return;
        var row = icon.closest('tr');
        var songId = row.dataset.songId;

        if (icon.dataset.action === 'play') {
            postForm('/player/play/' + songId).then(function (res) { return res.json(); }).then(function (json) {
                if (json.error) { alert(json.error); return; }
                setPlayingIcon(songId);
                if (window.MRPlayer) window.MRPlayer.showNowPlaying(json.title, json.artist);
            });
        } else {
            postForm('/player/stop').then(function () {
                resetPlayIcon(icon);
                if (window.MRPlayer) window.MRPlayer.clearNowPlaying();
            });
        }
    });

    // WebSocket-Live-Status (player.js): hält Icon/Statusleiste auch dann
    // korrekt, wenn ein Song von selbst zu Ende ist oder die Wiedergabe von
    // einem anderen Tab/Gerät aus gestartet/gestoppt wurde.
    if (window.MRPlayer) {
        window.MRPlayer.onStarted = function (songId) {
            setPlayingIcon(songId);
        };
        window.MRPlayer.onStopped = function () {
            table.querySelectorAll('[data-action="stop"]').forEach(resetPlayIcon);
        };
    }

    // ---------------------------------------------------------------
    // Kontextmenü (Rechtsklick auf einer Zeile ODER Klick auf das
    // Menü-Icon) - identische 5 Aktionen an beiden Stellen, entspricht
    // MRTableView.contextMenuEvent() / ActionDelegate-Menü-Icon.
    // ---------------------------------------------------------------
    var contextMenu = document.getElementById('songContextMenu');
    var activeSongId = null;
    var activeSongTitle = null;

    function openContextMenu(x, y, row) {
        activeSongId = row.dataset.songId;
        activeSongTitle = row.dataset.title;
        contextMenu.style.left = x + 'px';
        contextMenu.style.top = y + 'px';
        contextMenu.hidden = false;
    }

    function closeContextMenu() {
        contextMenu.hidden = true;
    }

    table.addEventListener('contextmenu', function (e) {
        var row = e.target.closest('tr[data-song-id]');
        if (!row) return;
        e.preventDefault();
        openContextMenu(e.clientX, e.clientY, row);
    });

    table.addEventListener('click', function (e) {
        var menuIcon = e.target.closest('[data-action="menu"]');
        if (!menuIcon) return;
        var row = menuIcon.closest('tr');
        var rect = menuIcon.getBoundingClientRect();
        openContextMenu(rect.left, rect.bottom, row);
    });

    document.addEventListener('click', function (e) {
        if (!contextMenu.hidden && !e.target.closest('#songContextMenu') && !e.target.closest('[data-action="menu"]')) {
            closeContextMenu();
        }
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeContextMenu();
    });

    // ---------------------------------------------------------------
    // Song bearbeiten (EditSongDialog-Pendant).
    // ---------------------------------------------------------------
    var editModal = document.getElementById('editSongModal');
    var editForm = document.getElementById('editSongForm');
    var editLyricsInfo = document.getElementById('editLyricsInfo');
    var editLyricsDisplay = document.getElementById('editLyricsDisplay');
    var editLyricsBrowseBtn = document.getElementById('editLyricsBrowseBtn');
    var editLyricsFileInput = document.getElementById('editLyricsFileInput');

    function openEditModal(songId) {
        fetch('/songs/' + songId + '/data').then(function (res) { return res.json(); }).then(function (data) {
            editForm.action = '/songs/' + songId + '/edit';
            editForm.querySelector('#editTitleInput').value = data.title;
            editForm.querySelector('#editArtistInput').value = data.artist;
            editForm.querySelector('#editGenreInput').value = data.genre;
            editForm.querySelector('#editSourceInput').value = data.source_id || '';
            editForm.querySelector('#editCollectionInput').value = data.collection;
            editForm.querySelector('#editBpmInput').value = data.bpm;
            editForm.querySelector('#editKeyInput').value = data.key;
            editForm.querySelector('#editTimeSigInput').value = data.time_sig;
            editForm.querySelector('#editIsEditedInput').checked = !!data.is_edited;
            editForm.querySelector('#editCommentInput').value = data.comment;

            editLyricsDisplay.value = '';
            editLyricsFileInput.value = '';
            editLyricsInfo.textContent = data.lyrics_filename
                ? '📄 Lyrics: ' + data.lyrics_filename
                : '📄 Keine Lyrics-Datei vorhanden';

            editModal.classList.add('open');
        });
    }

    editLyricsBrowseBtn.addEventListener('click', function () { editLyricsFileInput.click(); });
    editLyricsFileInput.addEventListener('change', function () {
        var file = editLyricsFileInput.files[0];
        editLyricsDisplay.value = file ? file.name : '';
    });

    [editModal].forEach(function (modal) {
        modal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
            btn.addEventListener('click', function () { modal.classList.remove('open'); });
        });
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.remove('open');
        });
    });

    // ---------------------------------------------------------------
    // Lyrics anzeigen (ShowLyricsDialog-Pendant).
    // ---------------------------------------------------------------
    var lyricsModal = document.getElementById('lyricsModal');
    var lyricsSongTitle = document.getElementById('lyricsSongTitle');
    var lyricsContent = document.getElementById('lyricsContent');
    var lyricsOpenExternalBtn = document.getElementById('lyricsOpenExternalBtn');
    var lyricsPrintBtn = document.getElementById('lyricsPrintBtn');

    function openLyricsModal(songId) {
        fetch('/songs/' + songId + '/lyrics').then(function (res) { return res.json(); }).then(function (data) {
            lyricsSongTitle.textContent = data.title;
            lyricsContent.value = data.content;

            lyricsOpenExternalBtn.onclick = function () {
                window.open('/songs/' + songId + '/lyrics-file', '_blank');
            };
            lyricsPrintBtn.onclick = function () {
                var win = window.open('', '_blank');
                win.document.write(
                    '<pre style="white-space:pre-wrap;font-family:inherit;">' +
                    data.content.replace(/&/g, '&amp;').replace(/</g, '&lt;') +
                    '</pre>'
                );
                win.document.close();
                win.print();
            };

            lyricsModal.classList.add('open');
        });
    }

    [lyricsModal].forEach(function (modal) {
        modal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
            btn.addEventListener('click', function () { modal.classList.remove('open'); });
        });
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.remove('open');
        });
    });

    // ---------------------------------------------------------------
    // Kontextmenü-Aktionen.
    // ---------------------------------------------------------------
    var deleteForm = document.getElementById('songDeleteForm');

    contextMenu.querySelectorAll('[data-action]').forEach(function (item) {
        item.addEventListener('click', function () {
            var action = item.dataset.action;
            closeContextMenu();

            if (action === 'edit') {
                openEditModal(activeSongId);
            } else if (action === 'lyrics') {
                openLyricsModal(activeSongId);
            } else if (action === 'mixer') {
                if (window.MRMixer) window.MRMixer.open(activeSongId);
            } else if (action === 'download') {
                window.location = '/songs/' + activeSongId + '/download';
            } else if (action === 'delete') {
                if (confirm("Soll der Song '" + activeSongTitle + "' wirklich gelöscht werden?\nDie Datei wird dauerhaft entfernt.")) {
                    deleteForm.action = '/songs/' + activeSongId + '/delete';
                    deleteForm.submit();
                }
            }
        });
    });

    // ---------------------------------------------------------------
    // Spalten-Sortierung per Klick auf den Spaltenkopf - entspricht
    // SortFilterProxyModel.lessThan(): BPM numerisch, Dauer als Sekunden,
    // Checkbox/Favorit/Bearbeitet als Bool, alles andere als Text
    // (case-insensitive). Reiner Client-Sort, da ohnehin alle Zeilen auf
    // einmal geladen sind (keine Pagination, wie im Original).
    (function () {
        var allHeaders = table.querySelectorAll('thead th');
        var currentSort = { index: -1, dir: 1 };

        function cellValue(row, index, type) {
            var cell = row.children[index];
            if (!cell) return '';

            if (type === 'bool') {
                var checkbox = cell.querySelector('.mr-check-box');
                if (checkbox) return checkbox.classList.contains('checked') ? 1 : 0;
                var fav = cell.querySelector('.mr-fav-toggle');
                if (fav) return fav.src.indexOf('fav_on') !== -1 ? 1 : 0;
                return cell.textContent.trim() === 'Ja' ? 1 : 0;
            }
            if (type === 'number') {
                var n = parseFloat(cell.textContent.trim());
                return isNaN(n) ? -Infinity : n;
            }
            if (type === 'duration') {
                var parts = cell.textContent.trim().split(':');
                if (parts.length === 2) {
                    return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
                }
                return -1;
            }
            return cell.textContent.trim().toLowerCase();
        }

        allHeaders.forEach(function (th, index) {
            var type = th.dataset.sort;
            if (!type) return;

            th.addEventListener('click', function () {
                var dir = (currentSort.index === index) ? -currentSort.dir : 1;
                currentSort = { index: index, dir: dir };

                allHeaders.forEach(function (h) { h.classList.remove('sorted-asc', 'sorted-desc'); });
                th.classList.add(dir === 1 ? 'sorted-asc' : 'sorted-desc');

                var tbody = table.querySelector('tbody');
                var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));

                rows.sort(function (a, b) {
                    var va = cellValue(a, index, type);
                    var vb = cellValue(b, index, type);
                    if (va < vb) return -1 * dir;
                    if (va > vb) return 1 * dir;
                    return 0;
                });

                rows.forEach(function (row) { tbody.appendChild(row); });
            });
        });
    })();
})();

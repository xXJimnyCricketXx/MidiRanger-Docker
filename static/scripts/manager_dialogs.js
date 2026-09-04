// Generisches JS für alle BaseManagerView-Ableger (Quellen, Playlists, ...):
// Zeilen-Selektion per Klick (Pendant zu QListWidget-Selektion), Umbenennen
// (gemeinsames Modal, Pendant zu QInputDialog.getText) und Löschen inkl.
// Umbuchen-Dialog bei Einträgen mit Inhalt (Pendant zur verschachtelten
// QDialog in BaseManagerView._delete_action()).
(function () {
    function setHidden(form, name, value) {
        var el = form.querySelector('[name="' + name + '"]');
        if (el) el.value = value;
    }

    // ---------------------------------------------------------------
    // Gemeinsames Umbenennen-Modal.
    // ---------------------------------------------------------------
    var renameModal = document.getElementById('managerRenameModal');
    var renameInput = document.getElementById('managerRenameInput');
    var renameConfirmBtn = document.getElementById('managerRenameConfirmBtn');
    var renameOnConfirm = null;

    function openRenameModal(sel, onConfirm) {
        renameOnConfirm = onConfirm;
        renameInput.value = sel.name;
        renameModal.classList.add('open');
        renameInput.focus();
        renameInput.select();
    }

    if (renameModal) {
        renameConfirmBtn.addEventListener('click', function () {
            var newName = renameInput.value.trim();
            if (!newName) { alert('Ungültiger oder leerer Name.'); return; }
            renameModal.classList.remove('open');
            if (renameOnConfirm) renameOnConfirm(newName);
        });
        renameInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); renameConfirmBtn.click(); }
        });
        renameModal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
            btn.addEventListener('click', function () { renameModal.classList.remove('open'); });
        });
        renameModal.addEventListener('click', function (e) {
            if (e.target === renameModal) renameModal.classList.remove('open');
        });
    }

    // ---------------------------------------------------------------
    // Gemeinsames Umbuchen-Modal ("Ziel auswählen: ... Umbuchen & Löschen").
    // ---------------------------------------------------------------
    var reassignModal = document.getElementById('managerReassignModal');
    var reassignSelect = document.getElementById('reassignSelect');
    var reassignTitle = document.getElementById('reassignTitle');
    var reassignConfirmBtn = document.getElementById('reassignConfirmBtn');
    var reassignOnConfirm = null;

    function openReassignModal(sel, others, onConfirm) {
        reassignOnConfirm = onConfirm;
        reassignSelect.innerHTML = '';
        others.forEach(function (o) {
            var opt = document.createElement('option');
            opt.value = o.id;
            opt.textContent = o.name;
            reassignSelect.appendChild(opt);
        });
        reassignTitle.textContent = sel.name + ' löschen – Songs umbuchen';
        reassignModal.classList.add('open');
    }

    if (reassignModal) {
        reassignConfirmBtn.addEventListener('click', function () {
            reassignModal.classList.remove('open');
            if (reassignOnConfirm) reassignOnConfirm(reassignSelect.value);
        });
        reassignModal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
            btn.addEventListener('click', function () { reassignModal.classList.remove('open'); });
        });
        reassignModal.addEventListener('click', function (e) {
            if (e.target === reassignModal) reassignModal.classList.remove('open');
        });
    }

    // ---------------------------------------------------------------
    // Eine Manager-Instanz (Liste + Hinzufügen/Umbenennen/Löschen).
    // ---------------------------------------------------------------
    function initManager(opts) {
        var list = document.getElementById(opts.listId);
        var renameBtn = document.getElementById(opts.renameBtnId);
        var deleteBtn = document.getElementById(opts.deleteBtnId);
        var renameForm = document.getElementById(opts.renameFormId);
        var deleteForm = document.getElementById(opts.deleteFormId);
        if (!list || !renameBtn || !deleteBtn) return;

        // Entspricht QListWidget-Selektion: Klick auf eine Zeile markiert sie.
        list.querySelectorAll('.mr-manager-row').forEach(function (row) {
            row.addEventListener('click', function () {
                list.querySelectorAll('.mr-manager-row.selected').forEach(function (r) {
                    r.classList.remove('selected');
                });
                row.classList.add('selected');
            });
        });

        function getSelected() {
            var row = list.querySelector('.mr-manager-row.selected');
            if (!row) return null;
            return { id: row.dataset.id, name: row.dataset.name, count: parseInt(row.dataset.count, 10) || 0 };
        }

        function getOthers(excludeId) {
            var others = [];
            list.querySelectorAll('.mr-manager-row').forEach(function (r) {
                if (r.dataset.id !== excludeId) others.push({ id: r.dataset.id, name: r.dataset.name });
            });
            return others;
        }

        renameBtn.addEventListener('click', function () {
            var sel = getSelected();
            if (!sel) { alert('Kein Eintrag ausgewählt.'); return; }

            openRenameModal(sel, function (newName) {
                setHidden(renameForm, opts.idField, sel.id);
                setHidden(renameForm, 'new_name', newName);
                renameForm.submit();
            });
        });

        deleteBtn.addEventListener('click', function () {
            var sel = getSelected();
            if (!sel) { alert('Kein Eintrag ausgewählt.'); return; }

            if (opts.protectedName && sel.name.toLowerCase() === opts.protectedName) {
                alert(opts.protectedMessage);
                return;
            }

            if (sel.count === 0) {
                setHidden(deleteForm, opts.idField, sel.id);
                setHidden(deleteForm, 'reassign_to', '');
                deleteForm.submit();
                return;
            }

            var others = getOthers(sel.id);
            if (others.length === 0) {
                alert('Es existiert keine Ziel-Option zum Umbuchen.');
                return;
            }

            openReassignModal(sel, others, function (targetId) {
                setHidden(deleteForm, opts.idField, sel.id);
                setHidden(deleteForm, 'reassign_to', targetId);
                deleteForm.submit();
            });
        });
    }

    initManager({
        listId: 'sourcesList',
        renameBtnId: 'sourceRenameBtn',
        deleteBtnId: 'sourceDeleteBtn',
        renameFormId: 'sourceRenameForm',
        deleteFormId: 'sourceDeleteForm',
        idField: 'source_id',
        protectedName: 'unbekannt',
        protectedMessage: 'Die Quelle „Unbekannt“ kann nicht gelöscht werden.'
    });

    initManager({
        listId: 'playlistsList',
        renameBtnId: 'playlistRenameBtn',
        deleteBtnId: 'playlistDeleteBtn',
        renameFormId: 'playlistRenameForm',
        deleteFormId: 'playlistDeleteForm',
        idField: 'playlist_id'
    });
})();

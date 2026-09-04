(function () {
    var themeSelect = document.getElementById('settingsThemeSelect');
    var modal = document.getElementById('settingsModal');
    if (!themeSelect || !modal || !window.THEMES_RESOLVED) return;

    var root = document.documentElement;
    var savedThemeKey = themeSelect.value;

    var VAR_MAP = {
        bg: '--theme-bg', surface: '--theme-surface', input_bg: '--theme-input-bg',
        content_text: '--theme-content-text', accent: '--theme-accent', text: '--theme-text',
        home_title_text: '--theme-home-title-text', header_text: '--theme-header-text',
        button_color: '--theme-button-color', button_text: '--theme-button-text',
        button_hover_color: '--theme-button-hover-color', button_hover_text: '--theme-button-hover-text',
        link_color: '--theme-link-color', link_hover_color: '--theme-link-hover-color',
        splash_text: '--theme-splash-text', border: '--theme-border', alternate_bg: '--theme-alternate-bg'
    };

    // Entspricht theme_combo.currentTextChanged -> controller.apply_internal_theme():
    // sofortige visuelle Vorschau, ohne zu speichern.
    function applyThemeVars(key) {
        var theme = window.THEMES_RESOLVED[key];
        if (!theme) return;
        Object.keys(VAR_MAP).forEach(function (field) {
            root.style.setProperty(VAR_MAP[field], theme[field]);
        });
    }

    // Entspricht _cancel_dialog(): Theme wieder auf den gespeicherten Stand zurücksetzen.
    function revertPreview() {
        applyThemeVars(savedThemeKey);
    }

    themeSelect.addEventListener('change', function () {
        applyThemeVars(themeSelect.value);
    });

    modal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
        btn.addEventListener('click', revertPreview);
    });

    modal.addEventListener('click', function (e) {
        if (e.target === modal) revertPreview();
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal.classList.contains('open')) revertPreview();
    });
})();

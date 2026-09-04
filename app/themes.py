# Port von dev-modus/alt/src/theme/theme_manager.py + themes/*.json.
# Bewusst dieselben snake_case-Feldnamen wie im Original.

THEMES = {
    'bubblegum_pop': {
        'bg': '#ffeef3', 'accent': '#ff80a6', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#ff80a6', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#ff80a6',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'bubblegum_pop_logo.png',
    },
    'coffee_break': {
        'bg': '#f3e8d8', 'accent': '#8b5e34', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#8b5e34', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#8b5e34',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'coffee_break_logo.png',
    },
    'crystal_white': {
        'bg': '#ffffff', 'accent': '#2d89ef', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#2d89ef', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#2d89ef',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'crystal_white_logo.png',
    },
    'deep_space': {
        'bg': '#1b1b1b', 'accent': '#3dc6d0', 'text': '#202020', 'home_title_text': '#ffffff',
        'header_text': '#ffffff', 'button_color': '#3dc6d0', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#3dc6d0',
        'link_hover_color': None, 'splash_text': '#ffffff', 'logo': 'deep_space_logo.png',
    },
    'dx7_purple': {
        'bg': '#1a1023', 'accent': '#9d4edd', 'text': '#202020', 'home_title_text': '#ffffff',
        'header_text': '#ffffff', 'button_color': '#9d4edd', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#9d4edd',
        'link_hover_color': None, 'splash_text': '#ffffff', 'logo': 'dx7_purple_logo.png',
    },
    'espresso': {
        'bg': '#362c2a', 'accent': '#a97450', 'text': '#202020', 'home_title_text': '#ffffff',
        'header_text': '#ffffff', 'button_color': '#a97450', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#a97450',
        'link_hover_color': None, 'splash_text': '#ffffff', 'logo': 'espresso_logo.png',
    },
    'korg_titanium': {
        'bg': '#d1d1d1', 'accent': '#005eff', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#005eff', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#005eff',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'korg_titanium_logo.png',
    },
    'lavender_dream': {
        'bg': '#f0e6ff', 'accent': '#9080ff', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#9080ff', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#9080ff',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'lavender_dream_logo.png',
    },
    'lime_groove': {
        'bg': '#1e1e1e', 'accent': '#a6ff00', 'text': '#202020', 'home_title_text': '#ffffff',
        'header_text': '#000000', 'button_color': '#a6ff00', 'button_text': '#000000',
        'button_hover_color': None, 'button_hover_text': '#000000', 'link_color': '#a6ff00',
        'link_hover_color': None, 'splash_text': '#ffffff', 'logo': 'lime_groove_logo.png',
    },
    'orange_punch': {
        'bg': '#202020', 'accent': '#ff7700', 'text': '#202020', 'home_title_text': '#ffffff',
        'header_text': '#ffffff', 'button_color': '#ff7700', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#ff7700',
        'link_hover_color': None, 'splash_text': '#ffffff', 'logo': 'orange_punch_logo.png',
    },
    'retro_midi': {
        'bg': '#c7c7c7', 'accent': '#6b5cff', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#6b5cff', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#6b5cff',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'retro_midi_logo.png',
    },
    'roland_blue': {
        'bg': '#101820', 'accent': '#0096ff', 'text': '#202020', 'home_title_text': '#ffffff',
        'header_text': '#ffffff', 'button_color': '#0096ff', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#0096ff',
        'link_hover_color': None, 'splash_text': '#ffffff', 'logo': 'roland_blue_logo.png',
    },
    'silverlight': {
        'bg': '#d0d4d8', 'accent': '#7a8a9a', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#7a8a9a', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#7a8a9a',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'silverlight_logo.png',
    },
    'sunset_orange': {
        'bg': '#fff4e6', 'accent': '#ff8c42', 'text': '#202020', 'home_title_text': '#000000',
        'header_text': '#ffffff', 'button_color': '#ff8c42', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#ff8c42',
        'link_hover_color': None, 'splash_text': '#000000', 'logo': 'sunset_orange_logo.png',
    },
    'wersi_gold': {
        'bg': '#1b1b1b', 'accent': '#d4af37', 'text': '#202020', 'home_title_text': '#ffffff',
        'header_text': '#ffffff', 'button_color': '#d4af37', 'button_text': '#ffffff',
        'button_hover_color': None, 'button_hover_text': '#ffffff', 'link_color': '#d4af37',
        'link_hover_color': None, 'splash_text': '#ffffff', 'logo': 'wersi_gold_logo.png',
    },
}

DEFAULT_THEME = 'bubblegum_pop'


def display_name(internal_name: str) -> str:
    """Port von settings_controller.py: display_name()."""
    return internal_name.replace('_', ' ').title()


def list_themes():
    return [{'key': key, 'name': display_name(key)} for key in THEMES]


def _hex_to_rgb(value: str):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _lighten(hex_color: str, amount: float = 0.1) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    r, g, b = min(r + amount, 1), min(g + amount, 1), min(b + amount, 1)
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'


def _darken(hex_color: str, amount: float = 0.1) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    r, g, b = max(r - amount, 0), max(g - amount, 0), max(b - amount, 0)
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'


def resolve_theme(theme_key: str) -> dict:
    """Baut aus einem rohen Theme das vollständige, aufgelöste Farbschema -
    Hover-Farben, Border, wie in theme_manager.py.load_theme()."""
    raw = THEMES.get(theme_key, THEMES[DEFAULT_THEME])

    button_color = raw['button_color'] or raw['accent']
    button_text = raw['button_text'] or raw['header_text']

    button_hover_color = raw['button_hover_color'] or (
        _lighten(button_color, 0.12) if _luminance(button_color) < 0.5 else _darken(button_color, 0.12)
    )

    link_color = raw['link_color'] or raw['accent']
    link_hover_color = raw['link_hover_color'] or (
        _lighten(link_color, 0.12) if _luminance(button_color) < 0.5 else _darken(link_color, 0.12)
    )

    border = _darken(raw['accent'], 0.25)
    is_dark_bg = _luminance(raw['bg']) < 0.5

    # Original: theme_manager.py berechnet "alternate_bg" für Widgets wie
    # MRButtonToggle (unchecked-Zustand, siehe Log-Viewer-Filterbuttons).
    alternate_bg = _lighten(raw['bg'], 0.10) if is_dark_bg else _darken(raw['bg'], 0.10)

    # Keine Entsprechung im Original: dort gab es keine "Karten"-Flächen, nur
    # Fenster-BG, Akzentfarbe und native Qt-Widgets. Für Web-Karten/-Inputs
    # braucht es trotzdem eine vom bunten bg abgesetzte Fläche.
    surface = 'rgba(255,255,255,0.06)' if is_dark_bg else 'rgba(255,255,255,0.55)'
    input_bg = 'rgba(255,255,255,0.12)' if is_dark_bg else 'rgba(255,255,255,0.8)'
    content_text = '#ffffff' if is_dark_bg else raw['text']

    return {
        'bg': raw['bg'],
        'accent': raw['accent'],
        'text': raw['text'],
        'home_title_text': raw['home_title_text'],
        'header_text': raw['header_text'],
        'button_color': button_color,
        'button_text': button_text,
        'button_hover_color': button_hover_color,
        'button_hover_text': raw['button_hover_text'] or button_text,
        'link_color': link_color,
        'link_hover_color': link_hover_color,
        'splash_text': raw['splash_text'],
        'border': border,
        'alternate_bg': alternate_bg,
        'surface': surface,
        'input_bg': input_bg,
        'content_text': content_text,
        'is_dark_bg': is_dark_bg,
        'logo': raw['logo'],
    }


def resolve_all_themes() -> dict:
    """Für die Live-Vorschau im Settings-Modal (JS wechselt CSS-Variablen,
    ohne dass gespeichert wird - genau wie theme_combo.currentTextChanged
    im Original vor dem Klick auf "Speichern")."""
    return {key: resolve_theme(key) for key in THEMES}

from dataclasses import dataclass


@dataclass
class UITheme:
    # Farger
    bg_main: str = "#2b2b2b"
    bg_row_top: str = "#3a3a3a"
    bg_row_normal: str = "#333333"
    bg_stat_box: str = "#1f1f1f"

    text_primary: str = "white"
    text_muted: str = "#cccccc"
    accent: str = "#4682B4"

    # Fontfamilier
    font_main: str = "Arial"
    font_mono: str = "Consolas"
    font_bracket: str = "Helvetica"

    # Standings scaling
    row_font_scale: float = 0.42
    stat_font_scale: float = 0.32
    row_corner_scale: float = 0.22
    stat_corner_scale: float = 0.14
    logo_scale: float = 0.62

    row_inner_padx_scale: float = 0.12
    row_inner_pady_scale: float = 0.05
    stat_box_padx_scale: float = 0.05
    stat_box_pady_scale: float = 0.12

    # Match scaling
    match_time_scale: float = 0.28
    match_team_scale: float = 0.36
    match_vs_scale: float = 0.34
    match_row_corner_scale: float = 0.22
    match_row_inner_pady_scale: float = 0.10

    # Bounds
    min_row_font: int = 8
    max_row_font: int = 14

    min_stat_font: int = 7
    max_stat_font: int = 11

    min_match_time_font: int = 7
    max_match_time_font: int = 11

    min_match_team_font: int = 7
    max_match_team_font: int = 13

    min_match_vs_font: int = 7
    max_match_vs_font: int = 13

    min_corner: int = 4
    min_logo_size: int = 10

    min_row_inner_padx: int = 2
    min_row_inner_pady: int = 0
    min_stat_box_padx: int = 1
    min_stat_box_pady: int = 2

    min_match_row_inner_pady: int = 0

    # ===== TIMER COLORS =====
    timer_bg: str = "#2b2b2b"
    timer_arc: str = "#4682B4"
    timer_text: str = "white"
    timer_warning: str = "#d9534f"
    timer_finished: str = "#2faa6a"

    # ===== BUTTON COLORS =====
    button_primary: str = "#4682B4"
    button_secondary: str = "#444444"
    button_text: str = "white"

    # ===== LOADING =====
    loading_circle_width: int = 10
    loading_size: int = 220

    # ===== BRACKET =====
    bracket_box_bg: str = "gray20"
    bracket_line_color: str = "white"

    # Timer
    timer_bg: str = "#2b2b2b" 
    timer_arc_idle: str = "#2b2b2b"
    timer_arc_ok: str = "#6CA0DC"
    timer_arc_warning: str = "#E6C229"
    timer_arc_danger: str = "#D1495B"
    timer_text: str = "white"

    # Form / status
    success: str = "#2faa6a"
    danger: str = "#d9534f"
    warning: str = "#c9a227"
    neutral: str = "#aaaaaa"
    form_unknown: str = "#666666"

    # Timer fonts
    font_timer: str = "Helvetica"


def get_dark_theme():
    return UITheme()


def get_light_theme():
    return UITheme(
        bg_main="#f5f5f5",
        bg_row_top="#e0e0e0",
        bg_row_normal="#ffffff",
        bg_stat_box="#dddddd",
        text_primary="black",
        text_muted="#555555",
        accent="#2f80ed",
    )
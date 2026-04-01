from dataclasses import dataclass


@dataclass
class UITheme:
    # ============================================================
    # BASE COLORS
    # ============================================================
    bg_main: str = "#2b2b2b"
    bg_panel: str = "#333333"
    bg_panel_alt: str = "#3a3a3a"
    bg_stat_box: str = "#1f1f1f"

    text_primary: str = "white"
    text_muted: str = "#cccccc"
    text_neutral: str = "#aaaaaa"

    border_subtle: str = "#444444"
    accent: str = "#4682B4"

    # ============================================================
    # STATUS / FEEDBACK COLORS
    # ============================================================
    success: str = "#2faa6a"
    warning: str = "#c9a227"
    danger: str = "#d9534f"
    error_text: str = "tomato"
    form_unknown: str = "#666666"

    # ============================================================
    # FONT FAMILIES
    # ============================================================
    font_main: str = "Arial"
    font_mono: str = "Consolas"
    font_bracket: str = "Helvetica"
    font_timer: str = "Helvetica"

    # ============================================================
    # LOADING
    # ============================================================
    loading_size: int = 220
    loading_circle_width: int = 10
    loading_font_size: int = 18
    loading_step_delay_ms: int = 350
    loading_initial_delay_ms: int = 100

    # ============================================================
    # STANDINGS SCALING
    # ============================================================
    row_font_scale: float = 0.42
    stat_font_scale: float = 0.32
    row_corner_scale: float = 0.22
    stat_corner_scale: float = 0.14
    logo_scale: float = 0.62

    row_inner_padx_scale: float = 0.12
    row_inner_pady_scale: float = 0.05
    stat_box_padx_scale: float = 0.05
    stat_box_pady_scale: float = 0.12

    min_row_font: int = 8
    max_row_font: int = 14

    min_stat_font: int = 7
    max_stat_font: int = 11

    min_corner: int = 4
    min_logo_size: int = 10

    min_row_inner_padx: int = 2
    min_row_inner_pady: int = 0
    min_stat_box_padx: int = 1
    min_stat_box_pady: int = 2

    # ============================================================
    # MATCH SCALING
    # ============================================================
    match_time_scale: float = 0.28
    match_team_scale: float = 0.36
    match_vs_scale: float = 0.34
    match_row_corner_scale: float = 0.22
    match_row_inner_pady_scale: float = 0.10

    min_match_time_font: int = 7
    max_match_time_font: int = 11

    min_match_team_font: int = 7
    max_match_team_font: int = 13

    min_match_vs_font: int = 7
    max_match_vs_font: int = 13

    min_match_row_inner_pady: int = 0

    # ============================================================
    # TIMER
    # ============================================================
    timer_bg: str = "#2b2b2b"
    timer_arc_idle: str = "#2b2b2b"
    timer_arc_ok: str = "#6CA0DC"
    timer_arc_warning: str = "#E6C229"
    timer_arc_danger: str = "#D1495B"
    timer_text: str = "white"

    # ============================================================
    # BRACKET
    # ============================================================
    bracket_box_bg: str = "gray20"
    bracket_box_outline: str = "black"
    bracket_line_color: str = "white"
    winner_text: str = "white"

    # ============================================================
    # COMMON FIXED FONT SIZES
    # ============================================================
    section_title_size: int = 20
    dialog_title_size: int = 20


def get_dark_theme():
    return UITheme()


def get_light_theme():
    return UITheme(
        bg_main="#f5f5f5",
        bg_panel="#ffffff",
        bg_panel_alt="#eaeaea",
        bg_stat_box="#dddddd",
        text_primary="black",
        text_muted="#555555",
        text_neutral="#777777",
        border_subtle="#c8c8c8",
        accent="#2f80ed",
        timer_bg="#f5f5f5",
        timer_arc_idle="#f5f5f5",
        timer_text="black",
        bracket_line_color="black",
        winner_text="black",
    )
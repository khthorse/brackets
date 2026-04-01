from dataclasses import dataclass


@dataclass
class UITheme:
    # ============================================================
    # BASE COLORS
    # ============================================================
    bg_main: str = "#2b2b2b"
    bg_row_normal: str = "#333333"
    bg_row_top: str = "#3a3a3a"
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
    font_main: str = "Helvetica"
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
    max_row_font: int = 30

    min_stat_font: int = 7
    max_stat_font: int = 20

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
    timer_text_dim: str = "#777777"
    button_fg: str = "#3f3f3f"
    button_hover: str = "#4a4a4a"
    button_text: str = "white"

    # ============================================================
    # TIMER SIZING
    # ============================================================
    timer_outer_pad_scale: float = 20 / 1080
    timer_title_scale: float = 50 / 1080
    timer_title_pad_y_scale: float = 10 / 1080
    timer_title_pad_x_scale: float = 5 / 1080
    timer_canvas_scale: float = 250 / 1080
    timer_canvas_pad_y_scale: float = 5 / 1080
    timer_arc_pad_scale: float = 10 / 1080
    timer_arc_width_scale: float = 15 / 1080
    timer_button_font_scale: float = 13 / 1080
    timer_button_width_scale: float = 140 / 1080
    timer_button_height_scale: float = 36 / 1080
    timer_button_pad_x_scale: float = 10 / 1080
    timer_button_pad_y_scale: float = 5 / 1080
    timer_time_font_scale: float = 40 / 1080

    # Minimums
    timer_min_outer_pad: int = 6
    timer_min_title_font: int = 18
    timer_min_canvas_size: int = 120
    timer_min_arc_pad: int = 4
    timer_min_arc_width: int = 6
    timer_min_button_font: int = 11
    timer_min_button_width: int = 70
    timer_min_button_height: int = 28
    timer_min_button_pad_x: int = 3
    timer_min_button_pad_y: int = 3
    timer_min_time_font: int = 18

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
    return UITheme()

from dataclasses import dataclass


@dataclass
class AppSettings:
    language: str = "no"
    custom_title: str = ""
    
    default_timer_seconds: int = 15 * 60
    alarm_enabled: bool = True
    default_muted: bool = False
    blink_enabled: bool = True
    pulse_enabled: bool = True

    ask_for_logos: bool = False
    show_team_logos: bool = True
    show_match_times: bool = True
    shuffle_teams: bool = True

    default_use_group_stage: bool = False
    default_playoff_team_count: int = 4

    table_count: int = 2
    timer_mode: str = "per_table"   # "single", "per_table", "custom"
    timer_count: int = 2

    fullscreen_enabled: bool = False
    fullscreen_monitor_index: int = 0

    def get_timer_count(self) -> int:
        if self.timer_mode == "single":
            return 1
        if self.timer_mode == "per_table":
            return max(1, self.table_count)
        if self.timer_mode == "custom":
            return max(1, self.timer_count)
        return 1    
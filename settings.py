from dataclasses import dataclass


@dataclass
class AppSettings:
    language: str = "no"
    default_timer_seconds: int = 15 * 60
    alarm_enabled: bool = True
    default_muted: bool = False
    ask_for_logos: bool = False
    blink_enabled: bool = True
    pulse_enabled: bool = True
    show_team_logos: bool = True
    show_match_times: bool = True
    shuffle_teams: bool = True
    default_use_group_stage: bool = False
    default_playoff_team_count: int = 4
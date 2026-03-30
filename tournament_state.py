from dataclasses import dataclass, field
from typing import Literal, Optional

from settings import AppSettings
from models import Team, GroupStageModel, TournamentModel


TournamentPhase = Literal["setup", "group_stage", "bracket", "finished"]


@dataclass
class TournamentState:
    settings: AppSettings
    title: str = ""
    source_teams: list[Team] = field(default_factory=list)

    phase: TournamentPhase = "setup"

    group_stage_model: Optional[GroupStageModel] = None
    bracket_model: Optional[TournamentModel] = None

    dirty: bool = False

    def has_teams(self) -> bool:
        return len(self.source_teams) > 0

    def has_group_stage(self) -> bool:
        return self.group_stage_model is not None

    def has_bracket(self) -> bool:
        return self.bracket_model is not None

    def mark_dirty(self):
        self.dirty = True

    def mark_clean(self):
        self.dirty = False

    def reset_to_setup(self, keep_teams: bool = True):
        if not keep_teams:
            self.source_teams = []

        self.group_stage_model = None
        self.bracket_model = None
        self.phase = "setup"
        self.mark_dirty()

    def reset_group_stage(self):
        self.group_stage_model = None
        if self.phase == "group_stage":
            self.phase = "setup"
        self.mark_dirty()

    def reset_bracket(self):
        self.bracket_model = None
        if self.phase == "bracket":
            if self.group_stage_model is not None:
                self.phase = "group_stage"
            else:
                self.phase = "setup"
        self.mark_dirty()
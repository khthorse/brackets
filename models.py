import random

from dataclasses import dataclass
from typing import Optional


@dataclass
class Team:
    name: str
    logo: Optional[str] = None
    wins: int = 0
    cups_hit: int = 0
    cups_missed: int = 0
    total_cups_diff: int = 0


@dataclass
class Match:
    team1: Optional[Team] = None
    team2: Optional[Team] = None
    winner: Optional[Team] = None
    start_time: Optional[str] = None
    played: bool = False
    team1_cups_left: Optional[int] = None
    team2_cups_left: Optional[int] = None
    time: Optional[str] = None


class TournamentModel:
    def __init__(self):
        self.loaded_teams = []  # [{"name": ..., "logo": ...}, ...]
        self.teams: list[Team] = []
        self.rounds: list[list[Match]] = []  # Hver runde er en liste med kamper

    def build_bracket(self, teams_input):

        team_objs = []

        for item in teams_input:
            if isinstance(item, Team):
                if item.name.strip():
                    team_objs.append(item)
            elif isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                logo = item.get("logo")
                if name:
                    team_objs.append(Team(name=name, logo=logo))
            else:
                name = str(item).strip()
                if name:
                    team_objs.append(Team(name=name))

        teams_shuffled = team_objs[:]
        random.shuffle(teams_shuffled)
        self.teams = teams_shuffled

        n = len(self.teams)
        size = 1
        while size < n:
            size *= 2

        seeds = self.teams + [None] * (size - n)

        first_round = []
        for i in range(0, size, 2):
            first_round.append(Match(team1=seeds[i], team2=seeds[i + 1])
        self.rounds = [first_round]

        rsize = size // 2
        while rsize >= 1:
            matches = []
            for _ in range(rsize // 2):
                matches.append(Match())
            if rsize // 2 > 0:
                self.rounds.append(matches)
            rsize //= 2


    def set_winner(self, round_index, match_index, winner: Team):
        self.rounds[round_index][match_index].winner = winner
        if round_index + 1 < len(self.rounds):
            next_match_index = match_index // 2
            next_match = self.rounds[round_index + 1][next_match_index]
            
            if match_index % 2 == 0:
                next_match.team1 = winner
            else:
                next_match.team2 = winner

    def set_start_time(self, round_index, match_index, start_time):
        self.rounds[round_index][match_index].start_time = start_time

    def set_match_teams(self, round_index, match_index, team1, team2):
        if isinstance(team1, str):
            team1 = Team(name=team1) if team1 and team1 != "TBD" else None
        if isinstance(team2, str):
            team2 = Team(name=team2) if team2 and team2 != "TBD" else None

    def get_rounds(self):
        return self.rounds
    

class GroupStageModel:
    def __init__(self, teams):
        self.teams: list[Team] = []

        for team in teams:
            if isinstance(team, Team):
                self.teams.append(
                    Team(
                        name=team.name,
                        logo=team.logo,
                        wins=0,
                        cups_hit=0,
                        cups_missed=0,
                        total_cups_diff=0,
                    )
                )
            elif isinstance(team, dict):
                self.teams.append(
                    Team(
                        name=team["name"],
                        logo=team.get("logo"),
                    )
                )

        self.matches: list[Match] = []

    def generate_matches(self):
        teams_shuffled = self.teams[:]
        random.shuffle(teams_shuffled)
        
        n = len(teams_shuffled)
        assert n % 2 == 0, "Antall lag bør være partall for dette oppsettet."
        
        # Sørg for at ingen møter samme motstander to ganger
        round1 = []
        for i in range(0, n, 2):
            round1.append(Match(team1=teams_shuffled[i], team2=teams_shuffled[i+1]))

        # Lag en ny tilfeldig rekkefølge og sørg for unike kamper
        round2 = []
        valid_round = False

        while not valid_round:
            random.shuffle(teams_shuffled)
            round2 = [
                Match(team1=teams_shuffled[i], team2=teams_shuffled[i+1])
                for i in range(0, n, 2)
            ]

            # sjekk at ingen par går igjen fra runde 1
            valid_round = all(
                frozenset((m.team1.name, m.team2.name)) not in round1_pairs
                for m in round2
            )

        self.matches = round1 + round2

    def update_match_result(self, match_index, cups_left_team1, cups_left_team2, winner):
        match = self.matches[match_index]

        # Rull tilbake gammelt resultat hvis kampen var spilt
        if match.played:
            prev_c1 = match.team1_cups_left
            prev_c2 = match.team2_cups_left
            prev_w  = match.winner
            if prev_c1 is not None and prev_c2 is not None and prev_w in (1, 2):
                self._apply_result(match, prev_c1, prev_c2, prev_w, sign=-1)

        # Lagre nytt resultat og påfør
        match.team1_cups_left = cups_left_team1
        match.team2_cups_left = cups_left_team2
        match.winner = winner
        self._apply_result(match, cups_left_team1, cups_left_team2, winner, sign=+1)
        match.played = True


    def standings(self):
        return sorted(
            self.teams,
            key=lambda x: (-x.wins, -x.cups_hit, -x.total_cups_diff)
        )
    
    def _apply_result(self, match, cups_left_team1, cups_left_team2, winner, sign=+1):
        """Påfør (sign=+1) eller rull tilbake (sign=-1) et resultat i tabellen."""
        team1 = next(t for t in self.teams if t.name == match.team1.name)
        team2 = next(t for t in self.teams if t.name == match.team2.name)

        cups_hit_team1 = 10 - cups_left_team2
        cups_hit_team2 = 10 - cups_left_team1

        # Poeng
        if cups_left_team1 != cups_left_team2:
            if cups_left_team1 > cups_left_team2 and winner == 1:
                team1.wins += 2 * sign
            elif cups_left_team1 < cups_left_team2 and winner == 2:
                team2.wins += 2 * sign
            else:
                raise ValueError("Ugyldig kombinasjon av kopper/vinner")
        else:
            team1.wins += 1 * sign
            team2.wins += 1 * sign
            if winner == 1 and cups_left_team1 == cups_hit_team2:
                team1.wins += 1 * sign
            elif winner == 2 and cups_left_team1 == cups_hit_team2:
                team2.wins += 1 * sign
            else:
                raise ValueError("Ugyldig tie-break kombinasjon")

        # Statistikk
        team1.cups_hit += cups_hit_team1 * sign
        team1.cups_missed += cups_hit_team2 * sign
        team1.total_cups_diff = team1.cups_hit - team1.cups_missed

        team2.cups_hit += cups_hit_team2 * sign
        team2.cups_missed += cups_hit_team1 * sign
        team2.total_cups_diff = team2.cups_hit - team2.cups_missed

    def clear_match_result(self, match_index):
        match = self.matches[match_index]

        if not match.played:
            return

        prev_c1 = match.team1_cups_left
        prev_c2 = match.team2_cups_left
        prev_w  = match.winner
        if prev_c1 is not None and prev_c2 is not None and prev_w in (1, 2):
            self._apply_result(match, prev_c1, prev_c2, prev_w, sign=-1)

        match.team1_cups_left = None
        match.team2_cups_left = None
        match.winner = None
        match.played = False

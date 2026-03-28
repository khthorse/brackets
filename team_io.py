import csv
from pathlib import Path

import csv
from pathlib import Path

from models import Team


def _split_smart(line: str) -> list[str]:
    if "," in line:
        try:
            for row in csv.reader([line]):
                if len(row) > 1:
                    return [s.strip() for s in row]
        except Exception:
            pass

    for delim in [";", "|", "\t"]:
        if delim in line:
            return [s.strip() for s in line.split(delim)]

    return [line.strip()]


def parse_team_file(filepath: str) -> list[Team]:
    teams: list[Team] = []
    base = Path(filepath).parent

    with open(filepath, "r", encoding="utf-8-sig") as f:
        lines = f.read().splitlines()

    if lines and ("name" in lines[0].lower() and "logo" in lines[0].lower()):
        lines = lines[1:]

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = _split_smart(line)

        if len(parts) == 1:
            name = parts[0].strip()
            logo = None
        else:
            name = parts[0].strip()
            logo = parts[1].strip() if parts[1] else None

        if logo:
            logo = logo.strip('"').strip("'")

        if not name:
            continue

        if logo:
            p = Path(logo).expanduser()
            if not p.is_absolute():
                p = (base / p).resolve()
            logo = str(p)

        teams.append(Team(name=name, logo=logo))

    return teams


def teams_from_text(text: str) -> list[Team]:
    names = [line.strip() for line in text.splitlines() if line.strip()]
    return [Team(name=name) for name in names]
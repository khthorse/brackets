def normalize_time_input(value: str) -> str:
    value = value.strip()

    if ":" in value:
        parts = value.split(":")
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            hh = int(parts[0])
            mm = int(parts[1])
            return f"{hh:02d}:{mm:02d}"
        return value

    if value.isdigit():
        if len(value) <= 2:
            return f"{int(value):02d}:00"
        elif len(value) == 3:
            h = int(value[0])
            m = int(value[1:])
            return f"{h:02d}:{m:02d}"
        elif len(value) == 4:
            h = int(value[:2])
            m = int(value[2:])
            return f"{h:02d}:{m:02d}"

    return value


def is_valid_hhmm(value: str) -> bool:
    if len(value) != 5 or value[2] != ":":
        return False

    hh, mm = value.split(":")
    if not (hh.isdigit() and mm.isdigit()):
        return False

    hh = int(hh)
    mm = int(mm)
    return 0 <= hh <= 23 and 0 <= mm <= 59


def hhmm_to_seconds(value: str) -> int:
    hh, mm = map(int, value.split(":"))
    return hh * 60 + mm
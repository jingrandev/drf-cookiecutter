def level_filter(record, levels: str | int | list[str | int]) -> bool:
    if isinstance(levels, (str, int)):
        levels = [levels]
    for lvl in levels:
        if isinstance(lvl, str):
            if record["level"].name == lvl.upper():
                return True
        elif record["level"].no == lvl:
            return True
    return False


def single_level_filter(record, level: str | int) -> bool:
    return level_filter(record, level)

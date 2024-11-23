from enum import IntEnum


class MatchType(IntEnum):
    competitive = 0
    battle_royal = 1


class MatchStatus(IntEnum):
    preparing = 0
    in_progress = 1
    finished = 2
    cancelled = 3
from enum import IntEnum


class ETournamentStatus(IntEnum):
    PENDING = 0
    ACTIVE = 1
    FINISHED = 2
    CANCELLED = 3


class ETournamentMemberStatus(IntEnum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2

from enum import IntEnum


class ETeamMemberRole(IntEnum):
    OWNER = 0
    ADMIN = 1
    MEMBER = 2
    RESERVED = 3


class ETeamJoinRequestType(IntEnum):
    INVITE = 0
    REQUEST = 1

from enum import IntEnum


class TeamMemberRole(IntEnum):
    owner = 0
    admin = 1
    member = 2
    reserved = 3

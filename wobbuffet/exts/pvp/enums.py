from enum import Enum


class League(Enum):
    TEST = 0, 'Test'
    GREAT = 10, 'Great'
    ULTRA = 20, 'Ultra'
    MASTER = 30, 'Master'

    def __new__(cls, value, name):
        member = object.__new__(cls)
        member._value_ = value
        member.fullname = name
        return member

    def __int__(self):
        return self.value

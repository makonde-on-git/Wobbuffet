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

    @staticmethod
    def get_league(name):
        for league in League:
            if league.fullname == name:
                return league
        return None

    @staticmethod
    def get_all_leagues():
        leagues = []
        for league in League:
            leagues.append(league.fullname)
        return leagues

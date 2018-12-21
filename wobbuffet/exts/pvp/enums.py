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

    @staticmethod
    def get_league(name):
        for league in League:
            if league.fullname.lower() == name.lower():
                return league
        return None


class Ranking(Enum):
    WEEKLY = 0, 'pvp_week', 'tygodniowy'
    MONTHLY = 10, 'pvp_month', 'miesięczny'
    ALL_TIME = 20, 'pvp_all_time', 'wszechczasów'

    def __new__(cls, value, name, print_name):
        member = object.__new__(cls)
        member._value_ = value
        member.table_name = name
        member.print_name = print_name
        return member

from discord.ext.commands import CommandError
from wobbuffet.core.data_manager.errors import *


class MissingSubcommand(CommandError):
    pass


class PvPChannelCheckFail(CommandError):
    'Exception raised checks.pvpchannel fails'
    pass


class NonPvPChannelCheckFail(CommandError):
    'Exception raised checks.nonpvphannel fails'
    pass


class RankingChannelCheckFail(CommandError):
    'Exception raised checks.rankingchannel fails'
    pass


class NonRankingChannelCheckFail(CommandError):
    'Exception raised checks.nonrankingchannel fails'
    pass


# class ActiveChannelCheckFail(CommandError):
#     'Exception raised checks.activechannel fails'
#     pass
#
#
# class CityRaidChannelCheckFail(CommandError):
#     'Exception raised checks.cityraidchannel fails'
#     pass
#
#
# class RegionEggChannelCheckFail(CommandError):
#     'Exception raised checks.cityeggchannel fails'
#     pass
#
# class RegionExRaidChannelCheckFail(CommandError):
#     'Exception raised checks.allowexraidreport fails'
#     pass
#
#
# class ExRaidChannelCheckFail(CommandError):
#     'Exception raised checks.cityeggchannel fails'
#     pass
#
#
# class ResearchReportChannelCheckFail(CommandError):
#     'Exception raised checks.researchreport fails'
#     pass
#
#
# class MeetupReportChannelCheckFail(CommandError):
#     'Exception raised checks.researchreport fails'
#     pass
#
#
# class WildReportChannelCheckFail(CommandError):
#     'Exception raised checks.researchreport fails'
#     pass
#
#
# class TradeChannelCheckFail(CommandError):
#     'Exception raised checks.tradereport fails'
#     pass
#
#
# class TradeSetCheckFail(CommandError):
#     'Exception raised checks.tradeset fails'
#     pass

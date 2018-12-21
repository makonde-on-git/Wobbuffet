from wobbuffet.core.data_manager import schema
from .enums import Ranking


def setup(bot):
    pvp_history_table = bot.dbi.table('pvp_history')
    pvp_history_table.new_columns = [
        schema.IDColumn('guild_id', primary_key=True),
        schema.IntColumn('time', big=True, primary_key=True),
        schema.IDColumn('player1', primary_key=True),
        schema.IDColumn('player2', primary_key=True),
        schema.IDColumn('league', primary_key=True),
    ]

    pvp_tables = [pvp_history_table]
    for ranking in Ranking:
        table = bot.dbi.table(ranking.print_name)
        table.new_columns = [
            schema.IDColumn('guild_id', primary_key=True),
            schema.IDColumn('player', primary_key=True),
            schema.IDColumn('points'),
            schema.IDColumn('league', primary_key=True),
        ]
        pvp_tables.append(table)

    pvp_config_table = bot.dbi.table('pvp_config')
    pvp_config_table.new_columns = [
        schema.IDColumn('guild_id', primary_key=True),
        schema.IntColumn('elo_initial'),
        schema.IntColumn('elo_k'),
        schema.DecimalColumn('confirmation_timeout', precision=5, scale=2),
        schema.StringColumn('manage_channels'),
        schema.StringColumn('ranking_channels'),
        schema.StringColumn('league_channels')
    ]
    pvp_tables.append(pvp_config_table)

    return pvp_tables

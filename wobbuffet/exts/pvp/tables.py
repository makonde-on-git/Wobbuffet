from wobbuffet.core.data_manager import schema


def setup(bot):
    pvp_history_table = bot.dbi.table('pvp_history')
    pvp_history_table.new_columns = [
        schema.IDColumn('guild_id', primary_key=True),
        schema.IntColumn('time', big=True, primary_key=True),
        schema.IDColumn('player1', primary_key=True),
        schema.IDColumn('player2', primary_key=True),
        schema.IDColumn('league', primary_key=True),
    ]

    pvp_week_table = bot.dbi.table('pvp_week')
    pvp_week_table.new_columns = [
        schema.IDColumn('guild_id', primary_key=True),
        schema.IDColumn('player', primary_key=True),
        schema.IDColumn('points'),
        schema.IDColumn('league', primary_key=True),
    ]

    pvp_month_table = bot.dbi.table('pvp_month')
    pvp_month_table.new_columns = [
        schema.IDColumn('guild_id', primary_key=True),
        schema.IDColumn('player', primary_key=True),
        schema.IDColumn('points'),
        schema.IDColumn('league', primary_key=True),
    ]

    pvp_all_time_table = bot.dbi.table('pvp_all_time')
    pvp_all_time_table.new_columns = [
        schema.IDColumn('guild_id', primary_key=True),
        schema.IDColumn('player', primary_key=True),
        schema.IDColumn('points'),
        schema.IDColumn('league', primary_key=True),
    ]

    return [pvp_history_table, pvp_week_table, pvp_month_table, pvp_all_time_table]

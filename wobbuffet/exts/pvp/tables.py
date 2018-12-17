from wobbuffet.core.data_manager import schema


def setup(bot):
    pvp_table = bot.dbi.table('pvp')
    pvp_table.new_columns = [
        schema.IDColumn('guild_id', primary_key=True),
        schema.IntColumn('match_time', big=True),
        schema.IDColumn('player1'),
        schema.IDColumn('player2'),
        schema.BoolColumn('player1_won'),
        schema.IDColumn('league'),
    ]

    return pvp_table

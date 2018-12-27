import time

from .enums import League, Ranking


class Data:
    def __init__(self, bot):
        self.bot = bot
        self.defaults = {
            'elo_initial': (1000, lambda x: int(x), False),  # initial points for the new player
            'elo_k': (32, lambda x: int(x), False),  # k value for elo algorithm
            'confirmation_timeout': (5, lambda x: float(x), True),  # default confirmation timeout, in minutes
            'manage_channels': (0, lambda x: list(map(lambda y: int(y), x.split(','))), True),
            'ranking_channels': (0, lambda x: list(map(lambda y: int(y), x.split(','))), True),
            'league_channels': (0, lambda x: list(map(lambda y: int(y), x.split(','))), True),
        }

    def get_defaults(self):
        return self.defaults

    async def set_config(self, guild_id, field, value=None):
        if field not in self.defaults.keys():
            return "Niewłaściwe ustawienie"
        if not self.defaults[field][2]:
            return "To ustawienie nie może być zmienianie"
        try:
            if value is None:  # reset to default value
                value = self.defaults[field][0]
            config_table = self.bot.dbi.table('pvp_config')
            data = {'guild_id': guild_id, 'config_field': field, 'config_value': str(value)}
            query = config_table.insert().row(**data)
            await query.commit(do_update=True)
        except Exception as e:
            return e
        return None

    async def read_config(self, guild_id):
        config_table = self.bot.dbi.table('pvp_config')
        query = config_table.query().select().where(guild_id=guild_id)
        data = await query.get()
        config = {}
        for k, v in self.defaults.items():
            config[k] = v[0]
        for row in data:
            field = row['config_field']
            value = row['config_value']
            if field in self.defaults.keys():
                try:
                    config[field] = self.defaults[field][1](value)
                except Exception as e:
                    pass
        return config

    async def store_result(self, guild_id, player1, player2, league: League,
                           p1_pre_points, p1_post_points, p2_pre_points, p2_post_points):
        history_table = self.bot.dbi.table('pvp_history')
        query = history_table.insert()
        d = {
            'guild_id': guild_id,
            'time': int(time.time()),
            'player1': int(player1),
            'player2': int(player2),
            'league': int(league.value),
            'player1_pre_points': int(p1_pre_points),
            'player2_pre_points': int(p2_pre_points),
            'player1_post_points': int(p1_post_points),
            'player2_post_points': int(p2_post_points)
        }
        query.row(**d)
        await query.commit()

    async def get_player_points(self, guild_id, player, league: League, ranking: Ranking):
        table = self.bot.dbi.table(ranking.table_name)
        query = table.query().select().where(guild_id=guild_id, player=player, league=int(league.value))
        data = await query.get()
        if data:
            return data[0]['points']
        return None

    async def store_player_points(self, guild_id, player, points, league: League, ranking: Ranking, is_new=False):
        table = self.bot.dbi.table(ranking.table_name)
        # todo change to insert with commit(do_update=True) after test
        if is_new:
            query = table.insert()
            query.row(guild_id=guild_id, player=player, league=int(league.value), points=int(points))
        else:
            query = table.update().where(guild_id=guild_id, player=player, league=int(league.value))
            query.values(points=int(points))
        await query.commit()

    async def clear_league_data(self, guild_id, league: League, ranking: Ranking):
        table = self.bot.dbi.table(ranking.table_name)
        query = table.query().where(guild_id=guild_id, league=int(league.value))
        await query.delete()

    async def get_league_and_ranking_data(self, guild_id, league: League, ranking: Ranking):
        table = self.bot.dbi.table(ranking.table_name)
        query = table.query().select('row_number() OVER(ORDER BY points DESC) as rank', 'player', 'points')\
            .where(guild_id=guild_id, league=int(league.value))
        return await query.get()

    async def get_league_data(self, guild_id, league: League):
        data = {}
        for ranking in Ranking:
            data[ranking] = await self.get_league_and_ranking_data(guild_id, league, ranking)
        return data

    async def get_all_data(self, guild_id):
        data = {}
        for league in League:
            data[league] = await self.get_league_data(guild_id, league)
        return data

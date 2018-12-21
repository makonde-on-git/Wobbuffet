import asyncio
import time

from wobbuffet import Cog, command
from wobbuffet.utils.pagination import Pagination

from .enums import League, Ranking


class Elo:

    def __init__(self, initial: int, k: int):
        self.initial = initial
        self.k = k

    def calculate_new_score(self, p1_points=None, p2_points=None):
        """Calculates new points for two players. Assuming player 1 won, no draws possible."""
        p1_points = self.initial if p2_points is None else p1_points
        p2_points = self.initial if p2_points is None else p2_points
        p1_rating = pow(10, p1_points/400)
        p2_rating = pow(10, p2_points/400)
        p1_expected = p1_rating / (p1_rating + p2_rating)
        p2_expected = p2_rating / (p1_rating + p2_rating)
        p1_new_points = p1_points + int(self.k * (1 - p1_expected))
        p2_new_points = p2_points + int(self.k * (0 - p2_expected))
        return p1_new_points, p2_new_points

    def get_initial(self):
        return self.initial


class Data:

    def __init__(self, bot):
        self.bot = bot

    async def store_result(self, guild_id, player1, player2, league: League):
        history_table = self.bot.dbi.table('pvp_history')
        query = history_table.insert()
        d = {
            'guild_id': guild_id,
            'time': int(time.time()),
            'player1': int(player1),
            'player2': int(player2),
            'league': int(league.value)
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
            data[league] = await self.get_league_data(self, guild_id, league)
        return data


class E:

    def __init__(self, string):
        self.qualified_name = string
        self.usage = None
        self.clean_params = None


class PvP(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.elo = Elo(1000, 32)
        self.db = Data(bot)
        self.confirmation_timeout = 0.1  # in minutes
        self.points = {}
        self.player_points = {}
        for league in League:
            self.points[league] = {}
            self.player_points[league] = {}
            for ranking in Ranking:
                self.points[league][ranking] = []
                self.player_points[league][ranking] = {}

    @command()
    async def ranking(self, ctx, *, league):
        """"""

        to_delete = [ctx.message]
        league_enum = League.get_league(league)
        if league_enum is None:
            to_delete.append(
                await ctx.error("Niepoprawna liga. Dostępne ligi: {}"
                                .format(', '.join([l.fullname for l in League]))))
            await asyncio.sleep(10)
            await ctx.channel.delete_messages(to_delete)
            return

        ranking_enum = Ranking.WEEKLY
        strings = []
        for row in self.points[league_enum][ranking_enum]:
            member = ctx.guild.get_member(row['player'])
            if member and member.name:
                strings.append(E("#{} **{}** {}".format(row['rank'], member.name, row['points'])))
        await ctx.channel.delete_messages(to_delete)
        p = Pagination(ctx, strings, per_page=5, show_entry_count=False, title='Ranking', msg_type='info',
                       category_name='Liga "{}" ranking {}'.format(league_enum.fullname, ranking_enum.print_name),
                       simple_footer=True, allow_stop=True, allow_index=False, timeout=30)
        await p.paginate()

    # todo add channel check
    # todo add permissions
    @command()
    async def refresh_points(self, ctx, *, league=None):
        """Refreshes all players points for given league or all"""

        to_delete = [ctx.message]
        if league is not None:
            league_enum = League.get_league(league)
            if league_enum is None:
                to_delete.append(
                    await ctx.error("Niepoprawna liga. Dostępne ligi: {}"
                                    .format(', '.join([l.fullname for l in League]))))
                await asyncio.sleep(10)
                await ctx.channel.delete_messages(to_delete)
                return
            leagues = [league_enum]
        else:
            leagues = [l for l in League]

        await self._refresh_points(ctx.guild.id, leagues)
        await ctx.channel.delete_messages(to_delete)
        await ctx.success("Punkty odświeżone (ligi: {}).".format(", ".join([l.fullname for l in leagues])))

    async def _refresh_points(self, guild_id, leagues: list):
        for league in leagues:
            self.points[league] = await self.db.get_league_data(guild_id, league)
            player_points = {}
            for ranking in Ranking:
                player_points[ranking] = {}
                for row in self.points[league][ranking]:
                    player_points[ranking][row['player']] = row
            self.player_points[league] = player_points

    # todo add channel check
    # todo add permissions
    @command()
    async def reset(self, ctx, *, league):
        """Resets all players stats for given league"""

        to_delete = [ctx.message]
        league_enum = League.get_league(league)
        if league_enum is None:
            to_delete.append(
                await ctx.error("Niepoprawna liga. Dostępne ligi: {}"
                                .format(', '.join([l.fullname for l in League]))))
            await asyncio.sleep(10)
            await ctx.channel.delete_messages(to_delete)
            return

        should_delete = await ctx.ask(
            await ctx.help(
                "Skasuję dane wszystkich graczy dla ligi '{}'. Czy jesteś pewny?".format(league_enum.fullname),
                send=False),
            timeout=15)

        if should_delete is None:
            to_delete.append(await ctx.warning("Za wolno, spróbuj jeszcze raz."))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

        if should_delete is False:
            to_delete.append(await ctx.error("Anulowane"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

        await self.db.clear_league_data(ctx.guild.id, league_enum)
        await ctx.channel.delete_messages(to_delete)
        await ctx.success("Dane dla ligi {} skasowane.".format(league_enum.fullname))

    # todo add channel check
    @command()
    async def won_vs(self, ctx, *, pokonany_gracz):
        """Zgłoś wygraną przeciw innemu graczowi. @zawołaj go w komendzie."""

        to_delete = [ctx.message]
        player_1_id = ctx.message.author.id
        if len(ctx.message.mentions) != 1:
            to_delete.append(await ctx.error("Użyj @nick żeby wskazać kogo pokonałeś."))
            await asyncio.sleep(10)
            await ctx.channel.delete_messages(to_delete)
            return

        player_2_id = ctx.message.mentions[0].id
        if player_1_id == player_2_id:
            to_delete.append(await ctx.error("Nie możesz walczyć sam ze sobą!"))
            await asyncio.sleep(10)
            await ctx.channel.delete_messages(to_delete)
            return

        member_1 = ctx.guild.get_member(player_1_id)
        member_2 = ctx.guild.get_member(player_2_id)

        approved = await ctx.ask(
            await ctx.help("Potwierdzenie wyniku", fields={"Potwierdzasz przegraną": member_2.mention}, send=False),
            timeout=60*self.confirmation_timeout, author_id=player_2_id)
        approved = True  # todo hack
        if approved is None:
            status = {
                "Wygrana zgłoszona przez": member_1.mention,
                "Brak potwierdzenia przez": member_2.mention,
                "Dogadajcie się i zgłoś jeszcze raz": ""
            }
            await ctx.warning("Problem", fields=status)
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

        if not approved:
            status = {
                "Wygrana zgłoszona przez": member_1.mention,
                "Zaprzeczenie przez": member_2.mention,
                "Dogadajcie się i zgłoś jeszcze raz.": "Albo nie."
            }
            await ctx.error("Zaprzeczenie", fields=status)
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

        points = await self._update_rankings(ctx.guild.id, player_1_id, player_2_id, League.TEST)
        await self._refresh_points(ctx.guild.id, [League.TEST])
        #to_delete.append(await ctx.send("channel: {}".format(ctx.channel.id)))
        #to_delete.append(await ctx.send("channel name: {}".format(ctx.bot.get_channel(ctx.channel.id))))

        await ctx.channel.delete_messages(to_delete)
        status = {}
        for ranking in Ranking:
            status['Ranking ' + ranking.print_name] = "#{} {} +{} ({})\n#{} {} {} ({})".format(
                self.player_points[League.TEST][ranking][player_1_id]['rank'],
                member_1.name,
                points[ranking]['p1_new']-points[ranking]['p1_old'],
                points[ranking]['p1_new'],
                self.player_points[League.TEST][ranking][player_2_id]['rank'],
                member_2.name,
                points[ranking]['p2_new'] - points[ranking]['p2_old'],
                points[ranking]['p2_new'])
        await ctx.success("Gratulacje!", fields=status)

    async def _update_rankings(self, guild_id, player_1_id, player_2_id, league: League):
        points = {}
        await self.db.store_result(guild_id, player_1_id, player_2_id, league)
        for ranking in Ranking:
            p1_points = await self.db.get_player_points(guild_id, player_1_id, league, ranking)
            p2_points = await self.db.get_player_points(guild_id, player_2_id, league, ranking)
            p1_points, p1_is_new = (p1_points, False) if p1_points is not None else (self.elo.get_initial(), True)
            p2_points, p2_is_new = (p2_points, False) if p2_points is not None else (self.elo.get_initial(), True)
            p1_new_points, p2_new_points = self.elo.calculate_new_score(p1_points, p2_points)
            await self.db.store_player_points(guild_id, player_1_id, p1_new_points, league, ranking, p1_is_new)
            await self.db.store_player_points(guild_id, player_2_id, p2_new_points, league, ranking, p2_is_new)
            points[ranking] = {
                'p1_old': p1_points,
                'p1_new': p1_new_points,
                'p2_old': p2_points,
                'p2_new': p2_new_points
            }
        return points

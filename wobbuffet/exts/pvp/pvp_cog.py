import asyncio
import time

from wobbuffet import Cog, command

from .enums import League


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
            'league': int(league)
        }
        query.row(**d)
        await query.commit()

    async def get_player_points(self, guild_id, player, league: League):
        week_table = self.bot.dbi.table('pvp_week')
        query = week_table.query().select().where(guild_id=guild_id, player=player, league=int(league))
        data = await query.get()
        if data:
            return data[0]['points']
        return None

    async def store_player_points(self, guild_id, player, points, league: League, is_new=False):
        week_table = self.bot.dbi.table('pvp_week')
        if is_new:
            query = week_table.insert()
            query.row(guild_id=guild_id, player=player, league=int(league), points=int(points))
        else:
            query = week_table.update().where(guild_id=guild_id, player=player, league=int(league))
            query.values(points=int(points))
        await query.commit()

    async def clear_league_data(self, guild_id, league: League):
        week_table = self.bot.dbi.table('pvp_week')
        query = week_table.query().where(guild_id=guild_id, league=int(league))
        await query.delete()


class PvP(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.elo = Elo(1000, 32)
        self.db = Data(bot)

    # todo add channel check
    # todo add permissions
    @command()
    async def reset(self, ctx, *, league):
        """Resets all players stats for given league"""

        to_delete = [ctx.message]
        league_enum = League.get_league(league)
        if league_enum is None:
            to_delete.append(
                await ctx.error("Niepoprawna liga. Dostępne ligi: {}".format(', '.join(League.get_all_leagues()))))
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
            timeout=15, author_id=player_2_id)
        approved = True
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

        #to_delete.append(await ctx.send("channel: {}".format(ctx.channel.id)))
        #to_delete.append(await ctx.send("channel name: {}".format(ctx.bot.get_channel(ctx.channel.id))))

        p1_points = await self.db.get_player_points(ctx.guild.id, player_1_id, League.TEST)
        p2_points = await self.db.get_player_points(ctx.guild.id, player_2_id, League.TEST)
        p1_points = p1_points or self.elo.get_initial()
        p2_points = p2_points or self.elo.get_initial()
        p1_new_points, p2_new_points = self.elo.calculate_new_score(p1_points, p2_points)
        await self.db.store_player_points(
            ctx.guild.id, player_1_id, p1_new_points, League.TEST, True if not p1_points else False)
        await self.db.store_player_points(
            ctx.guild.id, player_2_id, p2_new_points, League.TEST, True if not p1_points else False)
        await self.db.store_result(ctx.guild.id, player_1_id, player_2_id, League.TEST)

        await ctx.channel.delete_messages(to_delete)
        status = {
            "Zwycięzca": "{}, +{} ({})".format(member_1.mention, p1_new_points-p1_points, p1_new_points),
            "Przegrany": "{}, {} ({})".format(member_2.mention, p2_new_points-p2_points, p2_new_points),
        }
        await ctx.success("Gratulacje!", fields=status)

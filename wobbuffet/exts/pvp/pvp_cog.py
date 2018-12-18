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


class PvP(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.elo = Elo(1000, 32)
        self.db = Data(bot)

    # todo add channel check
    @command()
    async def won_vs(self, ctx, *, defeted_player_mention):
        """Set your Pokemon Go team."""

        to_delete = [ctx.message]
        player_1_id = ctx.message.author.id
        if len(ctx.message.mentions) != 1:
            to_delete.append(await ctx.send("Użyj @nick żeby wskazać kogo pokonałeś."))
            await asyncio.sleep(10)
            await ctx.channel.delete_messages(to_delete)
            return

        player_2_id = ctx.message.mentions[0].id
        if player_1_id == player_2_id:
            to_delete.append(await ctx.send("Nie możesz walczyć sam ze sobą!"))
            await asyncio.sleep(10)
            await ctx.channel.delete_messages(to_delete)
            return

        # todo add confirmation

        #to_delete.append(await ctx.send("channel: {}".format(ctx.channel.id)))
        #to_delete.append(await ctx.send("channel name: {}".format(ctx.bot.get_channel(ctx.channel.id))))

        p1_points = await self.db.get_player_points(ctx.guild.id, player_1_id, League.TEST)
        p2_points = await self.db.get_player_points(ctx.guild.id, player_2_id, League.TEST)
        p1_new_points, p2_new_points = self.elo.calculate_new_score(p1_points, p2_points)
        member_1 = ctx.guild.get_member(player_1_id)
        member_2 = ctx.guild.get_member(player_2_id)
        to_delete.append(await ctx.send("{}: {} -> {}".format(member_1.name, p1_points, p1_new_points)))
        to_delete.append(await ctx.send("{}: {} -> {}".format(member_2.name, p2_points, p2_new_points)))
        await self.db.store_player_points(
            ctx.guild.id, player_1_id, p1_new_points, League.TEST, True if not p1_points else False)
        await self.db.store_player_points(
            ctx.guild.id, player_2_id, p2_new_points, League.TEST, True if not p1_points else False)
        await self.db.store_result(ctx.guild.id, player_1_id, player_2_id, League.TEST)

        await asyncio.sleep(60)
        await ctx.channel.delete_messages(to_delete)

import asyncio

from wobbuffet import Cog, command
from wobbuffet.utils.pagination import Pagination
from wobbuffet.core import checks

from .enums import League, Ranking
from .elo import Elo
from .data import Data
from . import checks as pvp_checks


class PaginationElement:
    def __init__(self, string):
        self.qualified_name = string
        self.usage = None
        self.clean_params = None


class PvP(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Data(bot)
        self.config = None

    async def _initialize(self, guild_id, reinitialize=False):
        if self.config is not None:
            if reinitialize:
                self.config = await self.db.read_config(guild_id)
                self.elo = Elo(self.config['elo_initial'], self.config['elo_k'])
                # todo recount points based on history table?
            return
        self.config = await self.db.read_config(guild_id)
        self.elo = Elo(self.config['elo_initial'], self.config['elo_k'])
        self.points = {}
        self.player_points = {}
        for league in League:
            self.points[league] = {}
            self.player_points[league] = {}
            for ranking in Ranking:
                self.points[league][ranking] = []
                self.player_points[league][ranking] = {}
        # initialize points
        leagues = [l for l in League]
        await self._refresh_points(guild_id, leagues)

    @command(name='pvp_config', category='PvP')
    @checks.is_co_owner()
    async def _config(self, ctx, *, action=None, field=None, value=None):
        """Wyświetla lub modyfikuje konfigurację"""
        to_delete = [ctx.message]
        await self._check_initialization(ctx.guild.id)
        if not await pvp_checks.is_proper_channel(ctx, self.config['manage_channels']):
            to_delete.append(await ctx.error("Niewłaściwy kanał"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return
        if action is not None:
            if action not in ["set", "reset"]:
                to_delete.append(await ctx.error("Niewłaściwa akcja. Dostępne akcje to: **set** i **reset**"))
                await asyncio.sleep(10)
                await ctx.channel.delete_messages(to_delete)
                return
            defaults = self.db.get_defaults()
            if field not in defaults.keys():
                to_delete.append(await ctx.error("Niewłaściwe ustawienie. Dostępne ustawienia to: **" + "**, **".join(defaults.keys()) + "**"))
                await asyncio.sleep(10)
                await ctx.channel.delete_messages(to_delete)
                return
            if action == "reset":
                value = None
            if action == "set" and value is None:
                to_delete.append(await ctx.error("Brak wartości dla ustawienia **{}**".format(field)))
                await asyncio.sleep(10)
                await ctx.channel.delete_messages(to_delete)
                return
            result = self.db.set_config(ctx.guild.id, field, value)
            if result is not None:
                to_delete.append(await ctx.error("Błąd podczas zmiany wartości ustawienia **{}**: {}".format(field, result)))
                await asyncio.sleep(15)
                await ctx.channel.delete_messages(to_delete)
                return
            await self._check_initialization(ctx.guild.id, reinitialize=True)
            to_delete.append(await ctx.success("Zmieniono wartość pola **{}** na {}".format(field, "domyślną" if value is None else value)))
        message = []
        for k, v in self.config.items():
            message.append("{}: {}".format(k, v))
        to_delete(await ctx.info("Aktualne wartości ustawień", "\n".join(message)))
        await asyncio.sleep(30)
        await ctx.channel.delete_messages(to_delete)
        return

    @command(name='pvp_ranking_week', category='PvP')
    async def _ranking_week(self, ctx, *, league):
        """Wyświetla tygodniowy ranking danej ligi"""
        await self._check_initialization(ctx.guild.id)
        await self._ranking(ctx, league, Ranking.WEEKLY)

    @command(name='pvp_ranking_month', category='PvP')
    async def _ranking_month(self, ctx, *, league):
        """Wyświetla miesięczny ranking danej ligi"""
        await self._check_initialization(ctx.guild.id)
        await self._ranking(ctx, league, Ranking.MONTHLY)

    @command(name='pvp_ranking_all', category='PvP')
    async def _ranking_all(self, ctx, *, league):
        """Wyświetla ranking wszechczasów danej ligi"""
        await self._check_initialization(ctx.guild.id)
        await self._ranking(ctx, league, Ranking.ALL_TIME)

    async def _ranking(self, ctx, league, ranking: Ranking):
        to_delete = [ctx.message]
        if not await pvp_checks.is_proper_channel(ctx, self.config['ranking_channels']):
            to_delete.append(await ctx.error("Niewłaściwy kanał"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return
        league_enum = League.get_league(league)
        if league_enum is None:
            to_delete.append(await ctx.error("Niepoprawna liga. Dostępne ligi: {}"
                                             .format(', '.join([l.fullname for l in League]))))
            await asyncio.sleep(10)
            await ctx.channel.delete_messages(to_delete)
            return

        elements = []
        for row in self.points[league_enum][ranking]:
            member = ctx.guild.get_member(row['player'])
            if member and member.name:
                elements.append(PaginationElement("#{} **{}** {}".format(row['rank'], member.name, row['points'])))
        await ctx.channel.delete_messages(to_delete)
        p = Pagination(ctx, elements, per_page=10, show_entry_count=False, title='Ranking', msg_type='info',
                       category_name='Liga "{}" ranking {}'.format(league_enum.fullname, ranking.print_name),
                       simple_footer=True, allow_stop=True, allow_index=False, timeout=30)
        await p.paginate()

    @command(name='pvp_refresh_points', category='PvP')
    @checks.is_co_owner()
    async def _refresh(self, ctx, *, league=None):
        """Przeładowuje rankingi dla zadanej ligi lub wszystkich lig"""
        to_delete = [ctx.message]
        if not await pvp_checks.is_proper_channel(ctx, self.config['manage_channels']):
            to_delete.append(await ctx.error("Niewłaściwy kanał"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return
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

    @command(name='pvp_reset_week', category='PvP')
    @checks.is_co_owner()
    async def _reset_week(self, ctx, *, league):
        """Resetuje tygodniowy ranking dla danej ligi"""
        await self._ranking(ctx, league, Ranking.WEEKLY)

    @command(name='pvp_reset_month', category='PvP')
    @checks.is_co_owner()
    async def _reset_month(self, ctx, *, league):
        """Resetuje miesięczny ranking dla danej ligi"""
        await self._ranking(ctx, league, Ranking.MONTHLY)

    @command(name='pvp_reset_all', category='PvP')
    @checks.is_co_owner()
    async def _reset_all(self, ctx, *, league):
        """Resetuje ranking wszechczasów dla danej ligi"""
        await self._ranking(ctx, league, Ranking.ALL_TIME)

    async def _reset(self, ctx, *, league, ranking: Ranking):
        """Resets all players stats for given league"""
        to_delete = [ctx.message]
        if not await pvp_checks.is_proper_channel(ctx, self.config['manage_channels']):
            to_delete.append(await ctx.error("Niewłaściwy kanał"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

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
                "Skasuję ranking {} dla ligi '{}'. Czy jesteś pewny?".format(ranking.print_name, league_enum.fullname),
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

        await self.db.clear_league_data(ctx.guild.id, league_enum, ranking)
        await self._refresh_points(ctx.guild.id, [league_enum])
        await ctx.channel.delete_messages(to_delete)
        await ctx.success("Ranking {} ligi {} skasowany.".format(ranking.print_name, league_enum.fullname))

    async def _check_initialization(self, guild_id, reinitialize=False):
        if self.config is None or reinitialize:
            await self._initialize(guild_id, reinitialize)

    @command(name='pvp_rank', category='PvP')
    async def _rank(self, ctx):
        """Sprawdź swój ranking"""
        await self._check_initialization(ctx.guild.id)

        to_delete = [ctx.message]
        if not await pvp_checks.is_proper_channel(ctx, self.config['ranking_channels']):
            to_delete.append(await ctx.error("Niewłaściwy kanał"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

        player_id = ctx.message.author.id
        member = ctx.guild.get_member(player_id)
        status = {}
        for ranking in Ranking:
            messages = []
            for league in League:
                messages.append("{}: #{} {}".format(league.fullname,
                                                    self.player_points[league][ranking][player_id]['rank'],
                                                    self.player_points[league][ranking][player_id]['points']))
            messages = "\n".join(messages)
            status['Ranking ' + ranking.print_name] = messages
        await ctx.channel.delete_messages(to_delete)
        to_delete = [await ctx.success("Rankingi {}".format(member.name), fields=status)]
        await asyncio.sleep(30)
        await ctx.channel.delete_messages(to_delete)

    @command(name='pvp_won_vs', category='PvP')
    async def _won_vs(self, ctx, *, pokonany_gracz):
        """Zgłoś wygraną przeciw innemu graczowi. @zawołaj go w komendzie"""
        await self._check_initialization(ctx.guild.id)

        to_delete = [ctx.message]
        if not await pvp_checks.is_proper_channel(ctx, self.config['league_channels']):
            to_delete.append(await ctx.error("Niewłaściwy kanał"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

        channel_name = ctx.channel.name
        league = League.get_league(channel_name)
        if league is None:
            to_delete.append(await ctx.error("Niewłaściwy kanał"))
            await asyncio.sleep(5)
            await ctx.channel.delete_messages(to_delete)
            return

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
            timeout=60*self.config['confirmation_timeout'], author_id=player_2_id)
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

        points = await self._update_rankings(ctx.guild.id, player_1_id, player_2_id, league)
        await self._refresh_points(ctx.guild.id, [league])

        await ctx.channel.delete_messages(to_delete)
        status = {}
        for ranking in Ranking:
            status['Ranking ' + ranking.print_name] = "#{} {} +{} ({})\n#{} {} {} ({})".format(
                self.player_points[league][ranking][player_1_id]['rank'],
                member_1.name,
                points[ranking]['p1_new']-points[ranking]['p1_old'],
                points[ranking]['p1_new'],
                self.player_points[league][ranking][player_2_id]['rank'],
                member_2.name,
                points[ranking]['p2_new'] - points[ranking]['p2_old'],
                points[ranking]['p2_new'])
        await ctx.success("Gratulacje!", fields=status)

    async def _update_rankings(self, guild_id, player_1_id, player_2_id, league: League):
        points = {}
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
        await self.db.store_result(guild_id, player_1_id, player_2_id, league,
                                   points[ranking.ALL_TIME]['p1_old'], points[ranking.ALL_TIME]['p1_new'],
                                   points[ranking.ALL_TIME]['p2_old'], points[ranking.ALL_TIME]['p2_new'])
        return points

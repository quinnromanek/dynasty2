from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from dynasty.models import Player, Team, Game, PlayerStats, Season
from django.db.models import Q, Sum, Avg
from django.views.generic import TemplateView
from dynasty.models.game import regular_season_games
from dynasty.models.playoffs import Series
from dynasty.models.team import seed
from dynasty.utils import parse_position_string
from dynasty2.settings import STATIC_URL
from dynasty import constants
from itertools import chain


class DynastyView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(DynastyView, self).get_context_data(**kwargs)
        season = Season.objects.get(name="main")
        context['ticker_enabled'] = False
        if season is not None:
            context['season'] = season
            context['static_url'] = STATIC_URL
            context['finished_games'] = Game.objects.filter(week=season.week - 1,
                                                            season=season.year) if season.week > 0 else []
            context['next_games'] = Game.objects.filter(week=season.week, season=season.year)
        return context


# Create your views here.

def index(request):
    return render(request, 'index.html')


class TeamView(DynastyView):
    template_name = 'team.html'

    def get_context_data(self, **kwargs):
        context = super(TeamView, self).get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, name=context['team_name'].capitalize())
        team = context['team']
        context['players'] = team.starters() + team.bench()
        playoff_games = Game.objects.filter(Q(away_team=team) | Q(home_team=team), week__lt=0).order_by("series__round", "-week")
        context['season_games'] = chain(regular_season_games(context['team']), playoff_games)
        return context


def teams(request):
    """ A list of teams """
    divs = []
    for i in range(4):
        divs.append(Team.objects.filter(division=i).order_by("-wins"))

    return render(request, 'teams.html', {'divs': divs})


class TeamsView(DynastyView):
    template_name = 'teams.html'

    def get_context_data(self, **kwargs):
        context = super(TeamsView, self).get_context_data(**kwargs)

        divs = []
        for i in range(4):
            divs.append(seed(list(Team.objects.filter(division=i).order_by("-wins")), context['season']))

        all_teams = Team.objects.all().order_by("-wins")
        wildcards = []
        for team in list(all_teams):
            if team.div_rank() != 1:
                wildcards.append(team)

        wildcards = seed(wildcards, context['season'])

        wildcards = [w.id for w in wildcards[:2]]
        context['wildcards'] = wildcards


        confs = []
        confs.append(seed(list(Team.objects.filter(Q(division=0) | Q(division=1)).order_by("-wins")), context['season']))
        confs.append(seed(list(Team.objects.filter(Q(division=2) | Q(division=3)).order_by("-wins")), context['season']))

        context['confs'] = confs
        context['divs'] = divs
        return context


def players(request):
    return HttpResponse("Players list page")


def games(request):
    weeks = []
    for week_num in range(constants.SEASON_LENGTH):
        weeks.append(Game.objects.filter(week=week_num))

    return render(request, 'games.html', {'weeks': weeks})


class GamesView(DynastyView):
    template_name = 'games.html'

    def get_context_data(self, **kwargs):
        context = super(GamesView, self).get_context_data(**kwargs)
        weeks = []
        for week_num in range(constants.SEASON_LENGTH):
            weeks.append(Game.objects.filter(season=context['season'].year, week=week_num))
        context['weeks'] = weeks
        if context['season'].in_playoffs():
            context['rd1'] = Series.objects.filter(season=context['season'], round=1).order_by("-home_team_seed")
            context['rd2'] = Series.objects.filter(season=context['season'], round=2).order_by("home_team_seed")
            context['championship'] = Series.objects.get(season=context['season'], round=3)

        return context


def game(request, game_id):
    current_game = get_object_or_404(Game, id=game_id)
    home_stats = []
    away_stats = []
    if current_game.is_finished():
        home_stats = PlayerStats.objects.filter(Q(game__id=game_id) & Q(team=current_game.home_team)).order_by("roster")
        away_stats = PlayerStats.objects.filter(Q(game__id=game_id) & Q(team=current_game.away_team)).order_by("roster")

    return render(request, 'game.html', {'game': current_game, "home_stats": home_stats, "away_stats": away_stats})


class GameView(DynastyView):
    template_name = 'game.html'

    def get_context_data(self, **kwargs):

        def get_team_stats(team, game):
            stats = PlayerStats.objects.filter(Q(game=game) & Q(team=team)).aggregate(
                Sum('steals'), Sum('rebounds'), Sum('field_goals'), Sum('field_goals_attempted'), Sum('assists')
            )
            return stats
        context = super(GameView, self).get_context_data(**kwargs)
        game_id = context['game_id']
        current_game = get_object_or_404(Game, id=game_id)
        home_stats = []
        away_stats = []
        if current_game.is_finished():
            home_stats = PlayerStats.objects.filter(Q(game__id=game_id) & Q(team=current_game.home_team)).order_by(
                "roster")
            away_stats = PlayerStats.objects.filter(Q(game__id=game_id) & Q(team=current_game.away_team)).order_by(
                "roster")
        home_stats = list(home_stats)
        away_stats = list(away_stats)
        home_stats = home_stats[-5:] + home_stats[:-5]
        away_stats = away_stats[-5:] + away_stats[:-5]
        context['game'] = current_game
        context['home_stats'] = home_stats
        context['away_stats'] = away_stats
        context['home_team_stats'] = get_team_stats(current_game.home_team, current_game)
        context['away_team_stats'] = get_team_stats(current_game.away_team, current_game)
        return context


class PlayerView(DynastyView):
    template_name = "player.html"

    def get_context_data(self, **kwargs):
        context = super(PlayerView, self).get_context_data(**kwargs)
        player_id = context['player_id']
        player = get_object_or_404(Player, id=player_id)

        playoff_games = PlayerStats.objects.filter(player=player, game__week__lt=0).order_by("-game__series__round", "game__week")
        last_games = PlayerStats.objects.filter(player=player, game__week__gte=0).order_by("-game__season", "-game__week")[:(10-playoff_games.count())]

        context['last_games'] = chain(playoff_games, last_games)
        context['player'] = player
        return context


class PlayersView(DynastyView):
    template_name = "players.html"


    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        team = request.GET.get("team")
        team_names = [t.name for t in Team.objects.all()] + ["Free Agents"]
        if team in team_names:
            if team == "Free Agents":
                player_list = Player.objects.all().filter(team=None).order_by("name")
            else:
                player_list = Player.objects.all().filter(team__name=team).order_by("name")
        else:
            player_list = Player.objects.all().order_by("name")

        context['team_names'] = ["All"] + team_names
        context['team'] = team
        position_filter = request.GET.get('position')
        valid_orders = ['name', 'team', 'offense', 'defense', 'athletics', 'stamina', 'spg', 'apg', 'rpg', 'ppg']
        order = request.GET.get('order_by')
        context['order'] = ""
        if order is not None and order in valid_orders:
            context['order'] = order
            if order.endswith("pg"):
                stat = ""
                if order == "spg":
                    stat="steals"
                elif order == "apg":
                    stat = "assists"
                elif order == "rpg":
                    stat = "rebounds"
                else:
                    stat = "field_goals"
                player_list = player_list.annotate(stat_average=Avg("playerstats__" + stat)).order_by("-stat_average")
            else:
                player_list = player_list.order_by("-" + order)

        context['pos'] = ""
        if position_filter is not None and position_filter in ["PG", "SG", "SF", "PF", "C"]:
            context['pos'] = position_filter
            pos = parse_position_string(position_filter)
            player_list = player_list.filter(Q(primary_position=pos) | Q(secondary_position=pos))

        paginator = Paginator(player_list, 25)

        page = request.GET.get('page')

        if page is None:
            page = 1
        right_button = int(page) < paginator.num_pages
        left_button = int(page) > 1
        try:
            players = paginator.page(page)
        except PageNotAnInteger:
            players = paginator.page(1)
            page = 1
            left_button = False
        except EmptyPage:
            players = paginator.page(paginator.num_pages)
            page = paginator.num_pages
            right_button = False

        context['players'] = players
        context['page'] = int(page)
        context['page_range'] = paginator.page_range
        context['num_pages'] = paginator.num_pages

        return self.render_to_response(context)


class SeriesView(DynastyView):
    template_name = "series.html"

    def get_context_data(self, **kwargs):
        context = super(SeriesView, self).get_context_data(**kwargs)
        series_id = context['series_id']
        series = get_object_or_404(Series, id=series_id)

        context['series'] = series
        context['games'] = series.game_set.order_by("-week")

        return context




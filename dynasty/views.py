from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from dynasty.models import Player, Team, Game, PlayerStats, Season
from django.db.models import Q
from django.views.generic import TemplateView
from dynasty.models.game import season_games
from dynasty2.settings import STATIC_URL


class DynastyView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(DynastyView, self).get_context_data(**kwargs)
        season = Season.objects.get(name="main")
        context['ticker_enabled'] = True
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
        context['season_games'] = season_games(context['team'])
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
            divs.append(Team.objects.filter(division=i).order_by("-wins"))
        context['divs'] = divs
        return context


def players(request):
    return HttpResponse("Players list page")


def games(request):
    weeks = []
    for week_num in range(11):
        weeks.append(Game.objects.filter(week=week_num))

    return render(request, 'games.html', {'weeks': weeks})


class GamesView(DynastyView):
    template_name = 'games.html'

    def get_context_data(self, **kwargs):
        context = super(GamesView, self).get_context_data(**kwargs)
        weeks = []
        for week_num in range(11):
            weeks.append(Game.objects.filter(week=week_num))
        context['weeks'] = weeks
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
        return context


class PlayerView(DynastyView):
    template_name = "player.html"

    def get_context_data(self, **kwargs):
        context = super(PlayerView, self).get_context_data(**kwargs)
        player_id = context['player_id']
        player = get_object_or_404(Player, id=player_id)
        context['player'] = player
        return context


class PlayersView(DynastyView):
    template_name = "players.html"


    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        player_list = Player.objects.all().order_by("-offense")
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




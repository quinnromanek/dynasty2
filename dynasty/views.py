from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from dynasty.models import Player, Team, Game, PlayerStats
from django.db.models import Q

# Create your views here.
def index(request):
    return render(request, 'index.html')


def team(request, team_name):
    currentTeam = get_object_or_404(Team, name=team_name.capitalize())
    return render(request, 'team.html', {'team': currentTeam})


def teams(request):
    """ A list of teams """
    divs = []
    for i in range(4):
        divs.append(Team.objects.filter(division=i).order_by("-wins"))

    return render(request, 'teams.html', {'divs': divs})


def players(request):
    return HttpResponse("Players list page")


def games(request):
    weeks = []
    for week_num in range(11):
        weeks.append(Game.objects.filter(week=week_num))

    return render(request, 'games.html', {'weeks': weeks})


def game(request, game_id):
    current_game = get_object_or_404(Game, id=game_id)
    home_stats = []
    away_stats = []
    if current_game.is_finished():
        home_stats = PlayerStats.objects.filter(Q(game__id=game_id) & Q(team=current_game.home_team)).order_by("roster")
        away_stats = PlayerStats.objects.filter(Q(game__id=game_id) & Q(team=current_game.away_team)).order_by("roster")

    return render(request, 'game.html', {'game':current_game, "home_stats":home_stats, "away_stats":away_stats})
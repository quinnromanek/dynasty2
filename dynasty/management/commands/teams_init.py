from django.core.management.base import BaseCommand

from dynasty.constants import TEAMS

from dynasty.league import run_draft, create_random_player, create_schedule

from dynasty.models import Team, Player, Game, Season, PlayerStats, Series, Contract
from dynasty.models.team import set_best_rotation


def make_teams():
    """ Cleans all teams and repopulates divisions. """
    Team.objects.all().delete()

    for div in [0, 1, 2, 3]:
        for tname in TEAMS[div]:
            Team.objects.create(name=tname, division=div)


def generate_team(team):
    for starter in range(1, 6):
        create_random_player(team=team, position=starter, roster=starter)
    for player in range(7):
        create_random_player(team=team)

    set_best_rotation(team)

def set_team_rotations():
    teams = Team.objects.all()
    for team in teams:
        set_best_rotation(team)

def generate_players_for_teams():
    Player.objects.all().delete()
    teams = Team.objects.all()
    for team in teams:
        generate_team(team)


class Command(BaseCommand):
    help = "Cleans all teams and repopulates divisions"

    def handle(self, *args, **options):
        Season.objects.all().delete()
        PlayerStats.objects.all().delete()
        Series.objects.all().delete()
        Player.objects.all().delete()
        Game.objects.all().delete()
        Team.objects.all().delete()
        Season.objects.all().delete()
        Contract.objects.all().delete()
        season = Season.objects.create(name="main")
        make_teams()
        create_schedule(season)
        run_draft(season, expansion=True)
        for player in Player.objects.all():
            player.grow_year()

        set_team_rotations()
        self.stdout.write("Success.")

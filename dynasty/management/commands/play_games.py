__author__ = 'flex109'

from django.core.management import BaseCommand
from dynasty.models import Season, Game, Team

class Command(BaseCommand):
    def handle(self, *args, **options):
        season = Season.objects.get(name="main")
        games = Game.objects.filter(week=season.week, season=season.year)
        for game in games:
            game.play()
            self.stdout.write("{0}:{1} {2}:{3}".format(game.home_team.name, game.homeScore, game.away_team.name,
                                                       game.awayScore))
            game.save()
            home = Team.objects.get(id=game.home_team.id)
            away = Team.objects.get(id=game.away_team.id)
            if game.homeScore > game.awayScore:
                home.wins += 1
                away.losses += 1
            else:
                home.losses += 1
                away.wins += 1

            home.save()
            away.save()


        self.stdout.write("Week {0} completed.".format(season.week))

        season.week += 1
        season.save()


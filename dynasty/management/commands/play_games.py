from django.db.models import Q
from dynasty.models.playoffs import Series
from dynasty.models.team import seed

__author__ = 'flex109'

from django.core.management import BaseCommand
from dynasty.models import Season, Game, Team
from dynasty import constants

def start_playoffs(season):
    all_teams = seed(list(Team.objects.all().order_by("-wins")))
    playoff_teams = []
    wild_cards = 0
    for team in all_teams:
        if team.div_rank() == 1 or wild_cards < 2:
            playoff_teams.append(team)

    playoff_teams = seed(playoff_teams)
    championship = Series.objects.create(season=season, round=3)
    round2 = []
    for r2 in xrange(2):
        round2.append(Series.objects.create(advance=championship, season=season, round=2, home_team=playoff_teams[r2], home_team_seed=(r2+1)))

    # 3 v 6 matchup
    Series.objects.create(advance=round2[1], season=season, round=1,
                          home_team=playoff_teams[2], home_team_seed=3,
                          away_team=playoff_teams[5], away_team_seed=6)
    # 4 v 5 matchup
    Series.objects.create(advance=round2[0], season=season, round=1,
                          home_team=playoff_teams[3], home_team_seed=4,
                          away_team=playoff_teams[4], away_team_seed=5)

    for series in Series.objects.filter(round=1, season=season):
        series.begin()

def set_title_playoffs(season):
    season.title = "Playoffs: Round {0}".format(season.playoff_round)
    story = ""
    for series in Series.objects.filter(season=season, round=season.playoff_round):
        story += "<a href='/series/{0}'>{1} vs {2}</a> ".format(series.id, series.home_team.name, series.away_team.name)

    season.story = story





class Command(BaseCommand):
    def handle(self, *args, **options):
        season = Season.objects.get(name="main")
        if season.playoff_round == 0:
            games = Game.objects.filter(week=season.week, season=season.year)
        else:
            games = Game.objects.filter(week=season.week, series__round=season.playoff_round, season=season.year)

        for game in games:
            game.play()
            self.stdout.write("{0}:{1} {2}:{3}".format(game.home_team.name, game.homeScore, game.away_team.name,
                                                       game.awayScore))
            game.save()
            home = game.home_team
            away = game.away_team
            if season.playoff_round == 0:
                if game.homeScore > game.awayScore:
                    home.wins += 1
                    away.losses += 1
                else:
                    home.losses += 1
                    away.wins += 1

            home.save()
            away.save()


        self.stdout.write("Week {0} completed.".format(season.week))
        if season.playoff_round == 0:
            # Week is finished.
            season.week += 1
            season.title = "Week {0} Story.".format(season.week + 1)
            if season.week == constants.SEASON_LENGTH:
                # Week is finished, playoffs begin.
                self.stdout.write("Playoffs will begin next week.")
                season.playoff_round = 1
                season.week = -1
                start_playoffs(season)
                set_title_playoffs(season)
        else:
            if Series.objects.filter(Q(home_team_wins__lt=constants.PLAYOFF_WINS) & Q(away_team_wins__lt=constants.PLAYOFF_WINS),
                                     round=season.playoff_round, season=season).count() == 0:
                # All series in round are finished.
                if season.playoff_round == 3:
                    # Season is done. Crown new champion
                    season.champion = Series.objects.filter(season=season).get(round=3).winner().name
                    self.stdout.write("{0} have won the title.".format(season.champion))
                else:
                    self.stdout.write("Playoff round {0} complete.".format(season.playoff_round))
                    # Move on to the next round. The teams should have been placed already.
                    season.playoff_round += 1
                    for series in Series.objects.filter(season=season, round=season.playoff_round):
                        series.begin()
                    season.week = -1
                    set_title_playoffs(season)
            else:
                # Keep playing the series.
                season.week -= 1

        season.save()




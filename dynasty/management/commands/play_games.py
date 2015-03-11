from django.db.models import Q

from dynasty.league import start_playoffs, finish_season, play_regular_season_week, play_playoff_week, play_offseason_week
from dynasty.models.playoffs import Series


__author__ = 'flex109'

from django.core.management import BaseCommand
from dynasty.models import Season, Game
from dynasty import constants







def set_title_playoffs(season):
    season.title = "Playoffs: Round {0}".format(season.playoff_round)
    story = ""
    for series in Series.objects.filter(season=season, round=season.playoff_round):
        story += "<a href='/series/{0}'>{1} vs {2}</a> ".format(series.id, series.home_team.name, series.away_team.name)

    season.story = story





class Command(BaseCommand):
    def handle(self, *args, **options):
        season = Season.objects.get(name="main")
        if season.in_regular_season():
            play_regular_season_week(season)
        elif season.in_playoffs():
            play_playoff_week(season)
        elif season.in_offseason():
            play_offseason_week(season)



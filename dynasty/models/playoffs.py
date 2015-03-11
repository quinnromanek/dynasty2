from django.db import models
from dynasty import constants

__author__ = 'flex109'

class Series(models.Model):
    home_team = models.ForeignKey("dynasty.team", related_name="home_series", null=True, default=None)
    away_team = models.ForeignKey("dynasty.team", related_name="away_series", null=True, default=None)
    home_team_wins = models.IntegerField(default=0)
    away_team_wins = models.IntegerField(default=0)
    home_team_seed = models.IntegerField(default=0)
    away_team_seed = models.IntegerField(default=0)
    season = models.ForeignKey("dynasty.season")
    round = models.IntegerField(default=0)
    advance = models.ForeignKey("self", null=True, default=None)

    class Meta:
        app_label="dynasty"
        db_table="dynasty_series"

    def __unicode__(self):
        return "Round {0}: {1} vs {2}".format(self.round, self.home_team, self.away_team)

    def is_over(self):
        return self.home_team_wins == constants.PLAYOFF_WINS or self.away_team_wins == constants.PLAYOFF_WINS

    def winner(self):
        if self.home_team_wins == constants.PLAYOFF_WINS:
            return self.home_team
        elif self.away_team_wins == constants.PLAYOFF_WINS:
            return self.away_team

    def begin(self):
        if self.home_team_seed > self.away_team_seed:
            temp_team, temp_seed = self.home_team, self.home_team_seed
            self.home_team, self.home_team_seed = self.away_team, self.away_team_seed
            self.away_team, self.away_team_seed = temp_team, temp_seed
        self.save()
        self.game_set.create(home_team=self.home_team, away_team=self.away_team, week=-1, season=self.season.year)

    def game_finished(self, game):
        if game.winner().id == self.home_team.id:
            self.home_team_wins += 1
        elif game.winner().id == self.away_team.id:
            self.away_team_wins += 1
        self.save()

        if self.is_over() and self.advance is not None:
            seed = 7
            if self.winner().id == self.home_team.id:
                seed = self.home_team_seed
            elif self.winner().id == self.away_team.id:
                seed = self.away_team_seed

            if self.advance.home_team is None:
                self.advance.home_team = self.winner()
                self.advance.home_team_seed = seed
            else:
                self.advance.away_team = self.winner()
                self.advance.away_team_seed = seed
            self.advance.save()
        elif self.is_over() and self.advance is None:
            pass
        else:
            self.game_set.create(home_team=self.home_team, away_team=self.away_team, week=(game.week-1), season=self.season.year )

        self.save()







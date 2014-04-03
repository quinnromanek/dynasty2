from django.db import models
from django.db.models import Q
def position_string(pos):
	arr = ["Null", "PG", "SG", "SF", "PF", "C"]
	return arr[pos]

# Create your models here.
class Team(models.Model):
	name = models.CharField(max_length=50)
	wins = models.IntegerField(default=0)
	losses = models.IntegerField(default=0)
	division = models.IntegerField(default=0)

	def __unicode__(self):
		return "{0} ({1}-{2})".format(self.name, self.wins, self.losses)

	def win_pct(self):
		return float(self.wins)/(float(self.wins+self.losses))

	def season_games(self):
		return Game.objects.filter(Q(away_team__id=self.id) | Q(home_team__id=self.id)).order_by('week')

class Player(models.Model):
	name = models.CharField(max_length=100)
	age = models.IntegerField(default=1)
	skill = models.IntegerField(default=1)
	shooting = models.IntegerField(default=1)
	stamina = models.IntegerField(default=1)
	primary_position = models.IntegerField(default=0)
	secondary_position = models.IntegerField(default=0)
	team = models.ForeignKey(Team)
	roster = models.IntegerField('starting position or bench', default=0)
	minutes = models.IntegerField(default=0)

	def __unicode__(self):
		return "{0}".format(self.name)

class Game(models.Model):
	home_team = models.ForeignKey(Team, related_name="home_game")
	away_team = models.ForeignKey(Team, related_name="away_game")
	homeScore = models.IntegerField(default=0)
	awayScore = models.IntegerField(default=0)
	week = models.IntegerField(default=0)
	season = models.IntegerField(default=0)

	def __unicode__(self):
		return "{0} vs {1} : Week {2}".format(self.away_team.name, self.home_team.name, self.week)

	def is_finished(self):
		return self.homeScore > 0 and self.awayScore > 0


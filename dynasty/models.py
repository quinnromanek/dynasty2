from django.db import models
def position_string(pos):
	arr = ["Null", "PG", "SG", "SF", "PF", "C"]
	return arr[pos]

# Create your models here.
class Team(models.Model):
	name = models.CharField(max_length=50)
	wins = models.IntegerField(default=0)
	losses = models.IntegerField(default=0)
	division = models.IntegerField(default=0)

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



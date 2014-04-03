from dynasty.models import Team, Player, Game
from django.core.management.base import BaseCommand, CommandError
from random import randrange, shuffle
from itertools import combinations
teams = [
		["Rush", "Muscle", "Gryphons", "Knights"],
		["Wolves", "Bandits", "Cobras", "Phoenix"],
		["Dragons", "Warriors", "Nova", "Diamond"],
		["Flames", "Crocs", "Zombies", "Pilgrims"]
	]
def make_teams():
	""" Cleans all teams and repopulates divisions. """
	Team.objects.all().delete()
	
	for div in [0, 1, 2, 3]:
		for tname in teams[div]:
			Team.objects.create(name=tname, division=div)
def get_div_games(division):
	weeks = []
	for i in range(len(division)-1):
		week = []
		counted = []
		for ti in range(len(division)):
			t2 = (ti+i+1) % len(division)
			if division[ti] not in counted and division[t2] not in counted:
				week.append([division[ti], division[t2]])
				counted.extend([division[ti], division[t2]])
		weeks.append(week)
	return weeks

def create_schedule(div_games=2, conf_games=1, int_games=1):
	def team_id(team_name):
		return Team.objects.get(name=team_name)

	Game.objects.all().delete()
	weeks = 3*div_games*[0] + 4*conf_games*[1] + int_games*[2]
	shuffle(weeks)
	div_game_list = get_div_games([0, 1, 2, 3]) + list(get_div_games([0, 1, 2, 3]))
	for i in range(len(div_game_list)):
		for j in range(len(div_game_list[i])):
			if i >= len(div_game_list)/2:
				print("Switching {0} {1}".format(i,j))
				div_game_list[i][j].reverse()
	print(div_game_list)
	shuffle(div_game_list)
	counts = [0, 0, 0]
	conf_game_list = range(4)*conf_games
	shuffle(conf_game_list)
	int_game_list = randrange(4)
	
	i = 0
	for game_type in weeks:

		if game_type == 0:
			# Division game
			vs = div_game_list[counts[game_type]]
			for div in range(4):
				for game in vs:
					#print(game)
					
					Game.objects.create(away_team=team_id(teams[div][game[0]]), home_team=team_id(teams[div][game[1]]), week=i, season=0)
		elif game_type == 1:
			# Conference game
			vs = conf_game_list[counts[game_type]]
			for div in [0, 2]:
				for ti in range(4):
					game = [teams[div][ti], teams[div+1][(ti+vs) % 4]]
					shuffle(game)
					Game.objects.create(away_team=team_id(game[0]), home_team=team_id(game[1]), week=i, season=0)
		else:
			# Interconf game
			vs = int_game_list
			for div in [0, 1]:
				for ti in range(4):
					game = [teams[div][ti], teams[div+2][(ti+vs) % 4]]
					Game.objects.create(away_team=team_id(game[0]), home_team=team_id(game[1]), week=i, season=0)
		counts[game_type] += 1
		
		i += 1

class Command(BaseCommand):
	help = "Cleans all teams and repopulates divisions"

	def handle(self, *args, **options):
		make_teams()
		create_schedule()
		self.stdout.write("Success.")

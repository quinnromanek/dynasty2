from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from dynasty.models import Player, Team, Game

# Create your views here.
def index(request):
	return HttpResponse("Sup bishes")

def team(request, team_name):
	currentTeam = get_object_or_404(Team, name=team_name.capitalize())
	return render(request, 'teams.html', {'team':currentTeam})

def teams(request):
	""" A list of teams """
	return HttpResponse("A list of teams")

def players(request):
	return HttpResponse("Players list page")

def games(request):
	weeks = []
	for week_num in range(11):
		weeks.append(Game.objects.filter(week=week_num))

	return render(request, 'games.html', {'weeks':weeks})
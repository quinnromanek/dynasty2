from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
	return HttpResponse("Sup bishes")

def team(request, team_name):
	return HttpResponse("Placeholder Page for team %s" % team_name)

def players(request):
	return HttpResponse("Players list page")
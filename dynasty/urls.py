from django.conf.urls import patterns, url, include
from tastypie.api import Api
from dynasty.api import *
from dynasty import views

beta_api = Api(api_name="beta")
beta_api.register(PlayerResource())
beta_api.register(TeamResource())
beta_api.register(GameResource())
beta_api.register(PlayerStatResource())

urlpatterns = patterns('',
                       url(r'^$', views.DynastyView.as_view(template_name="index.html"), name='index'),
                       url(r'^teams/(?P<team_name>\w+)', views.TeamView.as_view(), name='team'),
                       url(r'^teams/', views.TeamsView.as_view(), name='teams'),
                       url(r'^players/(?P<player_id>\d+)', views.PlayerView.as_view(), name='player'),
                       url(r'^players/', views.PlayersView.as_view(), name='players'),
                       url(r'^games/(?P<game_id>\d+)', views.GameView.as_view(), name="game"),
                       url(r'^games/', views.GamesView.as_view(), name="games"),
                       url(r'^service/', include(beta_api.urls))

)
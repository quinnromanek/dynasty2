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
                       url(r'^$', views.index, name='index'),
                       url(r'^teams/(?P<team_name>\w+)', views.team),
                       url(r'^teams/', views.teams),
                       url(r'^players/', views.players),
                       url(r'^games/(?P<game_id>\d+)', views.game),
                       url(r'^games/', views.games),
                       url(r'^service/', include(beta_api.urls))

)
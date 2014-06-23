from django.conf.urls import patterns, url

from dynasty import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^teams/(?P<team_name>\w+)', views.team),
                       url(r'^teams/', views.teams),
                       url(r'^players/', views.players),
                       url(r'^games/(?P<game_id>\d+)', views.game),
                       url(r'^games/', views.games)

)
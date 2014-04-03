from django.conf.urls import patterns, url

from dynasty import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^teams/(?P<team_name>\w+)/', views.team),
	url(r'^players/', views.players),
)
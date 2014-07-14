from tastypie.authorization import Authorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS

__author__ = 'flex109'

from tastypie.resources import ModelResource
from dynasty.models import *
from tastypie import fields


class TeamResource(ModelResource):
    class Meta:
        queryset = Team.objects.all()
        filtering = {
            "name": 'exact',
            "division": 'exact'
        }
        ordering = ['name', 'wins', 'division']

class PlayerResource(ModelResource):
    team = fields.ForeignKey(TeamResource, 'team')

    class Meta:
        queryset = Player.objects.all()
        filtering = {
            'team':ALL_WITH_RELATIONS
        }
        ordering = ['name', 'age', 'defense',
                    'offense', 'athletics', 'primary_position',
                    'secondary_position', 'team', 'roster',
                    'minutes']
        authorization = Authorization()


class GameResource(ModelResource):

    away_team = fields.ForeignKey(TeamResource, 'away_team')
    home_team = fields.ForeignKey(TeamResource, 'home_team')

    class Meta:
        queryset = Game.objects.all()


class PlayerStatResource(ModelResource):
    player = fields.ForeignKey(PlayerResource, 'player')
    game = fields.ForeignKey(GameResource, 'game')
    team = fields.ForeignKey(TeamResource, 'team')

    class Meta:
        queryset = PlayerStats.objects.all()



from django.db import models
from dynasty.models import Team
from dynasty.templatetags.dynasty_interface import position_short

__author__ = 'flex109'

class Player(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField(default=1)
    defense = models.IntegerField(default=1)
    offense = models.IntegerField(default=1)
    athletics = models.IntegerField(default=1)
    primary_position = models.IntegerField(default=0)
    secondary_position = models.IntegerField(default=0)
    team = models.ForeignKey('dynasty.team')
    roster = models.IntegerField('starting position or bench', default=0)
    minutes = models.IntegerField(default=0)

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_player"

    def __unicode__(self):
        return "{0} {1}".format(self.name, position_short(self.primary_position) if self.secondary_position == 0 else
            position_short(self.primary_position) + "|" + position_short(self.secondary_position))

    def get_shot(self, defender, quarter, time_left):
        pass

    def has_position(self, pos):
        return pos == self.primary_position or pos == self.secondary_position

    def min_at_pos(self, pos):
        if pos == self.primary_position:
            return self.get_primary_minutes()
        elif pos == self.secondary_position:
            return self.get_secondary_minutes()
        else:
            return 0

    def shot_tendency(self):
        return 0.5

    def get_primary_minutes(self):
        return self.minutes / 25

    def get_secondary_minutes(self):
        return self.minutes % 25

    def set_primary_minutes(self, mins):
        self.minutes = mins * 25 + self.get_secondary_minutes()
        self.save()

    def set_secondary_minutes(self, mins):
        self.minutes = mins + self.get_primary_minutes() * 25
        self.save()

    def get_all_minutes(self):
        return self.get_primary_minutes() + self.get_secondary_minutes()

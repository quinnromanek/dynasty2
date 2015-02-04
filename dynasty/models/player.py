from django.db import models
from django.db.models import Avg
from dynasty.models import Team
from dynasty.templatetags.dynasty_interface import position_short
from math import log10, ceil, pow
from dynasty.utils import get_binomial_result

__author__ = 'flex109'


def constant_improvement(year, peak, amplitude):
    return int(round(float(amplitude) * (year / peak)))


def early_improvement(year, peak, amplitude):
    return int(round(float(amplitude) * log10((10.0 / peak) * year + 1)))


def late_improvement(year, peak, amplitude):
    return int(round(float(amplitude) / 57.0 * pow(1.5, (10.0 / peak) * year)))

def get_improve_func(type):
    if type == 0:
        improve_func = constant_improvement
    elif type == 1:
        improve_func = early_improvement
    elif type == 2:
        improve_func = late_improvement
    else:
        return lambda a, b, c: 0
    return improve_func

def improvement(type, year, peak, amplitude):
    improve_func = get_improve_func(type)

    return improve_func(year, peak, amplitude) - improve_func(year - 1, peak, amplitude)

def decline(type, year, peak, amplitude):
    decline_func = get_improve_func(type)
    year = year - peak
    assert year > 0
    return decline_func(5 - year, 5, amplitude) - decline_func(6 - year, 5, amplitude)


def pack_values(vals, base):
    encoding = 0
    for power in xrange(len(vals)):
        encoding += base**power*vals[power]
    return encoding

def unpack_values(encoding, total, base):
    values = [0]*total
    for power in xrange(total):
        values[power] = encoding % base
        encoding /= base

    return values


class Player(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField(default=1)

    # Attributes
    defense = models.IntegerField(default=1)
    offense = models.IntegerField(default=1)
    athletics = models.IntegerField(default=1)
    stamina = models.IntegerField(default=1)

    # In-game information
    primary_position = models.IntegerField(default=0)
    secondary_position = models.IntegerField(default=0)
    team = models.ForeignKey('dynasty.team', null=True)
    roster = models.IntegerField('starting position or bench', default=0)
    minutes = models.IntegerField(default=0)
    number = models.IntegerField(default=0)

    # Internal stats
    fatigue = models.IntegerField(default=0.0)

    tendency = models.FloatField(default=0.0)
    improvement_curves = models.IntegerField(default=0)
    improvement_amplitudes = models.IntegerField(default=0)
    prime_year = models.IntegerField(default=10)

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_player"

    def __unicode__(self):
        return "{0} {1}".format(self.name, position_short(self.primary_position) if self.secondary_position == 0 else
        position_short(self.primary_position) + "|" + position_short(self.secondary_position))

    def get_shot(self, defender, quarter, time_left):
        pass

    def rating(self):
        return self.offense + self.defense + self.athletics

    def scout(self):
        amplitudes = unpack_values(self.improvement_amplitudes, 8, 11)
        max_rating = self.offense + amplitudes[0] + self.defense + amplitudes[1] + self.athletics + amplitudes[2]
        max_rating_adj = max_rating + get_binomial_result(-5, 5, 0.5)
        if max_rating_adj < 3:
            return 3
        elif max_rating_adj > 30:
            return 30
        else:
            return max_rating_adj

    def has_position(self, pos):
        return pos == self.primary_position or pos == self.secondary_position

    def min_at_pos(self, pos):
        if pos == self.primary_position:
            return self.get_primary_minutes()
        elif pos == self.secondary_position:
            return self.get_secondary_minutes()
        else:
            return 0

    def set_min_at_pos(self, pos, min):
        if pos == self.primary_position:
            self.set_primary_minutes(min)
        elif pos == self.secondary_position:
            self.set_secondary_minutes(min)

    def shot_tendency(self, position):
        # # The chance to shoot is 25% plus shot_tendency/2
        tendency = 0.5
        if position == 1:
            tendency = 0.0
        elif position == 2:
            tendency = 0.6
        elif position == 3:
            tendency = 0.55
        elif position == 4:
            tendency = 0.4
        elif position == 5:
            tendency = 0.45

        return max(-0.2, tendency + self.tendency)

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

    def ppg_season(self):
        fgpg = self.playerstats_set.all().aggregate(Avg('field_goals'))['field_goals__avg']

        if fgpg is None:
            return 0.0
        return fgpg * 2

    def rpg_season(self):
        rpg = self.playerstats_set.all().aggregate(Avg('rebounds'))['rebounds__avg']
        if rpg is None:
            return 0.0
        return rpg

    def spg_season(self):
        spg = self.playerstats_set.all().aggregate(Avg('steals'))['steals__avg']
        if spg is None:
            return 0.0
        return spg

    def apg_season(self):
        spg = self.playerstats_set.all().aggregate(Avg('assists'))['assists__avg']
        if spg is None:
            return 0.0
        return spg

    def max_minutes(self):
        return int(ceil(12.0 + 7.0 * ((self.stamina - 1.0) / 9.0)))

    def grow_year(self):
        curves = unpack_values(self.improvement_curves, 8, 3)
        amplitudes = unpack_values(self.improvement_amplitudes, 8, 11)

        if self.age <= self.prime_year:
            self.offense += improvement(curves[0], self.age, self.prime_year, amplitudes[0])
            self.defense += improvement(curves[2], self.age, self.prime_year, amplitudes[2])
            self.athletics += improvement(curves[4], self.age, self.prime_year, amplitudes[4])
            self.stamina += improvement(curves[6], self.age, self.prime_year, amplitudes[6])
        elif self.age <= self.prime_year + 5:
            self.offense += decline(curves[1], self.age, self.prime_year, amplitudes[1])
            self.defense += decline(curves[3], self.age, self.prime_year, amplitudes[3])
            self.athletics += decline(curves[5], self.age, self.prime_year, amplitudes[5])
            self.stamina += decline(curves[7], self.age, self.prime_year, amplitudes[7])
        else:
            pass

        self.age += 1
        self.save()

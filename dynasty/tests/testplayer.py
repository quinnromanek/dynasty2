from django.test import TestCase
from dynasty.league import create_random_player
from dynasty.models import Team
from dynasty.models.player import unpack_values, constant_improvement, early_improvement, late_improvement

__author__ = 'flex109'

class PlayerTest(TestCase):

    def setUp(self):
        self.ballers = Team.objects.create(name="Ballers")
        self.ringers = Team.objects.create(name="Ringers")

    def test_improvement_curves(self):
        for peak in range(5, 15):
           for amplitude in range(0, 10):
               for year in range(peak):
                   self.assertLessEqual(constant_improvement(year, peak, amplitude), amplitude, "constant exceeded at {0} {1} {2}".format(year, peak, amplitude))
                   self.assertLessEqual(early_improvement(year, peak, amplitude), amplitude, "early exceeded at {0} {1} {2}".format(year, peak, amplitude))
                   self.assertLessEqual(late_improvement(year, peak, amplitude), amplitude, "late exceeded at {0} {1} {2}".format(year, peak, amplitude))

    def test_player_growth(self):

        def print_player(year, player):
            print("{0}:\tO:{1}\tD:{2}\tA:{3}\tS:{4}".format(year, player.offense, player.defense, player.athletics, player.stamina))
        player = create_random_player(self.ballers)

        curves = unpack_values(player.improvement_curves, 8, 3)
        amplitudes = unpack_values(player.improvement_amplitudes, 8, 11)

        print(amplitudes)
        print_player(0, player)
        for year in range(1, player.prime_year + 6):
            player.grow_year()
            print_player(year, player)


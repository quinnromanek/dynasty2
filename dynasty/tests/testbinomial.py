__author__ = 'flex109'

from django.test import TestCase
from dynasty.utils import *


class BinomialTest(TestCase):

    def test_binomial_probability(self):
        self.assertAlmostEqual(binomial_probability(2, 0.5, 1), 0.5, places=3)
        self.assertAlmostEqual(binomial_probability(2, 0.5, 0), 0.25, places=3)
        self.assertAlmostEqual(binomial_probability(2, 0.5, 2), 0.25, places=3)
        self.assertAlmostEqual(binomial_probability(5, 0.1, 2), 0.073, places=3)

    def test_binomial_result(self):
        catch = [0, 0, 0, 0, 0]
        for i in range(1000):
            result = get_binomial_result(0, 4, 0.5)
            catch[result] += 1

        self.assertAlmostEqual(binomial_probability(4, 0.5, 2), float(catch[2])/1000.0, delta=0.1)
        self.assertAlmostEqual(binomial_probability(4, 0.5, 1), float(catch[1])/1000.0, delta=0.1)
        self.assertAlmostEqual(binomial_probability(4, 0.5, 4), float(catch[4])/1000.0, delta=0.1)

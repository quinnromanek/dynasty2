from django.test import TestCase
from dynasty.models.player import pack_values, unpack_values

__author__ = 'flex109'

class EncodingTest(TestCase):
    def test_encoding_stability(self):
        encoding = pack_values([5, 4, 2, 3, 0], 6)
        decoding = unpack_values(encoding, 5, 6)
        self.assertEqual(2, decoding[2], "Unpacked values not stable")



__author__ = 'Quinn Romanek'

from django.test import TestCase

from dynasty.models import Team, Player, Game
from dynasty.management.commands.teams_init import create_random_player, generate_team

class GameTestCase(TestCase):

    def setUp(self):
        self.ballers = Team.objects.create(name="Ballers")
        self.ringers = Team.objects.create(name="Ringers")



    def test_average_score(self):
        total = 0.0
        wins = []
        losses = []
        for trial in range(100):
            Player.objects.all().delete()
            generate_team(self.ballers)
            generate_team(self.ringers)
            game = Game.objects.create(away_team=self.ballers, home_team=self.ringers)
            game.play()
            if game.homeScore == game.awayScore:
                self.fail("Game ended in tie")
            elif game.homeScore > game.awayScore:
                wins.append(game.homeScore)
                losses.append(game.awayScore)
            else:
                losses.append(game.homeScore)
                wins.append(game.awayScore)

            total += float(game.homeScore)
            total += float(game.awayScore)
        self.assertEqual(len(wins), len(losses), "Uneven amount of wins and losses")

        print("Average score after 200 trials: {0}\nAverage Win: {1} Average Loss: {2}".format(total/200.0, sum(wins)/len(wins), sum(losses)/len(losses)))

    def test_better_team_wins(self):
        Player.objects.all().delete()
        for pos in range(1, 6):
            Player.objects.create(defense=10, offense=10, athletics=10, primary_position=pos, roster=pos, team=self.ringers)
            Player.objects.create(defense=9, offense=9, athletics=9, primary_position=pos, roster=pos, team=self.ballers)

        times = 0
        for trial in range(100):
            game = Game.objects.create(home_team=self.ringers, away_team=self.ballers)
            game.play()
            if game.homeScore > game.awayScore:
                times += 1.0

        print("Win Pct on better team: {0}".format(times/100.0))
        self.assertGreater(times/100.0, 0.8, "Win Pct not high enough: {0}".format(times/100.0))


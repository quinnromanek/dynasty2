from dynasty.league import create_random_player
from dynasty.templatetags.dynasty_interface import position_short

__author__ = 'Quinn Romanek'

from django.test import TestCase
from django.db.models import Sum, Q
from dynasty.models import Team, Player, Game, PlayerStats
from dynasty.management.commands.teams_init import generate_team

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
            p1 = Player.objects.create(defense=10, offense=10, athletics=10, primary_position=pos, roster=pos, team=self.ringers)
            p1.set_primary_minutes(24)
            p2 = Player.objects.create(defense=5, offense=5, athletics=5, primary_position=pos, roster=pos, team=self.ballers)
            p2.set_primary_minutes(24)

        times = 0
        for trial in range(100):
            game = Game.objects.create(home_team=self.ringers, away_team=self.ballers)
            game.play()
            if game.homeScore > game.awayScore:
                times += 1.0

        print("Win Pct on better team: {0}".format(times/100.0))
        self.assertGreater(times/100.0, 0.8, "Win Pct not high enough: {0}".format(times/100.0))


    def test_stats_kept(self):
        Player.objects.all().delete()
        PlayerStats.objects.all().delete()
        generate_team(self.ballers)
        generate_team(self.ringers)

        game = Game.objects.create(away_team=self.ringers, home_team=self.ballers)
        game.play()

        stats = PlayerStats.objects.filter(game=game).filter(team=self.ringers)

        total_points = stats.aggregate(points=Sum('field_goals'))['points']

        self.assertEqual(total_points*2, game.awayScore)

    def test_pass_balancing(self):
        Player.objects.all().delete()
        Game.objects.all().delete()
        PlayerStats.objects.all().delete()
        for pos in range(1, 6):
            p1 = Player.objects.create(defense=5, offense=5, athletics=5, primary_position=pos, roster=pos, team=self.ringers)
            p1.set_primary_minutes(24)
            p2 = Player.objects.create(defense=5, offense=5, athletics=5, primary_position=pos, roster=pos, team=self.ballers)
            p2.set_primary_minutes(24)
        shot_attempts = [0, 0, 0, 0, 0]
        for trial in range(100):
            game = Game.objects.create(home_team=self.ringers, away_team=self.ballers)
            game.play()
            for pos in range(1, 6):
                shot_attempts[pos - 1] += PlayerStats.objects.get(Q(game=game) & Q(team=self.ringers) & Q(player__roster=pos)).field_goals_attempted
                shot_attempts[pos - 1] += PlayerStats.objects.get(Q(game=game) & Q(team=self.ballers) & Q(player__roster=pos)).field_goals_attempted

        for pos in range(len(shot_attempts)):
            print("{0}: {1}".format(position_short(pos + 1), shot_attempts[pos]))




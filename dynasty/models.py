from random import randrange, random
from django.db import models
from django.db.models import Q


def position_string(pos):
    arr = ["Null", "PG", "SG", "SF", "PF", "C"]
    return arr[pos]


class Season(models.Model):
    week = models.IntegerField(default=0)
    year = models.IntegerField(default=0)
    name = models.CharField(max_length=50)


class Team(models.Model):
    name = models.CharField(max_length=50)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    division = models.IntegerField(default=0)

    def __unicode__(self):
        return "{0} ({1}-{2})".format(self.name, self.wins, self.losses)

    def win_pct(self):
        try:
            return float(self.wins) / (float(self.wins + self.losses))
        except ZeroDivisionError:
            return 0

    def starters(self):
        """ Should only be called after validating roster. """
        s = []
        for pos in range(1, 6):
            s.append(self.player_set.get(roster=pos))
        return s

    def bench(self):
        b = self.player_set.filter(roster=0)
        return b


    def season_games(self):
        return Game.objects.filter(Q(away_team__id=self.id) | Q(home_team__id=self.id)).order_by('week')


class Player(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField(default=1)
    defense = models.IntegerField(default=1)
    offense = models.IntegerField(default=1)
    athletics = models.IntegerField(default=1)
    primary_position = models.IntegerField(default=0)
    secondary_position = models.IntegerField(default=0)
    team = models.ForeignKey(Team)
    roster = models.IntegerField('starting position or bench', default=0)
    minutes = models.IntegerField(default=0)

    def __unicode__(self):
        return "{0}".format(self.name)

    def get_shot(self, defender, quarter, time_left):
        pass

    def shot_tendency(self):
        return 0.5



class Game(models.Model):
    home_team = models.ForeignKey(Team, related_name="home_game")
    away_team = models.ForeignKey(Team, related_name="away_game")
    homeScore = models.IntegerField(default=0)
    awayScore = models.IntegerField(default=0)
    week = models.IntegerField(default=0)
    season = models.IntegerField(default=0)

    def __unicode__(self):
        return "{0} vs {1} : Week {2}".format(self.away_team.name, self.home_team.name, self.week)

    def is_finished(self):
        return self.homeScore > 0 and self.awayScore > 0

    def play(self):
        # For game positions are zero-indexed

        home_players = self.home_team.starters()
        away_players = self.away_team.starters()

        home_stats = []
        away_stats = []
        for i in range(5):
            home_stats.append([0, 0, 0, 0])
            away_stats.append([0, 0, 0, 0])
        roll = 3.0
        quarter_length = 600.0
        clock = quarter_length
        quarter = 1

        def log_stat(type, poss, player):
            if poss is home_players:
                stats = home_stats
            else:
                stats = away_stats

            if type == "score":
                stats[player][0] += 1
                stats[player][1] += 1
            elif type == "miss":
                stats[player][1] += 1
            elif type == "rebound":
                stats[player][2] += 1
            elif type == "steal":
                stats[player][3] += 1

        def avg(a, b):
            return float(a + b) / 2.0

        # Returns steal chance from [0,1]
        def steal(off_player_off, def_player_def):
            a = (float(def_player_def) - float(off_player_off) + 10.0) / 20.0
            return a

        def shot(off_player_off, def_player_def):
            return 1 - steal(off_player_off, def_player_def)

        # Returns the team that doesn't have possession.
        def switch_team(poss):
            if poss is home_players:
                return away_players
            elif poss is away_players:
                return home_players

        def score(poss):
            if poss is home_players:
                self.homeScore += 2
            else:
                self.awayScore += 2

        # Returns the team based on tipoff percentage

        def get_tipoff():
            p_home_tipoff = 0.25 + (0.5) * (
                (home_players[4].athletics) / (home_players[4].athletics + away_players[4].athletics))

            if random() > p_home_tipoff:
                return away_players
            else:
                return home_players

        def do_roll(clock, quarter):
            end = False
            if clock - roll < 0.0:
                clock = quarter_length
                quarter += 1
            if quarter > 4 and self.homeScore != self.awayScore:
                end = True
            return clock - roll, quarter, end

        player_poss = 0
        team_poss = get_tipoff()
        clock -= roll

        while True:
            p_steal = 0.05 * steal(team_poss[player_poss].offense, switch_team(team_poss)[player_poss].defense)
            p_shot = (0.25 + 0.5 * (team_poss[player_poss].shot_tendency())) * (1.0 - p_steal)
            p_pass = 1 - p_shot - p_steal

            main_roll = random()

            clock, quarter, end = do_roll(clock, quarter)
            if end:
                break

            if main_roll > p_shot + p_pass:
                # Steal
                team_poss = switch_team(team_poss)
                log_stat("steal", team_poss, player_poss)
            elif main_roll > p_shot:
                # Pass
                target = (player_poss + randrange(3) + 1) % 5

                if random() <= 0.05 * (steal(avg(team_poss[player_poss].offense, team_poss[target].offense),
                                             avg(switch_team(team_poss)[player_poss].defense,
                                                 switch_team(team_poss)[target].defense))):
                    team_poss = switch_team(team_poss)
                    log_stat("steal", team_poss, player_poss)

                clock, quarter, end = do_roll(clock, quarter)
                if end:
                    break

                player_poss = target

            else:
                # Shot
                if random() > 0.35 + 0.35 * shot(team_poss[player_poss].offense, switch_team(team_poss)[player_poss].defense):
                    # Rebound
                    # Placeholder for rebounding logic
                    log_stat("miss", team_poss, player_poss)
                    if random() > 0.75:
                        team_poss = switch_team(team_poss)
                        player_poss = 0
                    else:
                        player_poss = 3 if random() > 0.6 else 4


                    clock, quarter, end = do_roll(clock, quarter)
                    if end:
                        break
                else:
                    score(team_poss)
                    log_stat("score", team_poss, player_poss)
                    team_poss = switch_team(team_poss)
                    player_poss = 0


                clock, quarter, end = do_roll(clock, quarter)
                if end:
                    break

        for i in range(len(home_players)):
            log_game(home_players[i], self, self.home_team, home_stats[i])

        for i in range(len(away_players)):
            log_game(away_players[i], self, self.away_team, away_stats[i])

        if self.homeScore > self.awayScore:
            self.home_team.wins += 1
        else:
            self.away_team.wins += 1
        self.save()



class PlayerStats(models.Model):
    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)
    roster = models.IntegerField(default=0)
    team = models.ForeignKey(Team)
    field_goals = models.IntegerField(default=0)

    field_goals_attempted = models.IntegerField(default=0)
    rebounds = models.IntegerField(default=0)
    steals = models.IntegerField(default=0)

    def fg_pct(self):
        if self.field_goals_attempted > 0:
            return float(self.field_goals)/float(self.field_goals_attempted)
        else:
            return 0.0

    def points(self):
        return 2*self.field_goals

    def __unicode__(self):
        return "{0} %: {1} Stl: {2} Pts: {3}".format(self.player.name, self.fg_pct(), self.steals, self.points())


def log_game(player, game, team, data):
    obj = PlayerStats.objects.create(player=player, game=game, roster=player.roster, team=team,
                               field_goals=data[0], field_goals_attempted=data[1], rebounds=data[2], steals=data[3])


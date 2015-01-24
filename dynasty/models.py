from random import randrange, random
from django.db import models
from math import ceil
from django.db.models import Q
from templatetags.dynasty_interface import position_short


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
        b = list(self.player_set.filter(roster=0))
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


class GameTeam:
    """ Auxilary class for keeping track of in-game data.
    """

    def __init__(self, team, game):
        self.team = team
        self.game = game
        self.on_court = range(5)
        self.full_team = self.team.starters() + self.team.bench()
        self.stats = [[0, 0, 0, 0] for i in xrange(len(self.full_team))]
        self.rotation = self.find_rotation()

    def __repr__(self):
        return self.team.name

    def __getitem__(self, item):
        return self.full_team[self.on_court[item]]

    def find_rotation(self):

        def check_rotation(rotation, time, time_played):
            time = min([sum([stint[1] for stint in pos]) for pos in rotation])
            if time == 24:
                return rotation
            # Check for lineup hash here
            for position in range(5):
                if time == sum([stint[1] for stint in rotation[position]]):
                    # Then it's time to sub!
                    new_time_played = time_played[:]
                    current_player_index, current_stint = rotation[position][len(rotation[position]) - 1]
                    current_player = self.full_team[current_player_index]
                    cpi = current_player_index
                    tp, ts = time_played[cpi]
                    new_time_played[cpi] = (
                        (tp + current_stint), ts) if current_player.primary_position - 1 == position else \
                        (tp, (ts + current_stint))
                    players_in = [pos[-1][0] for pos in rotation]

                    result = None
                    for player_index in xrange(len(self.full_team)):
                        player = self.full_team[player_index]
                        if player_index in players_in and sum(
                                [stint[1] for stint in rotation[players_in.index(player_index)][:-1]]) == time:
                            continue

                        if player.has_position(position + 1) and new_time_played[player_index][
                            0 if player.primary_position - 1 == position else 1] < player.min_at_pos(position + 1):
                            new_rotation = rotation[:]
                            new_rotation[position] = new_rotation[position] + (
                                (player_index, player.min_at_pos(position + 1) - new_time_played[player_index][
                                    0 if player.primary_position - 1 == position else 1
                                ]),)

                            if player_index in players_in and sum(
                                    [stint[1] for stint in rotation[players_in.index(player_index)]]) > time:
                                player_pos = players_in.index(player_index)
                                time_diff = time - sum(stint[1] for stint in rotation[player_pos][:-1])
                                new_rotation[player_pos] = new_rotation[player_pos][:-1] + ((player_index, time_diff),)
                                tp, ts = new_time_played[player_index]
                                new_time_played[player_index] = (
                                    (tp + time_diff), ts) if player.primary_position - 1 == player_pos \
                                    else (tp, (ts + time_diff))

                            check = check_rotation(new_rotation, time, new_time_played)
                            if check is not None:
                                result = check

                    return result


        rotation = []

        for i in range(5):
            rotation.append(((i, self.full_team[i].min_at_pos(i + 1) / 2),))

        time_played = [(0, 0) for i in xrange(len(self.full_team))]

        return check_rotation(rotation, 0, time_played)


    def log_stat(self, type, player):
        # Stats are [fg, fga, reb, stl]
        player = self.on_court[player]
        if type == "score":
            self.stats[player][0] += 1
            self.stats[player][1] += 1
        elif type == "miss":
            self.stats[player][1] += 1
        elif type == "rebound":
            self.stats[player][2] += 1
        elif type == "steal":
            self.stats[player][3] += 1

    def check_subs(self):
        minutes = self.game.minutes()
        for i in range(5):
            time = minutes
            p_rot = 0
            while p_rot < len(self.rotation[i]):
                if time == 0:
                    self.on_court[i] = self.rotation[i][p_rot][0]
                    break
                elif time < 0:
                    break
                else:
                    time -= self.rotation[i][p_rot][1]
                    p_rot += 1


    def save_stats(self):
        for i in range(len(self.full_team)):
            if self.full_team[i].get_all_minutes() > 0:
                log_game(self.full_team[i], self.game, self.team, self.stats[i])


class Game(models.Model):
    home_team = models.ForeignKey(Team, related_name="home_game")
    away_team = models.ForeignKey(Team, related_name="away_game")
    homeScore = models.IntegerField(default=0)
    awayScore = models.IntegerField(default=0)
    week = models.IntegerField(default=0)
    season = models.IntegerField(default=0)

    def __unicode__(self):
        return "{0} vs {1} : Week {2}".format(self.away_team.name, self.home_team.name, self.week)

    def minutes(self):
        return 6 - ceil(self.clock / 100.0) + 6 * (self.quarter - 1)

    def is_finished(self):
        return self.homeScore > 0 and self.awayScore > 0

    def play(self):
        # For game positions are zero-indexed
        home_team = GameTeam(self.home_team, self)
        away_team = GameTeam(self.away_team, self)

        roll = 3.0
        quarter_length = 600.0
        self.minute = 0
        self.clock = quarter_length
        self.quarter = 1

        def log_stat(type, poss, player):
            if poss is home_team:
                home_team.log_stat(type, player)
            else:
                away_team.log_stat(type, player)


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
            if poss is home_team:
                return away_team
            elif poss is away_team:
                return home_team

        def score(poss):
            if poss is home_team:
                self.homeScore += 2
            else:
                self.awayScore += 2

        # Returns the team based on tipoff percentage

        def get_tipoff():
            p_home_tipoff = 0.25 + (0.5) * (
                home_team[4].athletics / (home_team[4].athletics + away_team[4].athletics))

            if random() > p_home_tipoff:
                return away_team
            else:
                return home_team

        def do_roll():
            end = False
            if self.clock - roll < 0.0:
                self.clock = quarter_length
                self.quarter += 1
                print("End of quarter {0}".format(self.quarter - 1))
            if self.quarter > 4 and self.homeScore != self.awayScore:
                end = True
            if self.minutes() > self.minute and not end:
                self.minute = self.minutes()
                home_team.check_subs()
                away_team.check_subs()
            self.clock -= roll
            return end

        player_poss = 0
        team_poss = get_tipoff()
        self.clock -= roll
        print("Game: {0} vs {1}".format(self.home_team.name, self.away_team.name))
        while True:
            p_steal = 0.05 * steal(team_poss[player_poss].offense,
                                   switch_team(team_poss)[player_poss].defense)
            p_shot = (0.25 + 0.5 * (team_poss[player_poss].shot_tendency())) * (1.0 - p_steal)
            p_pass = 1 - p_shot - p_steal

            main_roll = random()

            end = do_roll()
            if end:
                break

            if main_roll > p_shot + p_pass:
                # Steal
                team_poss = switch_team(team_poss)
                log_stat("steal", team_poss, player_poss)
            elif main_roll > p_shot:
                # Pass
                target = (player_poss + randrange(3) + 1) % 5

                if random() <= 0.05 * (
                        steal(avg(team_poss[player_poss].offense, team_poss[target].offense),
                              avg(switch_team(team_poss)[player_poss].defense,
                                  switch_team(team_poss)[target].defense))):
                    team_poss = switch_team(team_poss)
                    log_stat("steal", team_poss, player_poss)

                end = do_roll()
                if end:
                    break

                player_poss = target

            else:
                # Shot
                if random() > 0.35 + 0.35 * shot(team_poss[player_poss].offense,
                                                 switch_team(team_poss)[player_poss].defense):
                    # Rebound
                    # Placeholder for rebounding logic
                    log_stat("miss", team_poss, player_poss)
                    if random() > 0.75:
                        team_poss = switch_team(team_poss)
                        player_poss = 0
                        log_stat("rebound", team_poss, player_poss)
                    else:
                        player_poss = 3 if random() > 0.6 else 4
                        log_stat("rebound", team_poss, player_poss)

                    end = do_roll()
                    if end:
                        break
                else:
                    score(team_poss)
                    log_stat("score", team_poss, player_poss)
                    team_poss = switch_team(team_poss)
                    player_poss = 0

                end = do_roll()
                if end:
                    break

        home_team.save_stats()
        away_team.save_stats()

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
    minutes = models.IntegerField(default=0)
    field_goals_attempted = models.IntegerField(default=0)
    rebounds = models.IntegerField(default=0)
    steals = models.IntegerField(default=0)

    def fg_pct(self):
        if self.field_goals_attempted > 0:
            return float(self.field_goals) / float(self.field_goals_attempted)
        else:
            return 0.0

    def points(self):
        return 2 * self.field_goals

    def __unicode__(self):
        return "{0} %: {1} Stl: {2} Pts: {3}".format(self.player.name, self.fg_pct(), self.steals, self.points())


def log_game(player, game, team, data):
    obj = PlayerStats.objects.create(player=player, game=game, roster=player.roster, team=team,
                                     field_goals=data[0], field_goals_attempted=data[1], rebounds=data[2],
                                     steals=data[3], minutes=player.get_all_minutes())


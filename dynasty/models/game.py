from math import ceil
from random import random, randrange, choice
from django.db.models import Q
from django.db import models
from dynasty.models.player import Player
from dynasty.models.team import Team, find_rotation

__author__ = 'flex109'


class GameTeam:
    """ Auxilary class for keeping track of in-game data.
    """

    def __init__(self, team, game):
        self.team = team
        self.game = game
        self.on_court = range(5)
        self.full_team = self.team.starters() + self.team.bench()
        self.stats = [[0, 0, 0, 0, 0] for i in xrange(len(self.full_team))]
        self.rotation = self.find_rotation()

    def __repr__(self):
        return self.team.name

    def __getitem__(self, item):
        return self.full_team[self.on_court[item]]

    def find_rotation(self):
        return find_rotation(self.team)


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
        elif type == "assist":
            self.stats[player][4] += 1

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
    home_team = models.ForeignKey('dynasty.team', related_name="home_game")
    away_team = models.ForeignKey('dynasty.team', related_name="away_game")
    homeScore = models.IntegerField(default=0)
    awayScore = models.IntegerField(default=0)
    week = models.IntegerField(default=0)
    season = models.IntegerField(default=0)
    series = models.ForeignKey('dynasty.series', default=None, null=True)

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_game"

    def __unicode__(self):
        return "{0} vs {1} : Week {2}".format(self.away_team.name, self.home_team.name, self.week)

    def minutes(self):
        return 6 - ceil(self.clock / 100.0) + 6 * (self.quarter - 1)

    def is_finished(self):
        return self.homeScore > 0 and self.awayScore > 0

    def winner(self):
        if self.homeScore > self.awayScore:
            return self.home_team
        elif self.awayScore > self.homeScore:
            return self.away_team
        else:
            return None

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

        def do_roll(sub=False):
            end = False
            if self.clock - roll < 0.0:
                self.clock = quarter_length
                self.quarter += 1
            if self.quarter > 4 and self.homeScore != self.awayScore:
                end = True
            if self.minutes() > self.minute and not end and sub:
                self.minute = self.minutes()
                home_team.check_subs()
                away_team.check_subs()
            self.clock -= roll
            return end

        player_poss = 0
        assist_boost = 0.0
        assist_player = -1
        team_poss = get_tipoff()
        self.clock -= roll
        while True:
            p_steal = 0.05 * steal(team_poss[player_poss].offense,
                                   switch_team(team_poss)[player_poss].defense)
            p_shot = (0.25 + 0.5 * (team_poss[player_poss].shot_tendency(player_poss + 1))) * (1.0 - p_steal)
            p_pass = 1 - p_shot - p_steal

            main_roll = random()

            end = do_roll()
            if end:
                break

            if main_roll > p_shot + p_pass:
                # Steal
                team_poss = switch_team(team_poss)
                assist_boost = 0.0
                log_stat("steal", team_poss, player_poss)
            elif main_roll > p_shot:
                # Pass
                target = (player_poss + randrange(4) + 1) % 5

                if random() <= 0.05 * (
                        steal(avg(team_poss[player_poss].offense, team_poss[target].offense),
                              avg(switch_team(team_poss)[player_poss].defense,
                                  switch_team(team_poss)[target].defense))):
                    # Steal on pass
                    team_poss = switch_team(team_poss)
                    assist_boost = 0.0
                    log_stat("steal", team_poss, player_poss)
                elif random() <= team_poss[player_poss].offense/10.0:
                    # Assist active
                    assist_boost = team_poss[player_poss].offense/100.0
                    assist_player = player_poss

                end = do_roll()
                if end:
                    break

                player_poss = target

            else:
                # Shot
                fatigue_factor = (max(0.0, float(team_poss[player_poss].fatigue)) - max(0.0, float(switch_team(team_poss)[player_poss].fatigue)))/500.0
                if random() > 0.2 - fatigue_factor + assist_boost \
                                + 0.6 * shot(team_poss[player_poss].offense,
                                                 switch_team(team_poss)[player_poss].defense):
                    # Rebound
                    # Placeholder for rebounding logic
                    log_stat("miss", team_poss, player_poss)
                    reb_choices = []
                    for team in range(2):
                        team_data = team_poss if team == 0 else switch_team(team_poss)
                        for pos in range(5):
                            number = team*5 + pos
                            if number == player_poss:
                                reb_choices += [number]
                            elif pos in [0, 1]:
                                reb_choices += [number]*(team_data[pos].athletics)
                            elif pos == 2:
                                reb_choices += [number]*(team_data[pos].athletics*2)
                            else:
                                reb_choices += [number]*(team_data[pos].athletics*3)

                    winner = choice(reb_choices)
                    if winner > 4:
                        team_poss = switch_team(team_poss)
                        winner -= 5
                    player_poss = winner
                    log_stat("rebound", team_poss, player_poss)

                    end = do_roll(sub=True)
                    if end:
                        break
                else:
                    score(team_poss)
                    if assist_boost > 0.0:
                        log_stat("assist", team_poss, assist_player)
                    log_stat("score", team_poss, player_poss)
                    team_poss = switch_team(team_poss)
                    player_poss = 0

                # Either way, no more assists.
                assist_boost = 0.0
                end = do_roll(sub=True)
                if end:
                    break

        home_team.save_stats()
        away_team.save_stats()
        if self.series is not None:
            self.series.game_finished(self)


        self.save()


class PlayerStats(models.Model):
    player = models.ForeignKey('dynasty.player')
    game = models.ForeignKey(Game)
    roster = models.IntegerField(default=0)
    team = models.ForeignKey(Team)
    field_goals = models.IntegerField(default=0)
    minutes = models.IntegerField(default=0)
    field_goals_attempted = models.IntegerField(default=0)
    rebounds = models.IntegerField(default=0)
    steals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)

    def fg_pct(self):
        if self.field_goals_attempted > 0:
            return float(self.field_goals) / float(self.field_goals_attempted)
        else:
            return 0.0

    def points(self):
        return 2 * self.field_goals

    def opponent(self):
        if self.team.id == self.game.away_team.id:
            return self.game.home_team
        else:
            return self.game.away_team

    def __unicode__(self):
        return "{0} %: {1} Stl: {2} Pts: {3}".format(self.player.name, self.fg_pct(), self.steals, self.points())

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_playerstats"


def log_game(player, game, team, data):
    player.fatigue += player.get_all_minutes() - player.max_minutes()
    if player.fatigue < -5:
        player.fatigue = -5
    if player.fatigue > 50:
        player.fatigue = 50
    player.save()
    obj = PlayerStats.objects.create(player=player, game=game, roster=player.roster, team=team,
                                     field_goals=data[0], field_goals_attempted=data[1], rebounds=data[2],
                                     steals=data[3], minutes=player.get_all_minutes(), assists=data[4])

def regular_season_games(team):
    return Game.objects.filter(Q(away_team__id=team.id) | Q(home_team__id=team.id), week__gte=0).order_by('week')

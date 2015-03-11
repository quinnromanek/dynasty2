from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Sum, F
import operator
from dynasty.constants import GAME_LENGTH
from dynasty.models.other import current_season
from dynasty.templatetags.dynasty_interface import position_short

__author__ = 'flex109'


def clear_team_minutes(team):
    for player in team.player_set.all():
        player.set_primary_minutes(0)
        player.set_secondary_minutes(0)


def set_starter_rotation(team):
    clear_team_minutes(team)
    for pos in xrange(1, 6):
        player = team.player_set.get(roster=pos)
        player.set_min_at_pos(pos, 24)


def potential_minutes(player_set):
    minutes = [0] * 5
    for player in player_set:
        minutes[player.primary_position - 1] += player.max_minutes()

        if player.secondary_position > 0:
            minutes[player.secondary_position - 1] += player.max_minutes()

    return minutes


def set_best_rotation(team):
    def pos_order(minutes_list):
        return [pos[0] + 1 for pos in sorted(enumerate(minutes_list), key=operator.itemgetter(1))]

    clear_team_minutes(team)
    players = list(team.player_set.all())
    for player in players:
        player.roster = 0

    pos_min = [0] * 5
    starters = [None] * 5
    for position in pos_order(potential_minutes(team.player_set.all())):
        best = (None, -1)
        for player in players:
            if player.has_position(position) and player.rating() > best[1] and player.roster == 0:
                best = (player, player.rating())
        if best[0] is None:
            print("Fuck this")
        best[0].roster = position

        starters[position - 1] = best[0]
        best[0].set_min_at_pos(position, best[0].max_minutes())
        pos_min[position - 1] += best[0].get_all_minutes()
        best[0].save()

    for position in pos_order(potential_minutes(team.player_set.filter(roster=0))):
        while True:
            best = (None, -1)
            for player in players:
                if player.has_position(position) and player.get_all_minutes() < player.max_minutes() and \
                                player.roster == 0 and player.rating() > best[1]:
                    best = player, player.rating()

            if best[0] is None:
                break

            minutes_played = min(best[0].max_minutes() - best[0].get_all_minutes(), 24 - pos_min[position - 1])
            best[0].set_min_at_pos(position, minutes_played)
            pos_min[position - 1] += minutes_played

            if pos_min[position - 1] == 24:
                break

        if pos_min[position - 1] < 24:
            starters[position - 1].set_min_at_pos(position, starters[position - 1].min_at_pos(position) + (
                24 - pos_min[position - 1]))

    for player in players:
        player.save()

    print(team.name)
    # for i in range(len(starters)):
    #     print("{0} {1}:{2}".format(starters[i].name, position_short(i + 1), starters[i].min_at_pos(i + 1)))
    # for player in players:
    #     if player.roster == 0 and player.get_all_minutes() > 0:
    #         line = "{0} ".format(player.name)
    #         if player.get_primary_minutes() > 0:
    #             line += "{0} {1} ".format(position_short(player.primary_position), player.get_primary_minutes())
    #         if player.get_secondary_minutes() > 0:
    #             line += "{0} {1}".format(position_short(player.secondary_position), player.get_secondary_minutes())
    #         print(line)

    rotation = find_rotation(team)
    if rotation is None:
        raise RuntimeError("Rotation is not valid!")
    print("Rotation Rating: {0}".format(team.rotation_rating()))


def find_rotation(team):
    full_team = team.starters() + team.bench()

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
                current_player = full_team[current_player_index]
                cpi = current_player_index
                tp, ts = time_played[cpi]
                new_time_played[cpi] = (
                    (tp + current_stint), ts) if current_player.primary_position - 1 == position else \
                    (tp, (ts + current_stint))
                players_in = [pos[-1][0] for pos in rotation]

                result = None
                for player_index in xrange(len(full_team)):
                    player = full_team[player_index]
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
        rotation.append(((i, full_team[i].min_at_pos(i + 1) / 2),))

    time_played = [(0, 0) for i in xrange(len(full_team))]

    return check_rotation(rotation, 0, time_played)


def tiebreak(season, teams):
    def head_to_head(team, opp):
        wins = team.home_game.filter(Q(away_team=opp) & Q(homeScore__gt=F("awayScore")), season=season.year).count()
        wins += team.away_game.filter(Q(home_team=opp) & Q(awayScore__gt=F("homeScore")), season=season.year).count()
        return wins

    if len(teams) == 2:
        avb = head_to_head(teams[0], teams[1])
        bva = head_to_head(teams[1], teams[0])
        if avb > bva:
            return teams[:]
        elif bva > avb:
            return teams[::-1]

    return sorted(teams, key=Team.point_diff, reverse=True)


def seed(teams, season):
    ties = []
    for i in range(len(teams)):
        team = teams[i]
        if len(ties) == 0 or ties[-1].wins == team.wins:
            ties.append(team)
        else:
            if len(ties) > 1:
                ties_broken = tiebreak(season, ties)
                for j in range(len(ties_broken)):
                    teams[i - len(ties) + j] = ties_broken[j]

            ties = [teams[i]]

    if len(ties) > 1:
        ties_broken = tiebreak(season, ties)
        for j in range(len(ties_broken)):
            teams[len(teams) - len(ties) + j] = ties_broken[j]

    return teams


class Team(models.Model):
    name = models.CharField(max_length=50)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    division = models.IntegerField(default=0)
    owner = models.OneToOneField(User, null=True)

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_team"

    def is_ai(self):
        return self.owner is None

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

    def div_rank(self):
        agg = seed(list(Team.objects.filter(division=self.division).order_by("-wins")), current_season())
        for i in range(len(agg)):
            if agg[i].id == self.id:
                return i + 1

    def point_diff(self):
        try:
            home_scores = self.home_game.filter(season=current_season().year, week__gte=0).aggregate(
                team_score=Sum('homeScore'), opp_score=Sum('awayScore'))
            away_scores = self.away_game.filter(season=current_season().year, week__gte=0).aggregate(
                team_score=Sum('awayScore'), opp_score=Sum('homeScore'))
            if home_scores['team_score'] is None: home_scores['team_score'] = 0
            if home_scores['opp_score'] is None: home_scores['opp_score'] = 0
            if away_scores['team_score'] is None: away_scores['team_score'] = 0
            if away_scores['opp_score'] is None: away_scores['opp_score'] = 0
            return (home_scores['team_score'] + away_scores['team_score'] - home_scores['opp_score'] - away_scores[
                'opp_score']) / float(self.wins + self.losses)
        except ZeroDivisionError:
            return 0.0

    def rotation_rating(self):
        rating = 0.0
        for player in self.player_set.all():
            rating += player.rating() * (player.get_primary_minutes() + player.get_secondary_minutes())

        return rating/(GAME_LENGTH*5.0)






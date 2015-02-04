from random import shuffle, randrange, gauss
from django.db.models import Q
import operator
from dynasty.models import Team, Player
from dynasty.models.player import pack_values
from dynasty.models.team import seed
from dynasty.constants import GAME_LENGTH, FNAMES, LNAMES
from dynasty.templatetags.dynasty_interface import player_positions
from dynasty.utils import get_binomial_result

__author__ = 'flex109'


def choose_priorities(team, round, expansion):

    def min_index(data):
        return min(enumerate(data), key=operator.itemgetter(1))

    players = team.player_set.all()
    position_times = [0, 0, 0, 0, 0]
    position_age = [[], [], [], [], []]
    position_rating = [0, 0, 0, 0, 0]
    for player in players:
        minutes = 0
        if position_times[player.primary_position - 1] < GAME_LENGTH:
            minutes = min(GAME_LENGTH - position_times[player.primary_position - 1], player.max_minutes())
            position_times[player.primary_position - 1] += minutes
            position_age[player.primary_position - 1].append(player.age)
            if player.rating() > position_rating[player.primary_position - 1]:
                position_rating[player.primary_position - 1] = player.rating()

        if player.secondary_position > 0:
            position_age[player.secondary_position - 1].append(player.age)
            if player.rating() > position_rating[player.secondary_position - 1]:
                position_rating[player.secondary_position - 1] = player.rating()

            if minutes < player.max_minutes() and position_times[player.secondary_position - 1] < GAME_LENGTH:
                position_times[player.secondary_position - 1] += min(player.max_minutes() - minutes, GAME_LENGTH - position_times[player.primary_position - 1])

    desired_position = 0
    win_now = True
    i, d = min_index(position_times)
    if d < 24:
        desired_position = i + 1
    elif not expansion and team.win_pct() > 0.4:
        i, d = min_index(position_rating)
        desired_position = i + 1
    elif not expansion and team.win_pct() <= 0.4:
        i, d = min_index([sum(l)/float(len(l)) for l in position_age])
        desired_position = i + 1

    if expansion:
        win_now = round < 8
    else:
        win_now = team.win_pct() < 0.4
    if team.name == "Rush":
        pass

    return desired_position, win_now


def run_draft(expansion=False):
    rounds = 12 if expansion else 2

    # Set draft order - worst to first for regular draft, random for expansion.
    draft_order = list(Team.objects.all())
    if not expansion:
        draft_order = seed(draft_order)[::-1]
    else:
        shuffle(draft_order)

    # create players
    num_players = int(rounds*len(draft_order)*1.2)
    for position in range(1, 6):
        for _ in range(num_players/5):
            create_random_player(None, age=-1, position=position)

    for round in range(rounds):
        pick = 1
        for team in draft_order:

            position, win_now = choose_priorities(team, round, expansion)

            pool = Player.objects.filter(age=-1)

            if position > 0:
                pool = pool.filter(Q(primary_position=position) | Q(secondary_position=position))

            pool = list(pool)

            if win_now:
                pool = sorted(pool, reverse=True, key=Player.rating)
            else:
                pool = sorted(pool, reverse=True, key=Player.scout)

            drafted_player = pool[0]
            print("{0}:{1} \t{2:10}\t{7:5}\t{3:30}\t{4}\t{5}\t{6}".format(round, pick, team.name, drafted_player.name,
                                                            drafted_player.offense, drafted_player.defense, drafted_player.athletics,
                                                            player_positions(drafted_player)))
            drafted_player.team = team
            drafted_player.age = 0
            drafted_player.save()
            pick += 1

        if expansion:
            draft_order = draft_order[::-1]

    undrafted = Player.objects.filter(age=-1)
    for player in undrafted:
        player.age = 0
        player.save()



def create_random_player(team, age=1, position=0, roster=0):
    if position == 0:
        position = randrange(5) + 1
        s_position = get_secondary_position(position)
    else:
        s_position = get_secondary_position(position)

    name = FNAMES[randrange(len(FNAMES))] + " " + LNAMES[randrange(len(LNAMES))]
    skill =  get_binomial_result(1, 10, 0.35)
    shooting = get_binomial_result(1, 10, 0.35)
    athletics = get_binomial_result(1, 10, 0.35)
    stamina = get_binomial_result(1, 10, 0.35)

    attrs = [skill, shooting, athletics, stamina]
    amplitudes = []
    for i in xrange(len(attrs)):
        # Growth amplitude
        amplitudes.append(get_binomial_result(0, 10 - attrs[i], 0.4))
        peak = attrs[i] + amplitudes[-1]
        amplitudes.append(get_binomial_result(0, peak-1, 0.4))

    player = Player.objects.create(name=name, primary_position=position, secondary_position=s_position, defense=shooting,
                          offense=skill, prime_year=randrange(6, 11),
                          improvement_curves=pack_values([randrange(3) for _ in xrange(8)], 3),
                          improvement_amplitudes=pack_values(amplitudes, 11),
                          number=randrange(99),
                          tendency=gauss(0.0, 0.15),
                          athletics=athletics, stamina=stamina, age=age, team=team, roster=roster)

    return player


def get_secondary_position(primary_position):
    secondary_position = 0
    if primary_position == 1:
        if randrange(2) > 0:
            secondary_position = 2
    elif primary_position == 2:
        rand = randrange(3)
        if rand == 2:
            secondary_position = 1
        elif rand == 1:
            secondary_position = 3
    elif primary_position == 3:
        rand = randrange(3)
        if rand == 2:
            secondary_position = 4
        elif rand == 1:
            secondary_position = 2
    elif primary_position == 4:
        rand = randrange(3)
        if rand == 2:
            secondary_position = 5
        elif rand == 3:
            secondary_position = 3
    elif primary_position == 5:
        rand = randrange(2)
        if rand == 1:
            secondary_position = 4
    return secondary_position
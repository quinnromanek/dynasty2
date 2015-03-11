from random import shuffle, randrange, gauss
from django.db.models import Q
import operator
from dynasty.models import Team, Player, Game, Series, Season, Contract
from dynasty.models.contract import sign_draft_contract, resign_offer, create_fa_offer
from dynasty.models.player import pack_values
from dynasty.models.team import seed, set_best_rotation
from dynasty.constants import *
from dynasty.templatetags.dynasty_interface import player_positions
from dynasty.utils import get_binomial_result

__author__ = 'flex109'


def play_regular_season_week(season):
    games = Game.objects.filter(season=season.year, week=season.week)
    for game in games:
        game.play()
        print("{0}:{1} {2}:{3}".format(game.home_team.name, game.homeScore, game.away_team.name,
                                       game.awayScore))
        game.save()
        home = game.home_team
        away = game.away_team
        if game.homeScore > game.awayScore:
            home.wins += 1
            away.losses += 1
        else:
            home.losses += 1
            away.wins += 1

        home.save()
        away.save()

    season.week += 1
    if season.week == SEASON_LENGTH:
        season.playoff_round = 1
        season.week = -1
        start_playoffs(season)
    season.save()


def play_playoff_week(season):
    games = Game.objects.filter(season=season.year, week=season.week, series__round=season.playoff_round)

    for game in games:
        game.play()

    if Series.objects.filter(Q(home_team_wins__lt=PLAYOFF_WINS) & Q(away_team_wins__lt=PLAYOFF_WINS),
                             round=season.playoff_round, season=season).count() == 0:
        # All series in round are finished.
        if season.playoff_round == 3:
            # Season is done. Crown new champion
            season.champion = Series.objects.filter(season=season).get(round=3).winner().name
            print("{0} have won the title.".format(season.champion))
            finish_season(season)
        else:
            print("Playoff round {0} complete.".format(season.playoff_round))
            # Move on to the next round. The teams should have been placed already.
            season.playoff_round += 1
            for series in Series.objects.filter(season=season, round=season.playoff_round):
                series.begin()
            season.week = -1
    else:
        # Keep playing the current round.
        season.week -= 1

    season.save()


def play_offseason_week(season):
    if season.playoff_round == -1 * FREE_AGENCY_WEEKS - 2:
        for team in Team.objects.all():
            if team.is_ai():
                expiring = list(Contract.objects.filter(team=team))
                expiring = filter(lambda x: x.years_left(season) == 0, expiring)
                for contract in expiring:
                    resign = resign_offer(team, contract.player, contract.salary)
                    if resign is not None:
                        create_fa_offer(season, team, contract.player, resign[0], resign[1])


    elif season.playoff_round < -1:
        pass
    else:
        pass


def choose_priorities(best_available, team, round, expansion):
    def min_index(data):
        return min(enumerate(data), key=operator.itemgetter(1))

    def min_index_multiple(data):
        indices = []
        minimum = 1000
        for i, d in enumerate(data):
            if d < minimum:
                indices = [i]
                minimum = d
            elif d == minimum:
                indices.append(i)

        return indices, minimum


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
                position_times[player.secondary_position - 1] += min(player.max_minutes() - minutes,
                                                                     GAME_LENGTH - position_times[
                                                                         player.secondary_position - 1])

    desired_position = 0
    win_now = True
    indices, d = min_index_multiple(position_times)
    if d < 24:
        if len(indices) == 1:
            desired_position = indices[0] + 1
        else:
            shuffle(indices)
            i, d = max([(j, best_available[j]) for j in indices], key=operator.itemgetter(1))
            desired_position = i + 1
    elif not expansion and team.win_pct() > 0.4:
        i, d = min_index(position_rating)
        desired_position = i + 1
    elif not expansion and team.win_pct() <= 0.4:
        i, d = min_index([sum(l) / float(len(l)) for l in position_age])
        desired_position = i + 1

    if expansion:
        win_now = round < 8
    else:
        win_now = team.win_pct() < 0.4

    return desired_position, win_now


def run_draft(season, last_season=None, expansion=False):
    rounds = 12 if expansion else 2

    def find_best_available(pos):
        pos_pool = Player.objects.filter(Q(primary_position=position) | Q(secondary_position=position), age=-1)
        if pos_pool.count() == 0:
            return -1
        else:
            return sorted(list(pos_pool), key=Player.rating, reverse=True)[0].rating()

    # Set draft order - worst to first for regular draft, random for expansion.
    draft_order = list(Team.objects.all())
    if not expansion:
        draft_order = seed(draft_order, last_season)[::-1]
    else:
        shuffle(draft_order)

    # create players
    num_players = int(rounds * len(draft_order) * 1.2)
    if expansion:
        for position in range(1, 6):
            for _ in range(num_players / 5):
                create_random_player(None, age=-1, position=position)
    else:
        for _ in xrange(num_players):
            create_random_player(None, age=-1)

    best_available = [-1] * 5

    for position in range(1, 6):
        best_available[position - 1] = find_best_available(position)

    for round in range(rounds):
        pick = 1
        for team in draft_order:

            position, win_now = choose_priorities(best_available, team, round, expansion)

            pool = Player.objects.filter(age=-1)

            if position > 0:
                pool = pool.filter(Q(primary_position=position) | Q(secondary_position=position))

            pool = list(pool)
            if len(pool) == 0:
                pool = list(Player.objects.filter(age=-1))

            if win_now:
                pool = sorted(pool, reverse=True, key=Player.rating)
            else:
                pool = sorted(pool, reverse=True, key=Player.scout)

            drafted_player = pool[0]
            print(
                "{8:3}\t{0}:{1} \t{2:10}\t{7:5}\t{3:30}\t{4}\t{5}\t{6}".format(round, pick, team.name, drafted_player.name,
                                                                               drafted_player.offense,
                                                                               drafted_player.defense,
                                                                               drafted_player.athletics,
                                                                               player_positions(drafted_player),
                                                                               position))
            drafted_player.team = team
            drafted_player.age = 0
            sign_draft_contract(drafted_player, team, pick, round, season, expansion)
            drafted_player.save()
            best_available[drafted_player.primary_position - 1] = find_best_available(drafted_player.primary_position)
            if drafted_player.secondary_position > 0:
                best_available[drafted_player.secondary_position - 1] = find_best_available(
                    drafted_player.secondary_position)

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
    skill = get_binomial_result(1, 10, 0.35)
    shooting = get_binomial_result(1, 10, 0.35)
    athletics = get_binomial_result(1, 10, 0.35)
    stamina = get_binomial_result(1, 10, 0.35)

    attrs = [skill, shooting, athletics, stamina]
    amplitudes = []
    for i in xrange(len(attrs)):
        # Growth amplitude
        amplitudes.append(get_binomial_result(0, 10 - attrs[i], 0.4))
        peak = attrs[i] + amplitudes[-1]
        amplitudes.append(get_binomial_result(0, peak - 1, 0.4))

    player = Player.objects.create(name=name, primary_position=position, secondary_position=s_position,
                                   defense=shooting,
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


def create_schedule(season, div_games=DIVISION_GAMES, conf_games=CONFERENCE_GAMES, int_games=1):
    def team_id(team_name):
        return Team.objects.get(name=team_name)

    weeks = 3 * div_games * [0] + 4 * conf_games * [1] + int_games * [2]
    shuffle(weeks)
    div_game_list = get_div_games([0, 1, 2, 3]) + list(get_div_games([0, 1, 2, 3]))
    for i in range(len(div_game_list)):
        for j in range(len(div_game_list[i])):
            if i >= len(div_game_list) / 2:
                div_game_list[i][j].reverse()
    shuffle(div_game_list)
    counts = [0, 0, 0]
    conf_game_list = range(4) * conf_games
    shuffle(conf_game_list)
    int_game_list = randrange(4)

    i = 0
    for game_type in weeks:

        if game_type == 0:
            # Division game
            vs = div_game_list[counts[game_type]]
            for div in range(4):
                for game in vs:
                    # print(game)

                    Game.objects.create(away_team=team_id(TEAMS[div][game[0]]), home_team=team_id(TEAMS[div][game[1]]),
                                        week=i, season=season.year)
        elif game_type == 1:
            # Conference game
            vs = conf_game_list[counts[game_type]]
            for div in [0, 2]:
                for ti in range(4):
                    game = [TEAMS[div][ti], TEAMS[div + 1][(ti + vs) % 4]]
                    shuffle(game)
                    Game.objects.create(away_team=team_id(game[0]), home_team=team_id(game[1]), week=i,
                                        season=season.year)
        else:
            # Interconf game
            vs = int_game_list
            for div in [0, 1]:
                for ti in range(4):
                    game = [TEAMS[div][ti], TEAMS[div + 2][(ti + vs) % 4]]
                    Game.objects.create(away_team=team_id(game[0]), home_team=team_id(game[1]), week=i,
                                        season=season.year)
        counts[game_type] += 1

        i += 1


def get_div_games(division):
    weeks = []
    for i in range(len(division) - 1):
        week = []
        counted = []
        for ti in range(len(division)):
            t2 = (ti + i + 1) % len(division)
            if division[ti] not in counted and division[t2] not in counted:
                week.append([division[ti], division[t2]])
                counted.extend([division[ti], division[t2]])
        weeks.append(week)
    return weeks


def start_playoffs(season):
    all_teams = seed(list(Team.objects.all().order_by("-wins")), season)
    playoff_teams = []
    wild_cards = []
    for team in all_teams:
        if team.div_rank() == 1:
            playoff_teams.append(team)
        else:
            wild_cards.append(team)

    wild_cards = seed(wild_cards, season)
    playoff_teams.append(wild_cards[0])
    playoff_teams.append(wild_cards[1])
    playoff_teams = seed(playoff_teams, season)
    championship = Series.objects.create(season=season, round=3)
    round2 = []
    for r2 in xrange(2):
        round2.append(Series.objects.create(advance=championship, season=season, round=2, home_team=playoff_teams[r2],
                                            home_team_seed=(r2 + 1)))

    # 3 v 6 matchup
    Series.objects.create(advance=round2[1], season=season, round=1,
                          home_team=playoff_teams[2], home_team_seed=3,
                          away_team=playoff_teams[5], away_team_seed=6)
    # 4 v 5 matchup
    Series.objects.create(advance=round2[0], season=season, round=1,
                          home_team=playoff_teams[3], home_team_seed=4,
                          away_team=playoff_teams[4], away_team_seed=5)

    for series in Series.objects.filter(round=1, season=season):
        series.begin()


def finish_season(season):
    # Season is over, what do we do?
    season.name = "done"
    season.save()
    new_season = Season.objects.create(name="main", year=(season.year + 1))
    create_schedule(new_season)
    # Draft first
    run_draft(new_season, last_season=season)
    # Then we age all players
    for player in Player.objects.all():
        player.grow_year()
    for team in Team.objects.all():
        team.wins = 0
        team.losses = 0
        set_best_rotation(team)
        team.save()
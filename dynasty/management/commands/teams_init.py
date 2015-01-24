from dynasty.models import Team, Player, Game, Season, PlayerStats
from django.core.management.base import BaseCommand, CommandError
from random import randrange, shuffle
from itertools import combinations
from dynasty.utils import get_binomial_result

teams = [
    ["Rush", "Muscle", "Gryphons", "Knights"],
    ["Wolves", "Bandits", "Cobras", "Phoenix"],
    ["Dragons", "Warriors", "Nova", "Diamond"],
    ["Flames", "Crocs", "Zombies", "Pilgrims"]
]
fnames = ["George", "James", "Clint", "Alex", "Alexander",
          "Fred", "Tom", "Abraham", "Gustav", "Joseph", "Andrew", "Zach",
          "Michael", "Eric", "Matthew", "Daniel", "Brandon", "Liam", "Lewis",
          "Andre", "Frank", "Asher", "LaRon", "Chris", "Nick", "Patrick",
          "Max", "Xavier", "Dan", "Sean", "Shawn", "Mark", "Giuseppe",
          "Stephen", "Sam", "Samuel", "Sammy", "Mike", "Sebastian", "Lee", "Ming", "Tao", "Jose",
          "Eduardo", "Jim", "Jimmy", "D.J", "Allen", "Ray", "Griffin", "Quinn", "Louis", "Lou", "Will",
          "William", "Willie", "Raymond", "Connor", "C.J", "Ethan", "Carter", "John", "Johnny", "Mitchell",
          "Francisco", "Jamie", "Victor", "Paul", "Harry", "Harrison", "Noah", "Desmond", "Ryan", "Weston"  # 74
]
lnames = [
    "Bradley", "Marshall", "Gordon",
    "Jordan", "Romanek", "Owen", "Goldstein", "Robinson", "Louis",
    "Thomas", "Conrad", "Waterson", "Jacques", "Smithson", "Binks",
    "Anderson", "Moran", "Jones", "Roberts", "Richardson", "Hanson",
    "Bransen", "Enroth", "Butler", "Tyler", "Wallace", "Franklin",
    "Washington", "Madison", "Mason", "Johnson", "Miller", "Allen", "Green", "Li",
    "Lincoln", "Bird", "Monroe", "Jefferson", "Richards", "Smith", "Williams", "Lopez",
    "Brown", "Davis", "Wilson", "Moore", "Taylor", "Thomas", "Jackson", "White", "Harris",
    "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lee"  # 60
]


def make_teams():
    """ Cleans all teams and repopulates divisions. """
    Team.objects.all().delete()

    for div in [0, 1, 2, 3]:
        for tname in teams[div]:
            Team.objects.create(name=tname, division=div)


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


def create_schedule(div_games=2, conf_games=1, int_games=1):
    def team_id(team_name):
        return Team.objects.get(name=team_name)

    Game.objects.all().delete()
    weeks = 3 * div_games * [0] + 4 * conf_games * [1] + int_games * [2]
    shuffle(weeks)
    div_game_list = get_div_games([0, 1, 2, 3]) + list(get_div_games([0, 1, 2, 3]))
    for i in range(len(div_game_list)):
        for j in range(len(div_game_list[i])):
            if i >= len(div_game_list) / 2:
                print("Switching {0} {1}".format(i, j))
                div_game_list[i][j].reverse()
    print(div_game_list)
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

                    Game.objects.create(away_team=team_id(teams[div][game[0]]), home_team=team_id(teams[div][game[1]]),
                                        week=i, season=0)
        elif game_type == 1:
            # Conference game
            vs = conf_game_list[counts[game_type]]
            for div in [0, 2]:
                for ti in range(4):
                    game = [teams[div][ti], teams[div + 1][(ti + vs) % 4]]
                    shuffle(game)
                    Game.objects.create(away_team=team_id(game[0]), home_team=team_id(game[1]), week=i, season=0)
        else:
            # Interconf game
            vs = int_game_list
            for div in [0, 1]:
                for ti in range(4):
                    game = [teams[div][ti], teams[div + 2][(ti + vs) % 4]]
                    Game.objects.create(away_team=team_id(game[0]), home_team=team_id(game[1]), week=i, season=0)
        counts[game_type] += 1

        i += 1


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


def create_random_player(team, age=1, position=0, roster=0):
    if position == 0:
        position = randrange(5) + 1
    name = fnames[randrange(len(fnames))] + " " + lnames[randrange(len(lnames))]
    s_position = get_secondary_position(position)
    skill =  get_binomial_result(1, 10, 0.35)
    shooting = get_binomial_result(1, 10, 0.35)
    stamina = get_binomial_result(1, 10, 0.35)
    Player.objects.create(name=name, primary_position=position, secondary_position=s_position, defense=skill,
                          offense=shooting,
                          athletics=stamina, age=age, team=team, roster=roster)



def generate_team(team):
    for starter in range(1, 6):
        create_random_player(team=team, position=starter, roster=starter)
    for player in range(7):
        create_random_player(team=team)

    starters = team.starters()
    for i in range(len(starters)):
        if starters[i].primary_position - 1 == i:
            starters[i].set_primary_minutes(18)
        else:
            starters[i].set_secondary_minutes(18)

    bench = team.bench()
    sub_minutes = [0]*5
    for i in range(len(sub_minutes)):
        found = False
        for player in bench:
            if player.primary_position - 1 == i:
                player.set_primary_minutes(6)
                found = True
                break
            if player.secondary_position - 1 == i:
                player.set_secondary_minutes(6)
                found = True
                break
        if found:
            continue
        else:

            if starters[i].primary_position - 1 == i:
                starters[i].set_primary_minutes(24)
            else:
                starters[i].set_secondary_minutes(24)



def generate_players_for_teams():
    Player.objects.all().delete()
    teams = Team.objects.all()
    for team in teams:
        generate_team(team)


class Command(BaseCommand):
    help = "Cleans all teams and repopulates divisions"

    def handle(self, *args, **options):
        Season.objects.all().delete()
        PlayerStats.objects.all().delete()
        make_teams()
        create_schedule()
        generate_players_for_teams()
        Season.objects.create(name="main")
        self.stdout.write("Success.")

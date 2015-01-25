from random import random

__author__ = 'flex109'


def binomial_probability(n, p, k):
    def fact(num):
        if num == 1 or num == 0:
            return 1
        return num * fact(num - 1)

    def factorial(num):
        return float(fact(num))

    return (factorial(n) / (factorial(k) * factorial(n - k))) * p ** k * (1 - p) ** (n - k)


def get_binomial_result(low, high, p):
    n = high - low
    roll = random()
    prob_sum = 0.0
    for i in range(0, n + 1):
        prob_sum += binomial_probability(n, p, i)
        if roll < prob_sum:
            return low + i

    raise ArithmeticError()


def parse_position_string(pos_str):
    try:
        return ["", "PG", "SG", "SF", "PF", "C"].index(pos_str)
    except ValueError:
        return 0


def game_html(game):
    if game.is_finished():
        return "<a href='/teams/{0}'>{1} {2}</a> @ <a href='/teams/{3}'>{4} {5}</a> (<a href='/games/{6}'>Box Score</a>)".format(
            game.away_team.name.lower(), game.away_team.name, game.awayScore, game.home_team.name.lower(),
            game.homeScore,
            game.home_team.name, game.id
        )
    else:
        return "<a href='/teams/{0}'>{1}</a> @ <a href='/teams/{2}'>{3}</a> (<a href='/games/{4}'>Preview</a>)".format(
            game.away_team.name.lower(), game.away_team.name, game.home_team.name.lower(), game.home_team.name, game.id)

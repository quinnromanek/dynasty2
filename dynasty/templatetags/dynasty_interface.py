from django import template

register = template.Library()


@register.filter
def position_short(value):
    table = ["None", "PG", "SG", "SF", "PF", "C"]
    return table[value]


@register.filter
def position_verbose(value):
    table = ["None", "Point Guard", "Shooting Guard", "Small Forward", "Power Forward"
        , "Center"]
    return table[value]


@register.filter
def division_name(value):
    table = ["Northeast", "Southeast", "Northwest", "Southwest"]
    return table[value]

@register.filter
def game_verbose(game):
    if game.is_finished():
        return "{0} {1} - {2} {3}".format(game.home_team.name, game.homeScore, game.awayScore, game.away_team.name)
    else:
        return "{0} - {1}".format(game.home_team.name, game.away_team.name)

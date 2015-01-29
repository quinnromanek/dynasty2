from django import template
from dynasty.utils import game_html
from django.utils.safestring import mark_safe

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
def player_positions(player):
    if player.secondary_position > 0:
        return "{0}|{1}".format(position_short(player.primary_position), position_short(player.secondary_position))
    else:
        return position_short(player.primary_position)



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

@register.filter
def tendency_description(tendency):
    if tendency < -0.25:
        return "Passive"
    elif tendency < 0:
        return "Pass-first"
    elif tendency < 0.25:
        return "Shoot-first"
    else:
        return "Black Hole"

@register.filter
def fatigue_description(fatigue):
    if fatigue < 0:
       return "Rested"
    if fatigue < 5:
        return "Fresh"
    elif fatigue < 15:
        return "Sore"
    elif fatigue < 30:
        return "Tired"
    else:
        return "Exhausted"

@register.filter
def minute_color(player):
    if player.get_all_minutes() > player.max_minutes():
        return "fatigue"
    elif player.get_all_minutes() < player.max_minutes():
        return "rest"
    else:
        return ""

@register.filter
def counting_number(number):
    suffix = ""
    if number % 10 == 1 and number != 11:
        suffix = "st"
    elif number % 10 == 2 and number != 12:
        suffix = "nd"
    elif number % 10 == 3 and number != 13:
        suffix = "rd"
    else:
        suffix = "th"
    return str(number) + suffix

@register.filter
def abs(value):
    value = int(value)
    return value if value >= 0 else value * -1

@register.filter
def week_text(value):
    if value.week >= 0:
        return value.week + 1
    else:
        return "Rd {0}, Gm {1}".format(value.series.round, abs(value.week))



###### Quick ways to generate model links ######
@register.filter()
def game_links(game):
    return mark_safe(game_html(game))

@register.filter()
def game_tr(game):
    def get_class(a, b):
        return "game-win" if a>b else ""
    return mark_safe("<tr><td>{0}</td><td class='{6}'>{1}</td><td>{2}</td><td>vs</td><td>{4}</td><td class='{7}'>{3}</td><td><a href='/games/{5}'>Box</a></td></tr>".format(
       week_text(game), game.home_team.name, game.homeScore, game.away_team.name, game.awayScore, game.id, get_class(game.homeScore, game.awayScore),
       get_class(game.awayScore, game.homeScore)
    ))

@register.filter()
def team_link(team):
    return mark_safe("<a href='/teams/{0}'>{1}</a>".format(team.name.lower(), team.name))

@register.filter()
def player_link(player):
    return mark_safe("<a href='/players/{0}'>{1}</a>".format(player.id, player.name))


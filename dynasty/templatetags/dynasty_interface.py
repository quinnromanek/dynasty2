from django import template

register = template.Library()

@register.filter
def position_short(value):
	table = ["None", "PG", "SG", "SF", "PF", "C"]
	return table[value]

@register.filter
def position_verbose(value):
	table = ["None", "Point Guard", "Shooting Guard", "Small Forward", "Power Forward"
					,"Center"]
	return table[value]

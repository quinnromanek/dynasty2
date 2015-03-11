from django.db import models
from dynasty.models.other import current_season


class Contract(models.Model):
    start = models.IntegerField(default=0)
    years = models.IntegerField(default=1)
    team_option = models.IntegerField(default=0)
    player_option = models.IntegerField(default=0)
    team = models.ForeignKey("dynasty.team")
    salary = models.IntegerField(default=0)

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_contract"

    def years_left(self, season=None):
        if season is None:
            season = current_season()

        return self.start - season.year + self.years

class Transaction(models.Model):
    type = models.IntegerField(default=0)
    # 0 is signing, 1 is trade, etc
    status = models.IntegerField(default=1)
    contract = models.ForeignKey("dynasty.contract")
    player = models.ForeignKey("dynasty.player")
    season = models.IntegerField(default=0)
    COMPLETE = 0 # Signed or trade completed
    PENDING = 1
    ACCEPTED = 2
    DECLINED = 3
    BIDDING = 4



def create_fa_offer(season, team, player, salary, years):
    contract = Contract.objects.create(start=season.year, team=team, salary=salary, years=years)
    return Transaction.objects.create(contract=contract, player=player, season=season.year)

def sign_draft_contract(player, team, pick, round,season, expansion=False):
    if expansion:
        years = 1
    else:
        years = 2
    if expansion:
        salary = [8, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2][round] * 1000000
    else:
        salary = [4, 2][round]*1000000

    salary += (8-pick)*100000 if pick > 8 else (9-pick)* 100000

    contract = Contract.objects.create(start=season.year, team=team, years=years, salary=salary, team_option=1)
    player.contract = contract
    player.save()


def base_salary(player):
    rating = player.rating()
    if rating >= 25:
        return maximum_salary()
    elif rating >= 20:
        return 10000000
    elif rating >= 15:
        return 5000000
    elif rating >= 10:
        return 2000000
    else: return minimum_salary(player)


def minimum_salary(player):
    return 100000 * player.age + 500000


def maximum_salary(player):
    if player.age <= 6:
        return 15000000
    elif player.age <= 9:
        return 18000000
    else:
        return 21000000


def sign_minimum_contract(player, team, years):
    pass

def resign_offer(team, player, old_salary):
    if old_salary > base_salary(player):
        return None
    elif player.rating() > 25:
        return maximum_salary(player), 4
    else:
        return round_salary(base_salary(player) * 0.9), 2


def round_salary(raw_salary):
    return (raw_salary/100000)*100000



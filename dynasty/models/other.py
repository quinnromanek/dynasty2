from django.db import models

__author__ = 'flex109'

class Season(models.Model):
    week = models.IntegerField(default=0)
    year = models.IntegerField(default=0)
    name = models.CharField(max_length=50)
    playoff_round = models.IntegerField(default=0)
    champion = models.CharField(max_length=100, null=True)
    title = models.CharField(max_length=100, default="Welcome to Dynasty")
    story = models.TextField(default="Games start now.")

    def in_playoffs(self):
        return self.playoff_round > 0

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_season"

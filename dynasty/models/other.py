from django.db import models

__author__ = 'flex109'

class Season(models.Model):
    week = models.IntegerField(default=0)
    year = models.IntegerField(default=0)
    name = models.CharField(max_length=50)

    class Meta:
        app_label = "dynasty"
        db_table = "dynasty_season"

import datetime
from django.db import models
from django.utils import timezone
from django.contrib import admin

class Question(models.Model):
    question_text=models.CharField(max_length=200)
    pub_date=models.DateTimeField('date published')
    def __str__(self) -> str:
        return self.question_text
    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

class Choice(models.Model):
    question=models.ForeignKey(Question,on_delete=models.CASCADE)
    choice_text=models.CharField(max_length=200)
    votes=models.IntegerField(default=0)
    def __str__(self) -> str:
        return self.choice_text
    
class ZoneForDB(models.Model):
    name = models.CharField(max_length=200)
    latOfCenter = models.FloatField(default=0.0)
    longOfCenter = models.FloatField(default=0.0)
    stepOfAzimuth = models.FloatField(default=0.25)
    intervals = models.JSONField()
    position = models.CharField(max_length=200, default='')

    def __str__(self):
        return self.name

class TraceAN(models.Model):
    name = models.CharField(max_length=20)
    pods = models.JSONField()
    def __str__(self) -> str:
        return self.name
    
class AirportBuilding(models.Model):
    name = models.CharField(max_length=200)
    polygons = models.JSONField()
    max_lat = models.FloatField(default=90.0)
    min_lat = models.FloatField(default=90.0)
    min_lon = models.FloatField(default=0.0)
    max_lon = models.FloatField(default=0.0)






    
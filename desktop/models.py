from django.db import models


class ChartData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    time = models.CharField(max_length=50)
    soll_spalt = models.FloatField()
    sensor1_str = models.FloatField()
  #  sensor2_str = models.FloatField()
    sensor3_str = models.FloatField()
    soll_kraft = models.FloatField()
    kraft_sensor1 = models.FloatField()
    kraft_sensor2 = models.FloatField()
    KI_1 = models.FloatField()
    KI_2 = models.FloatField()

    def __str__(self):
        return f"Data recorded at {self.time}"

# Create your models here.

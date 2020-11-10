from django.db import models


class StarWarsMeta(models.Model):
    csv_name = models.TextField(max_length=255)
    record_count = models.IntegerField()

    def __str__(self):
        return self.csv_name

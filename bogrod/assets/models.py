from django.db import models


class Asset(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    receipt = models.ImageField(blank=True, null=True)

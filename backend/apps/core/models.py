from django.db import models


class TimeStampedModel(models.Model):
    """Base for every table: Django fills created_at and updated_at on its own."""

    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        abstract = True

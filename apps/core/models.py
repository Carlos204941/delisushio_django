from django.db import models


class BusinessHours(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True)
    is_open = models.BooleanField(default=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['day_of_week']
        verbose_name_plural = 'Business hours'

    def __str__(self):
        return f"{self.get_day_of_week_display()}: {'Open' if self.is_open else 'Closed'}"

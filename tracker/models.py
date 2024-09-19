from django.db import models
from django.contrib.auth.models import User

class Period(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_day = models.DateField()
    ovulation_day = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'first_day', 'ovulation_day'], name='unique three')
            ]

    def __str__(self):
        return str(self.first_day)
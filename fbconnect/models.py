from django.db import models
from django.contrib.auth.models import User

class FBAssociation(models.Model):
    user = models.ForeignKey(User)
    fbuid = models.CharField(max_length=12,  unique=True)

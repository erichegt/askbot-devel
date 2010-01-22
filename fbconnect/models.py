from django.db import models
from django.contrib.auth.models import User

class FBAssociation(models.Model):
    user = models.ForeignKey(User)
    fbuid = models.TextField(max_length=12)

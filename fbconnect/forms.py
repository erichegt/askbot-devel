from django_authopenid.forms import NextUrlField,  UserNameField,  UserEmailField

from django import forms

class FBConnectRegisterForm(forms.Form):
    next = NextUrlField()
    username = UserNameField()
    email = UserEmailField()

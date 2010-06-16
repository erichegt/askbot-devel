"""
linking of askbot modules to admin interface
"""
# -*- coding: utf-8 -*-
from django.contrib import admin
from askbot import models

class AnonymousQuestionAdmin(admin.ModelAdmin):
    """AnonymousQuestion admin class"""

class QuestionAdmin(admin.ModelAdmin):
    """Question admin class"""

class TagAdmin(admin.ModelAdmin):
    """Tag admin class"""

class Answerdmin(admin.ModelAdmin):
    """Answer admin class"""

class CommentAdmin(admin.ModelAdmin):
    """  admin class"""

class VoteAdmin(admin.ModelAdmin):
    """  admin class"""

class FlaggedItemAdmin(admin.ModelAdmin):
    """  admin class"""

class FavoriteQuestionAdmin(admin.ModelAdmin):
    """  admin class"""

class QuestionRevisionAdmin(admin.ModelAdmin):
    """  admin class"""

class AnswerRevisionAdmin(admin.ModelAdmin):
    """  admin class"""

class AwardAdmin(admin.ModelAdmin):
    """  admin class"""

class BadgeAdmin(admin.ModelAdmin):
    """  admin class"""

class ReputeAdmin(admin.ModelAdmin):
    """  admin class"""

class ActivityAdmin(admin.ModelAdmin):
    """  admin class"""
    
#class BookAdmin(admin.ModelAdmin):
#    """  admin class"""
    
#class BookAuthorInfoAdmin(admin.ModelAdmin):
#    """  admin class"""
    
#class BookAuthorRssAdmin(admin.ModelAdmin):
#    """  admin class"""
    
admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.Answer, Answerdmin)
admin.site.register(models.Comment, CommentAdmin)
admin.site.register(models.Vote, VoteAdmin)
admin.site.register(models.FlaggedItem, FlaggedItemAdmin)
admin.site.register(models.FavoriteQuestion, FavoriteQuestionAdmin)
admin.site.register(models.QuestionRevision, QuestionRevisionAdmin)
admin.site.register(models.AnswerRevision, AnswerRevisionAdmin)
admin.site.register(models.Badge, BadgeAdmin)
admin.site.register(models.Award, AwardAdmin)
admin.site.register(models.Repute, ReputeAdmin)
admin.site.register(models.Activity, ActivityAdmin)
#admin.site.register(Book, BookAdmin)
#admin.site.register(BookAuthorInfo, BookAuthorInfoAdmin)
#admin.site.register(BookAuthorRss, BookAuthorRssAdmin)

"""Version 1 of API helper for the south orm
usage of this api implementation starts with migration 24
"""
from askbot.migrations_api import BaseAPI
from django.db import models
#from django.contrib.contenttypes.models import ContentType

class API(BaseAPI):
    def get_origin_post_from_content_object(self, parent):
        """follows relations from the parent object
        until origin post (question) is found
        starting point is always ``parent.content_object``
        """
        model = parent.content_type.model
        id = parent.object_id
        #print 'model is ' + model
        if model == 'question':
            return self.orm.Question.objects.get(id=id)
        elif model == 'answer':
            return self.orm.Answer.objects.get(id=id).question
        elif model == 'favoritequestion':
            try:
                return self.orm.FavoriteQuestion.objects.get(id=id).question
            except self.orm.FavoriteQuestion.DoesNotExist:
                #ignore this issue for now
                return None
        elif model == 'answerrevision':
            return self.orm.AnswerRevision.objects.get(id=id).answer.question
        elif model == 'questionrevision':
            return self.orm.QuestionRevision.objects.get(id=id).question
        elif model == 'comment':
            comment = self.orm.Comment.objects.get(id=id)
            return self.get_origin_post_from_content_object(comment)
        else:
            #print 'dropped migration of activity in %s' % model
            return None

    def get_moderators_and_admins(self):
        """return list of forum moderators and django site admins
        """
        filter_expression = models.Q(status='m') | models.Q(is_superuser=True)
        return self.orm['auth.User'].objects.filter(filter_expression)

    def get_activity_items_for_object(self, instance):
        """get all activity items that have content_object set
        where ``<Activity instance>.content_object == instance``
        """
        return self.orm.Activity.objects.filter(
            object_id = instance.id,
            content_type = self.get_content_type_for_model(instance)
        )

    def get_content_type_for_model(self, instance):
        ct = self.orm['contenttypes.ContentType'].objects
        return ct.get(app_label='askbot', model=instance._meta.object_name.lower())

    def add_recipients_to_activity(self, recipients, activity):
        for recipient in recipients:
            memo = self.orm.ActivityAuditStatus(
                user = recipient,
                activity = activity,
            )
            memo.save()

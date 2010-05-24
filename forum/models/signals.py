import django.dispatch

tags_updated = django.dispatch.Signal(providing_args=['question'])

#todo: this one seems to be unused
edit_question_or_answer = django.dispatch.Signal(
                                    providing_args=['instance', 'modified_by']
                                )
delete_post_or_answer = django.dispatch.Signal(
                                    providing_args=['instance', 'deleted_by']
                                )
mark_offensive = django.dispatch.Signal(providing_args=['instance', 'mark_by'])
user_updated = django.dispatch.Signal(providing_args=['instance', 'updated_by'])
#todo: move this to authentication app
user_logged_in = django.dispatch.Signal(providing_args=['session'])
#todo: remove this upon migration to 1.2
fake_m2m_changed = django.dispatch.Signal(providing_args=['instance','created'])

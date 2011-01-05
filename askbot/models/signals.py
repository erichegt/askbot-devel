"""Custom django signals defined for the askbot forum application.
"""
import django.dispatch

tags_updated = django.dispatch.Signal(
                        providing_args=['tags', 'user', 'timestamp']
                    )

#todo: this one seems to be unused
edit_question_or_answer = django.dispatch.Signal(
                                    providing_args=['instance', 'modified_by']
                                )
delete_question_or_answer = django.dispatch.Signal(
                                    providing_args=['instance', 'deleted_by']
                                )
flag_offensive = django.dispatch.Signal(providing_args=['instance', 'mark_by'])
user_updated = django.dispatch.Signal(providing_args=['instance', 'updated_by'])
#todo: move this to authentication app
user_logged_in = django.dispatch.Signal(providing_args=['session'])

post_updated = django.dispatch.Signal(
                                providing_args=[
                                            'post', 
                                            'updated_by',
                                            'newly_mentioned_users'
                                        ]
                            )
site_visited = django.dispatch.Signal(providing_args=['user', 'timestamp'])

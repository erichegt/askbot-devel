"""utility functions used by Askbot test cases
"""
from askbot import models

def create_user(
            username = None, 
            email = None, 
            notification_schedule = None,
            date_joined = None,
            status = 'a'
        ):
    """Creates a user and sets default update subscription
    settings"""
    user = models.User.objects.create_user(username, email)
    if date_joined is not None:
        user.date_joined = date_joined
        user.save()
    user.set_status(status)
    if notification_schedule == None:
        notification_schedule = models.EmailFeedSetting.NO_EMAIL_SCHEDULE
        
    for feed_type, frequency in notification_schedule.items():
        feed = models.EmailFeedSetting(
                        feed_type = feed_type,
                        frequency = frequency,
                        subscriber = user
                    )
        feed.save()
    return user


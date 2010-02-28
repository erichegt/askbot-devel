from base import *

from django.utils.translation import ugettext as _

class Badge(models.Model):
    """Awarded for notable actions performed on the site by Users."""
    GOLD = 1
    SILVER = 2
    BRONZE = 3
    TYPE_CHOICES = (
        (GOLD,   _('gold')),
        (SILVER, _('silver')),
        (BRONZE, _('bronze')),
    )

    name        = models.CharField(max_length=50)
    type        = models.SmallIntegerField(choices=TYPE_CHOICES)
    slug        = models.SlugField(max_length=50, blank=True)
    description = models.CharField(max_length=300)
    multiple    = models.BooleanField(default=False)
    # Denormalised data
    awarded_count = models.PositiveIntegerField(default=0)

    awarded_to    = models.ManyToManyField(User, through='Award', related_name='badges')

    class Meta:
        app_label = 'forum'
        db_table = u'badge'
        ordering = ('name',)
        unique_together = ('name', 'type')

    def __unicode__(self):
        return u'%s: %s' % (self.get_type_display(), self.name)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = self.name#slugify(self.name)
        super(Badge, self).save(**kwargs)

    def get_absolute_url(self):
        return '%s%s/' % (reverse('badge', args=[self.id]), self.slug)

class AwardManager(models.Manager):
    def get_recent_awards(self):
        awards = super(AwardManager, self).extra(
            select={'badge_id': 'badge.id', 'badge_name':'badge.name',
                          'badge_description': 'badge.description', 'badge_type': 'badge.type',
                          'user_id': 'auth_user.id', 'user_name': 'auth_user.username'
                          },
            tables=['award', 'badge', 'auth_user'],
            order_by=['-awarded_at'],
            where=['auth_user.id=award.user_id AND badge_id=badge.id'],
        ).values('badge_id', 'badge_name', 'badge_description', 'badge_type', 'user_id', 'user_name')
        return awards

class Award(models.Model):
    """The awarding of a Badge to a User."""
    user       = models.ForeignKey(User, related_name='award_user')
    badge      = models.ForeignKey('Badge', related_name='award_badge')
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    awarded_at = models.DateTimeField(default=datetime.datetime.now)
    notified   = models.BooleanField(default=False)

    objects = AwardManager()

    def __unicode__(self):
        return u'[%s] is awarded a badge [%s] at %s' % (self.user.username, self.badge.name, self.awarded_at)

    class Meta:
        app_label = 'forum'
        db_table = u'award'

class ReputeManager(models.Manager):
    def get_reputation_by_upvoted_today(self, user):
        """
        For one user in one day, he can only earn rep till certain score (ep. +200)
        by upvoted(also substracted from upvoted canceled). This is because we need
        to prohibit gaming system by upvoting/cancel again and again.
        """
        if user is not None:
            today = datetime.date.today()
            sums = self.filter(models.Q(reputation_type=1) | models.Q(reputation_type=-8),
                                user=user, reputed_at__range=(today, today + datetime.timedelta(1))). \
                               agregate(models.Sum('positive'), models.Sum('negative'))            

            return sums['positive__sum'] + sums['negative__sum']
        else:
            return 0

class Repute(models.Model):
    """The reputation histories for user"""
    user     = models.ForeignKey(User)
    positive = models.SmallIntegerField(default=0)
    negative = models.SmallIntegerField(default=0)
    question = models.ForeignKey('Question')
    reputed_at = models.DateTimeField(default=datetime.datetime.now)
    reputation_type = models.SmallIntegerField(choices=TYPE_REPUTATION)
    reputation = models.IntegerField(default=1)
    
    objects = ReputeManager()

    def __unicode__(self):
        return u'[%s]\' reputation changed at %s' % (self.user.username, self.reputed_at)

    class Meta:
        app_label = 'forum'
        db_table = u'repute'

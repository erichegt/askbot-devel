try:
    from haystack import indexes, site
    from haystack.query import SearchQuerySet
except ImportError:
    pass

from askbot.models import Post, Thread, Tag, User

class ThreadIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    post_text = indexes.CharField(model_attr='posts__text__search')

    def index_queryset(self):
        return Thread.objects.filter(posts__deleted=False)

    def prepare(self, obj):
        self.prepared_data = super(ThreadIndex, self).prepare(object)

        self.prepared_data['tags'] = [tag.name for tag in objects.tags.all()]

class PostIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    post_text = indexes.CharField(model_attr='text')
    author = indexes.CharField(model_attr='user')
    thread_id = indexes.CharField(model_attr='thread')

    def index_queryset(self):
        return Post.objects.filter(deleted=False)

site.register(Post, PostIndex)
site.register(Thread, ThreadIndex)

class AskbotSearchQuerySet(SearchQuerySet):

    #def get_django_queryset(self, model_klass=Thread):
    def get_django_queryset(self):
        id_list = []
        for r in self:
            if getattr(r, 'thread_id'):
                id_list.append(r.thread_id)
            else:
                id_list.append(r.pk)

        return Thread.objects.filter(id__in=set(id_list))

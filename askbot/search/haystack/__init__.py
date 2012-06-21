try:
    from haystack import indexes, site
    from haystack.query import SearchQuerySet
    from askbot.models import Post, Thread, User


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

    class UserIndex(indexes.SearchIndex):
        text = indexes.CharField(document=True, use_template=True)

        def index_queryset(self):
            return User.objects.all()

    site.register(Post, PostIndex)
    site.register(Thread, ThreadIndex)
    site.register(User, UserIndex)

    class AskbotSearchQuerySet(SearchQuerySet):

        def get_django_queryset(self, model_klass=Thread):
            '''dirty hack because models() method from the
            SearchQuerySet does not work </3'''
            id_list = []
            for r in self:
                if r.model_name in ['thread','post'] \
                        and model_klass._meta.object_name.lower() == 'thread':
                    if getattr(r, 'thread_id'):
                        id_list.append(r.thread_id)
                    else:
                        id_list.append(r.pk)
                elif r.model_name == model_klass._meta.object_name.lower():
                    #FIXME: add a highlight here?
                    id_list.append(r.pk)

            return model_klass.objects.filter(id__in=set(id_list))

except:
    pass

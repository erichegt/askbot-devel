import re
from forum.modules import get_modules_script_classes
from forum.authentication.base import AuthenticationConsumer, ConsumerTemplateContext

class ConsumerAndContext():
    def __init__(self, id, consumer, context):
        self.id = id
        self.consumer = consumer()

        context.id = id
        self.context = context

consumers = dict([
            (re.sub('AuthConsumer$', '', name).lower(), cls) for name, cls
            in get_modules_script_classes('authentication', AuthenticationConsumer).items()
            if not re.search('AbstractAuthConsumer$', name)
        ])

contexts = dict([
            (re.sub('AuthContext$', '', name).lower(), cls) for name, cls
            in get_modules_script_classes('authentication', ConsumerTemplateContext).items()
        ])

AUTH_PROVIDERS = dict([
            (name, ConsumerAndContext(name, consumers[name], contexts[name])) for name in consumers.keys()
            if name in contexts
        ])
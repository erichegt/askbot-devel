from django.template import Library as DjangoLibrary, InvalidTemplateLibrary
from jinja2.ext import Extension as Jinja2Extension
from coffin.interop import (
    DJANGO, JINJA2,
    guess_filter_type, jinja2_filter_to_django, django_filter_to_jinja2)


__all__ = ['Library']


class Library(DjangoLibrary):
    """Version of the Django ``Library`` class that can handle both
    Django template engine tags and filters, as well as Jinja2
    extensions and filters.

    Tries to present a common registration interface to the extension
    author, but provides both template engines with only those
    components they can support.

    Since custom Django tags and Jinja2 extensions are two completely
    different beasts, they are handled completely separately. You can
    register custom Django tags as usual, for example:

        register.tag('current_time', do_current_time)

    Or register a Jinja2 extension like this:

        register.tag(CurrentTimeNode)

    Filters, on the other hand, work similarily in both engines, and
    for the most one can't tell whether a filter function was written
    for Django or Jinja2. A compatibility layer is used to make to
    make the filters you register usuable with both engines:

        register.filter('cut', cut)

    However, some of the more powerful filters just won't work in
    Django, for example if more than one argument is required, or if
    context- or environmentfilters are used. If ``cut`` in the above
    example where such an extended filter, it would only be registered
    with Jinja.

    See also the module documentation for ``coffin.interop`` for
    information on some of the limitations of this conversion.

    TODO: Jinja versions of the ``simple_tag`` and ``inclusion_tag``
    helpers would be nice, though since custom tags are not needed as
    often in Jinja, this is not urgent.
    """

    def __init__(self):
        super(Library, self).__init__()
        self.jinja2_filters = {}
        self.jinja2_extensions = []
        self.jinja2_globals = {}
        self.jinja2_tests = {}

    @classmethod
    def from_django(cls, django_library):
        """Create a Coffin library object from a Django library.

        Specifically, this ensures that filters already registered
        with the Django library are also made available to Jinja,
        where applicable.
        """
        from copy import copy
        result = cls()
        result.filters = copy(django_library.filters)
        result.tags = copy(django_library.tags)
        for name, func in result.filters.iteritems():
            result._register_filter(name, func, jinja2_only=True)
        return result

    def test(self, name=None, func=None):
        def inner(f):
            name = getattr(f, "_decorated_function", f).__name__
            self.jinja2_tests[name] = f
            return f
        if name == None and func == None:
            # @register.test()
            return inner
        elif func == None:
            if (callable(name)):
                # register.test()
                return inner(name)
            else:
                # @register.test('somename') or @register.test(name='somename')
                def dec(func):
                    return self.test(name, func)
                return dec
        elif name != None and func != None:
            # register.filter('somename', somefunc)
            self.jinja2_tests[name] = func
            return func
        else:
            raise InvalidTemplateLibrary("Unsupported arguments to "
                "Library.test: (%r, %r)", (name, func))

    def object(self, name=None, func=None):
        def inner(f):
            name = getattr(f, "_decorated_function", f).__name__
            self.jinja2_globals[name] = f
            return f
        if name == None and func == None:
            # @register.object()
            return inner
        elif func == None:
            if (callable(name)):
                # register.object()
                return inner(name)
            else:
                # @register.object('somename') or @register.object(name='somename')
                def dec(func):
                    return self.object(name, func)
                return dec
        elif name != None and func != None:
            # register.object('somename', somefunc)
            self.jinja2_globals[name] = func
            return func
        else:
            raise InvalidTemplateLibrary("Unsupported arguments to "
                "Library.object: (%r, %r)", (name, func))

    def tag(self, name_or_node=None, compile_function=None):
        """Register a Django template tag (1) or Jinja 2 extension (2).

        For (1), supports the same invocation syntax as the original
        Django version, including use as a decorator.

        For (2), since Jinja 2 extensions are classes (which can't be
        decorated), and have the tag name effectively built in, only the
        following syntax is supported:

            register.tag(MyJinjaExtensionNode)
        """
        if isinstance(name_or_node, Jinja2Extension):
            if compile_function:
                raise InvalidTemplateLibrary('"compile_function" argument not supported for Jinja2 extensions')
            self.jinja2_extensions.append(name_or_node)
            return name_or_node
        else:
            return super(Library, self).tag(name_or_node, compile_function)

    def tag_function(self, func_or_node):
        if issubclass(func_or_node, Jinja2Extension):
            self.jinja2_extensions.append(func_or_node)
            return func_or_node
        else:
            return super(Library, self).tag_function(func_or_node)

    def filter(self, name=None, filter_func=None, jinja2_only=False):
        """Register a filter with both the Django and Jinja2 template
        engines, if possible - or only Jinja2, if ``jinja2_only`` is
        specified. ``jinja2_only`` does not affect conversion of the
        filter if neccessary.

        Implements a compatibility layer to handle the different
        auto-escaping approaches transparently. Extended Jinja2 filter
        features like environment- and contextfilters are however not
        supported in Django. Such filters will only be registered with
        Jinja.

        Supports the same invocation syntax as the original Django
        version, including use as a decorator.

        If the function is supposed to return the registered filter
        (by example of the superclass implementation), but has
        registered multiple filters, a tuple of all filters is
        returned.
        """
        def filter_function(f):
            return self._register_filter(
                getattr(f, "_decorated_function", f).__name__,
                f, jinja2_only=jinja2_only)
        if name == None and filter_func == None:
            # @register.filter()
            return filter_function
        elif filter_func == None:
            if (callable(name)):
                # @register.filter
                return filter_function(name)
            else:
                # @register.filter('somename') or @register.filter(name='somename')
                def dec(func):
                    return self.filter(name, func, jinja2_only=jinja2_only)
                return dec
        elif name != None and filter_func != None:
            # register.filter('somename', somefunc)
            return self._register_filter(name, filter_func,
                jinja2_only=jinja2_only)
        else:
            raise InvalidTemplateLibrary("Unsupported arguments to "
                "Library.filter: (%r, %r)", (name, filter_func))

    def _register_filter(self, name, func, jinja2_only=None):
        filter_type, can_be_ported = guess_filter_type(func)
        if filter_type == JINJA2 and not can_be_ported:
            self.jinja2_filters[name] = func
            return func
        elif filter_type == DJANGO and not can_be_ported:
            if jinja2_only:
                raise ValueError('This filter cannot be ported to Jinja2.')
            self.filters[name] = func
            return func
        elif jinja2_only:
            func = django_filter_to_jinja2(func)
            self.jinja2_filters[name] = func
            return func
        else:
            # register the filter with both engines
            django_func = jinja2_filter_to_django(func)
            jinja2_func = django_filter_to_jinja2(func)
            self.filters[name] = django_func
            self.jinja2_filters[name] = jinja2_func
            return (django_func, jinja2_func)

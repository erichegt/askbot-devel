"""management command that renames a tag or merges
it to another, all corresponding questions are automatically
retagged
"""
import sys
from optparse import make_option
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from askbot import api, models
from askbot.utils import console

def get_admin(seed_user_id = None):
    """requests admin with an optional seeded user id
    """
    try:
        admin = api.get_admin(seed_user_id = seed_user_id)
    except models.User.DoesNotExist, e:
        raise CommandError(e)

    if admin.id != seed_user_id:
        if seed_user_id is None:
            prompt = """You have not provided user id for the moderator
who to assign as the performer this operation, the default moderator is
%s, id=%s. Will that work?""" % (admin.username, admin.id)
        else:
            prompt = """User with id=%s is not a moderator
would you like to select default moderator %s, id=%d
to run this operation?""" % (seed_user_id, admin.username, admin.id)
        choice = console.choice_dialog(prompt, choices = ('yes', 'no'))
        if choice == 'no':
            print 'Canceled'
            sys.exit()
    return admin

def parse_tag_names(input):
    decoded_input = input.decode(sys.stdin.encoding)
    return set(decoded_input.strip().split(' '))

def format_tag_ids(tag_list):
    return ' '.join([str(tag.id) for tag in tag_list])

class Command(BaseCommand):
    "The command object itself"

    help = """Retags questions tagged with <from_names> to <to_names>.

If in the end some tags end up being unused, they are automatically removed.
Tag names are case sensitive, non-ascii characters are also accepted.

* if --user-id is provided, it will be used to set the user performing the operation
* The user must be either administrator or moderator
* if --user-id is not given, the earliest active site administrator will be assigned

Both --to and --from arguments accept multiple tags, but the argument must be quoted
in that case (e.g. --from="raw material" --to="raw-material"), thus tags
can be renamed, merged or split. It is highly recommended to first inspect the
list of questions that are to be affected before running this operation.

The tag rename operation cannot be undone, but the command will
ask you to confirm your action before making changes.
    """
    option_list = BaseCommand.option_list + (
        make_option('--from',
            action = 'store',
            type = 'str',
            dest = 'from',
            default = None,
            help = 'list of tag names which needs to be replaced'
        ),
        make_option('--to',
            action = 'store',
            type = 'str',
            dest = 'to',
            default = None,
            help = 'list of tag names that are to be used instead'
        ),
        make_option('--user-id',
            action = 'store',
            type = 'int',
            dest = 'user_id',
            default = None,
            help = 'id of the user who will be marked as a performer of this operation'
        ),
    )

    #@transaction.commit_manually
    def handle(self, *args, **options):
        """command handle function. reads tag names, decodes
        them using the standard input encoding and attempts to find
        the matching tags

        If "from" tags are not resolved, command fails
        if one of "to" tag is not resolved, a new tag is created

        The data of tag id's is then delegated to the command "rename_tag_id"
        """
        if options['from'] is None:
            raise CommandError('the --from argument is required')
        if options['to'] is None:
            raise CommandError('the --to argument is required')
        from_tag_names = parse_tag_names(options['from'])
        to_tag_names = parse_tag_names(options['to'])

        in_both = from_tag_names & to_tag_names
        if in_both:
            in_both_str = u' '.join(in_both)
            if len(in_both) > 1:
                error_message = 'Tags %s appear to be ' % in_both_str
            else:
                error_message = 'Tag %s appears to be ' % in_both_str
            raise CommandError(error_message + 'in both --from and --to sets')

        from_tags = list()
        try:
            for tag_name in from_tag_names:
                from_tags.append(models.Tag.objects.get(name = tag_name))
        except models.Tag.DoesNotExist:
            error_message = u"""tag %s was not found. It is possible that the tag
exists but we were not able to match it's unicode value
or you may have misspelled the tag. Please remember that
tag names are case sensitive.

Also, you can try command "rename_tag_id"
""" % tag_name
            raise CommandError(error_message)
        except models.Tag.MultipleObjectsReturned:
            raise CommandError(u'found more than one tag named %s' % from_tag_name)

        admin = get_admin(seed_user_id = options['user_id'])

        to_tags = list()
        for tag_name in to_tag_names:
            try:
                to_tags.append(models.Tag.objects.get(name = tag_name))
            except models.Tag.DoesNotExist:
                to_tags.append(
                    models.Tag.objects.create(
                                name = tag_name,
                                created_by = admin
                    )
                )
            except models.Tag.MultipleObjectsReturned:
                raise CommandError(u'found more than one tag named %s' % tag_name)
        options['user_id'] = admin.id
        options['from'] = format_tag_ids(from_tags)
        options['to'] = format_tag_ids(to_tags)

        management.call_command('rename_tags_id', *args, **options)

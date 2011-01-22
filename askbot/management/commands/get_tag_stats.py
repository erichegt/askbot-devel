import sys
import optparse
from django.core.management.base import BaseCommand, CommandError
from askbot import models

def get_tag_lines(tag_marks, width = 25):
    output = list()
    line = ''
    for mark in tag_marks:
        name = mark.tag.name
        if line == '':
            line = name
        elif len(line) + len(name) + 1 > width:
            output.append(line)
            line = name
        else:
            line += ' ' + name
    output.append(line)
    return output

def get_empty_lines(num_lines):
    output = list()
    for idx in xrange(num_lines):
        output.append('')
    return output

def pad_list(the_list, length):
    if len(the_list) < length:
        the_list.extend(get_empty_lines(length - len(the_list)))

def format_table_row(*cols, **kwargs):
    max_len = max(map(len, cols))
    for col in cols:
        pad_list(col, max_len)

    output = list()
    for idx in xrange(max_len):
        bits = list()
        for col in cols:
            bits.append(col[idx])
        line = kwargs['format_string'] % tuple(bits)
        output.append(line)

    return output


class Command(BaseCommand):
    help = """Dumps askbot forum data into the file for the later use with "load_forum".
The extension ".json" will be added automatically."""

    option_list = BaseCommand.option_list + (
            optparse.make_option(
                '-t',
                '--sub-counts',
                action = 'store_true',
                default = False,
                dest = 'sub_counts',
                help = 'Print tag subscription statistics, for all tags, listed alphabetically'
            ),
            optparse.make_option(
                '-u',
                '--user-sub-counts',
                action = 'store_true',
                default = False,
                dest = 'user_sub_counts',
                help = 'Print tag subscription data per user, with users listed alphabetically'
            ),
            optparse.make_option(
                '-e',
                '--print-empty',
                action = 'store_true',
                default = False,
                dest = 'print_empty',
                help = 'Print empty records too (with zero counts)'
            ),
        )
    def handle(self, *args, **options):
        if not(options['sub_counts'] ^ options['user_sub_counts']):
            raise CommandError('Please use either -u or -t (but not both)')

        print ''
        if options['sub_counts']:
            self.print_sub_counts(options['print_empty'])

        if options['user_sub_counts']:
            self.print_user_sub_counts(options['print_empty'])
        print ''

    def print_user_sub_counts(self, print_empty):
        """prints list of users and what tags they follow/ignore
        """
        users = models.User.objects.all().order_by('username')
        item_count = 0
        for user in users:
            tag_marks = user.tag_selections
            followed_tags = tag_marks.filter(reason='good')
            ignored_tags = tag_marks.filter(reason='bad')
            followed_count = followed_tags.count()
            ignored_count = ignored_tags.count()
            if followed_count == 0 and ignored_count == 0 and print_empty == False:
                continue
            if item_count == 0:
                print '%-28s %25s %25s' % ('User (id)', 'Interesting tags', 'Ignored tags')
                print '%-28s %25s %25s' % ('=========', '================', '============')
            followed_lines = get_tag_lines(followed_tags, width = 25)
            ignored_lines = get_tag_lines(ignored_tags, width = 25)
            user_string = '%s (%d)' % (user.username, user.id)
            output_lines = format_table_row(
                                [user.username,],
                                followed_lines,
                                ignored_lines,
                                format_string = '%-28s %25s %25s'
                            )
            item_count += 1
            for line in output_lines:
                print line
            print ''

        self.print_postamble(item_count)

    def print_sub_counts(self, print_empty):
        """prints subscription counts for
        each tag (ignored and favorite counts)
        """
        tags = models.Tag.objects.all().order_by('name')
        item_count = 0
        for tag in tags:
            tag_marks = tag.user_selections
            follow_count = tag_marks.filter(reason='good').count()
            ignore_count = tag_marks.filter(reason='bad').count()
            if follow_count + ignore_count == 0 and print_empty == False:
                continue
            if item_count == 0:
                print '%-32s %12s %12s' % ('Tag name', 'Interesting', 'Ignored')
                print '%-32s %12s %12s' % ('========', '===========', '=======')
            print '%-32s %12d %12d' % (tag.name, follow_count, ignore_count)
            item_count += 1

        self.print_postamble(item_count)

    def print_postamble(self, item_count):
        print ''
        if item_count == 0:
            print 'Did not find anything'
        else:
            print '%d records shown' % item_count
        print 'Since -e option was not selected, empty records were hidden'

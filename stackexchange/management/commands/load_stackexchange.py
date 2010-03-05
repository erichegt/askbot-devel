from django.core.management.base import BaseCommand
import os
import sys
import stackexchange.parse_models as se_parser
from xml.etree import ElementTree as et
from django.db import models

xml_read_order = (
        'VoteTypes','UserTypes','Users','Users2Votes',
        'Badges','Users2Badges','CloseReasons','FlatPages',
        'MessageTypes','PostHistoryTypes','PostTypes','SchemaVersion',
        'Settings','SystemMessages','ThemeResources','ThemeTextResources',
        'ThrottleBucket','UserHistoryTypes','UserHistory',
        'Users2Badges','VoteTypes','Users2Votes','MessageTypes',
        'Posts','Posts2Votes','PostHistory','PostComments',
        'ModeratorMessages','Messages','Comments2Votes',
        )


class Command(BaseCommand):
    help = 'Loads StackExchange data from unzipped directory of XML files into the OSQA database'
    args = 'se_dump_dir'

    def handle(self, *arg, **kwarg):
        if len(arg) < 1 or not os.path.isdir(arg[0]):
            print 'Error: first argument must be a directory with all the SE *.xml files'
            sys.exit(1)

        self.dump_path = arg[0]
        for xml in xml_read_order:
            xml_path = self.get_xml_path(xml)
            table_name = self.get_table_name(xml)
            self.load_xml_file(xml_path, table_name)

    def load_xml_file(self, xml_path, table_name):
        tree = et.parse(xml_path)
        print 'loading from %s to %s' % (xml_path, table_name) ,
        model = models.get_model('stackexchange', table_name)
        i = 0
        for row in tree.findall('.//row'):
            model_entry = model()
            i += 1
            for col in row.getchildren():
                field_name = se_parser.parse_field_name(col.tag)
                field_type = model._meta.get_field(field_name)
                field_value = se_parser.parse_value(col.text, field_type)
                setattr(model_entry, field_name, field_value)
            model_entry.save()
        print '... %d objects saved' % i

    def get_table_name(self,xml):
        return se_parser.get_table_name(xml)

    def get_xml_path(self, xml):
        xml_path = os.path.join(self.dump_path, xml + '.xml') 
        if not os.path.isfile(xml_path):
            print 'Error: file %s not found' % xml_path
            sys.exit(1)
        return xml_path

from xml.etree import ElementTree as et
import sys
import re

types = {
   'unsignedByte':'models.IntegerField',
   'FK':'models.ForeignKey',
   'string':'models.CharField',
   'text':'models.TextField',
   'int':'models.IntegerField',
   'boolean':'models.BooleanField',
   'dateTime':'models.DateTimeField',
   'base64Binary':'models.TextField',
   'double':'models.IntegerField',
}

def camel_to_python(camel):
    """http://stackoverflow.com/questions/1175208/
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def singular(word):
    if word.endswith('s'):
        return word[:-1]
    else:
        return word

class DjangoModel(object):
    def __init__(self, name):
        self.name = 'StackExchange'
        if name.find('2') == -1:
            self.name += singular(name)
        else:
            bits = name.split('2')
            bits = map(singular, bits)
            self.name += '2'.join(bits) 
        self.fields = []
    def add_field(self,field):
        field.table = self
        self.fields.append(field)
    def __str__(self):
        out = 'class %s(models.Model):\n' % self.name
        for f in self.fields:
            out += '    %s\n' % str(f)
        return out

class DjangoField(object):
    def __init__(self, name, type, restriction = None):
        self.name = camel_to_python(name)
        if self.name == 'class':
            self.name = 'class_type'#work around python keyword
        self.type = type
        self.table = None
        self.restriction = restriction
        self.relation = None

    def __str__(self):
        out  = '%s = %s(' % (self.name, types[self.type])
        if self.relation and self.restriction:
            raise Exception('impossible')
        elif self.relation:
            out += "'%s'" % self.relation  
            out += ", related_name='%s_%s_set'" % (self.table.name, self.name)
            out += ', null=True'#nullable to make life easier
        elif self.restriction != -1:
            if self.type == 'string':
                out += 'max_length=%s' % self.restriction
            else:
                raise Exception('only max_length restriction is supported')
        out += ')'
        return out

class DjangoFK(DjangoField):
    def __init__(self, source_name):
        bits = source_name.split('Id')
        if len(bits) == 2 and bits[1] == '':
            name = bits[0]
        super(DjangoFK, self).__init__(name, 'FK')
        self.set_relation(name)

    def set_relation(self, name):
        """some relations need to be mapped 
        to actual tables
        """
        self.relation = 'StackExchange'
        if name.endswith('User'):
            self.relation += 'User'
        elif name.endswith('Post'):
            self.relation += 'Post'
        elif name in ('AcceptedAnswer','Parent'):
            self.relation = 'self' #self-referential Post model
        else:
            self.relation += name

def get_col_type(col):
    type = col.get('type')
    restriction = -1
    if type == None:
        type_e = col.find('.//simpleType/restriction')
        type = type_e.get('base')
        try:
            restriction = int(type_e.getchildren()[0].get('value'))
        except:
            restriction = -1 
        if restriction > 400:
            type = 'text'
            restriction = -1
    return type, restriction

print 'from django.db import models'
for file in sys.argv:
    if '.xsd' in file:
        tname = file.replace('.xsd','')
        tree = et.parse(file)

        model = DjangoModel(tname)

        row = tree.find('.//sequence')
        for col in row.getchildren():
            name = col.get('name')
            if name in ('Id', 'LinkedVoteId'):#second one is not used
                continue
            elif name.endswith('Id') and name not in ('OpenId','PasswordId'):
                field = DjangoFK(name)
            elif name.endswith('GUID'):
                field = DjangoField(name, 'string', 64)
            else:
                type, restriction = get_col_type(col)
                field = DjangoField(name, type, restriction)
            model.add_field(field)
        print model

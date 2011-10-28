from django.core.management.base import NoArgsCommand
from django.db.models import get_model
from django.contrib.auth.models import User


class Command(NoArgsCommand):
  def find_relations(self, **options):
    rel = User._meta.get_all_related_objects()
    print 'simple:'
    for r in rel:
        print r.model, r.field.name
    print 'm2m:'
    rel_m2m = User._meta.get_all_related_many_to_many_objects()
    for r in rel_m2m:
      print r.model, r.field.name

  def handle_noargs(self, **options):
    from_id = 2 
    to_id = 1 

    self.from_user = User.objects.get(id = from_id)
    self.to_user = User.objects.get(id = to_id)

    # Process all foreign key Relationships
    for rel in User._meta.get_all_related_objects():
      try:
        self.process_field(rel.model, rel.field.name)
      except:
        if rel.field.name == 'UserAssociation':
          print 'had problem with UserAssociation uniquiness'
        elif rel.field.name == 'UserPasswordQueue':
          print 'had problem with UserPasswordQueue uniquiness'

    #Get all the many_to_many items
    #import ipdb; ipdb.set_trace()
    for rel in User._meta.get_all_related_many_to_many_objects():
      self.process_m2m_field(rel.model, rel.field.name)
           

    self.to_user.reputation += self.from_user.reputation - 1
    self.to_user.gold += self.from_user.gold
    self.to_user.silver += self.from_user.silver
    self.to_user.bronze += self.from_user.bronze

    if self.from_user.last_seen > self.to_user.last_seen:
      self.to_user.last_seen = self.from_user.last_seen

    if self.from_user.date_joined < self.to_user.date_joined:
      self.to_user.date_joined = self.from_user.date_joined

    self.to_user.save()

    self.from_user.delete()

  def process_field(self, model, field_name):
    filter_condition = {field_name: self.from_user}
    related_objects_qs = model.objects.filter(**filter_condition)
    update_condition = {field_name: self.to_user}
    related_objects_qs.update(**update_condition)

  def process_m2m_field(self, model, field_name):
    filter_condition = {field_name: self.from_user}
    related_objects_qs = model.objects.filter(**filter_condition)
    for obj in related_objects_qs:
      m2m_field = getattr(obj, field_name)
      m2m_field.remove(self.from_user)
      m2m_field.add(self.to_user)

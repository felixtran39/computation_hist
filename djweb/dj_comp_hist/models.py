from django.db import models
from django.db.models.signals import  post_save
import csv

# Create your models here.


class Organization(models.Model):
    location = models.CharField(max_length=191, blank=True)
    name = models.CharField(max_length=191, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "No name"

    def __repr__(self):
        if self.name:
            return f"<Organization {self.name}>"
        else:
            return f"<Organization without a name>"



class Box(models.Model):
    number = models.IntegerField(default=0)

    def __str__(self):
        return str(self.number)

    def __repr__(self):
        return f"<Box {self.number}>"


class Person(models.Model):
    first = models.CharField(max_length=191, blank=True)
    last = models.CharField(max_length=191, blank=True)
    organization = models.ManyToManyField(Organization, blank=True)

    def __str__(self):
        if self.last and self.first:

            return self.last + ' ' + self.first[0]

        elif self.last:
            return self.last
        elif self.first:
            return self.first
        else:
            return "No name"

    def __repr__(self):
        if self.last and self.first:
            return f"<Person {self.last}, {str(self.first)[0]}>"
        elif self.last:
            return f"<Person {self.last}>"
        elif self.first:
            return f"<Person {self.first}>"
        else:
            return f"<Person without a name>"


class Folder(models.Model):
    name = models.CharField(max_length=191)
    box = models.ForeignKey(Box, on_delete=models.CASCADE)
    full = models.CharField(max_length=191)
    number = models.IntegerField(default=0)

    def __str__(self):
        return self.full

    def __repr__(self):
        return f"<Folder {self.full} - {self.number}>"


class Document(models.Model):
    author_person = models.ManyToManyField(Person, related_name='author_person', blank=True)
    author_organization = models.ManyToManyField(Organization,
                                                 related_name='author_organization', blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    title = models.CharField(max_length=191)
    type = models.CharField(max_length=191, blank=True)
    # TODO: turn type into choices- note that choices needs to be able to grow
    number_of_pages = models.IntegerField(default=1)
    date = models.DateField(auto_now_add=False, auto_now=False, blank=True)
    recipient_person = models.ManyToManyField(Person, related_name='recipient_person', blank=True)
    recipient_organization = models.ManyToManyField(Organization,
                                                    related_name='recipient_organization',
                                                    blank=True)
    cced_person = models.ManyToManyField(Person, related_name='cced_person', blank=True)
    cced_organization = models.ManyToManyField(Organization, related_name='cced_organization',
                                               blank=True)
    notes = models.CharField(max_length=191, blank=True)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Document {self.title}>"


class Page(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    page_number = models.IntegerField(default=0)
    file_name = models.CharField(max_length=191)

    def __str__(self):
        return "Page " + str(self.page_number) + " of " + str(self.document)

    def __repr__(self):
        return f"<Page {self.page_number} of {self.document}"


class Text(models.Model):
    page = models.OneToOneField(Page, on_delete=models.SET(None), blank=True)


def check_generate(model, key, value):
    if model.objects.filter(**{key: value}):
        existed = True
        new_item = model.objects.get(**{key: value})

    else:
        new_item = model(**{key: value})
        existed = False
    return existed, new_item

def check_person_known(person):
    if person.first == "unknown":
        person.first = None
    if person.last == "unknown":
        person.first = None
    return person


def interpret_person_organization(field, item_organization, item_person, new_doc):
    #Creates list of authors
    field_split = field.split('; ')
    #Checks if it is an organizatio

    for person_or_organization in field_split:
        if len(person_or_organization.split(', ')) == 1:
            org_exist, new_org = check_generate(Organization, "name", field_split[0])
            new_org.save()
            bound_attr = getattr(new_doc, item_organization)
            bound_attr.add(Organization.objects.get(name=field_split[0]))
        else:
            item_current = person_or_organization.split(', ')
            item_exist, new_item = check_generate(Person, "last", item_current[0])
            check_person_known(new_item)
            # TODO change check_generate to have more than one key for people with the
            # same last name
            if not item_exist:
                new_item.first = item_current[1]
            new_item.save()
            bound_attr = getattr(new_doc, item_person)
            bound_attr.add(Person.objects.get(last=item_current[0]))


def populate_from_metadata(file_name):
    with open(file_name) as file:
        csv_file = csv.DictReader(file)
        for line in csv_file:
            new_doc = Document(number_of_pages=int(line['last_page']) - int(line['first_page']) + 1,
                               title=line['title'], type=line['doc_type'], notes=line['notes'])

            # ---------------------DATE-----------------------------------------------
            if line['date'] != '' or line['date'][0] == '1':
                new_doc.date = line['date']

            # ------------------------------------------------------------------------

            # ---------------------Folder---------------------------------------------
            folder_exist,new_folder = check_generate(Folder, "name" ,line['foldername_short'])
            if not folder_exist:
                box_exist,new_box = check_generate(Box, "number" , line['box'])
                new_box.save()
                new_folder.box = new_box
                new_folder.number = line['folder_number']
                new_folder.full = line['foldername_full']
            new_folder.save()
            new_doc.folder = new_folder
            new_doc.save()

            # -----------------------Author, Recipient,cced--------------------------
            interpret_person_organization(line['author'], "author_organization", "author_person", new_doc)
            interpret_person_organization(line['recipients'], "recipient_organization",
                                          "recipient_person",
                                          new_doc)
            interpret_person_organization(line['cced'], "cced_organization", "cced_person",
                                          new_doc)


            new_doc.save()

            # ------------------------pages,
            for i in range(1, new_doc.number_of_pages+1):
                new_page = Page(document = new_doc, file_name = line['filename'], page_number = i)
                new_page.save()

            print(new_doc)
            print(new_doc.author_person, new_doc.author_organization)




        return
"""
@reciever(post_save, sender=Document)

def create_pages(sender, instance, created, **kwargs):
    for i in range(1, instance.number_of_pages + 1):
        new_page = Page(document=instance, file_name=line['filename'], page_number=i)
        new_page.save(

"""
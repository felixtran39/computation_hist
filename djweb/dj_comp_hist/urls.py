from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(r'person/<int:person_id>', views.person, name='person'),
    path('doc/<int:doc_id>', views.doc, name='document'),
    path('box/<int:box_id>', views.box, name='box'),
    path('folder/<int:folder_id>', views.folder, name='folder'),
    path('organization/<int:org_id>', views.organization, name='organization'),

    # Todo: Slugify at a much later time?
    path('list/<str:model_str>', views.list, name='list')
]
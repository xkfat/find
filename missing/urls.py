from django.urls import path
from .views import missing_person_detail, missing_person_list


urlpatterns = [
    path('cases/', missing_person_list, name='missing-persons-list'),
    path('cases/<int:id>/', missing_person_detail, name='missing-person-detail'),

    
]

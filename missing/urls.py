from django.urls import path
from .views import missing_person_detail, missing_person_list


urlpatterns = [
    path('', missing_person_list, name='missing-persons-cases-list'),
    path('<int:pk>/', missing_person_detail, name='missing-person-case-detail'),

]

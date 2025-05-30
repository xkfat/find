from django.urls import path
from .views import missing_person_detail, missing_person_list, user_submitted_cases, case_updates, add_case_update, case_detail_with_updates


urlpatterns = [
    path('', missing_person_list, name='missing-persons-cases-list'),
    path('submitted-cases/', user_submitted_cases, name='my-submitted-cases'),
    path('<int:pk>/updates/', case_updates, name='case-updates'),
    path('<int:pk>/add-update/', add_case_update, name='add-case-update'),
    path('<int:case_id>/with-updates/', case_detail_with_updates, name='case-detail-with-updates'),
    path('<int:pk>/', missing_person_detail, name='missing-person-case-detail'),

]

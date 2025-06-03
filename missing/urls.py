from django.urls import path
from .views import (
    missing_person_detail, 
    missing_person_list, 
    user_submitted_cases, 
    case_updates, 
    add_case_update, 
    case_detail_with_updates,
    get_cases_for_updates,
    
)
from .dashboard_views import DashboardActivityView, DashboardStatsView


urlpatterns = [
    path('', missing_person_list, name='missing-persons-cases-list'),
    path('submitted-cases/', user_submitted_cases, name='my-submitted-cases'),
    path('<int:case_id>/updates/', case_updates, name='case-updates'),
    path('<int:case_id>/add-update/', add_case_update, name='add-case-update'),
    path('<int:case_id>/with-updates/', case_detail_with_updates, name='case-detail-with-updates'),
    path('<int:pk>/', missing_person_detail, name='missing-person-case-detail'),
    path('for-updates/', get_cases_for_updates, name='cases-for-updates'),  # New endpoint

    path('dashboard/activity/', DashboardActivityView.as_view(), name='dashboard-activity'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
from django.urls import path
from .views import submit_report, list_reports, report_detail , update_report_status

urlpatterns = [
path('submit/', submit_report, name='submit-report'),  
path('', list_reports, name='list-reports'),
path('<int:id>/', report_detail, name='report-detail') ,
path('admin/reports/<int:report_id>/update-status/', update_report_status, name='update-report-status')

]
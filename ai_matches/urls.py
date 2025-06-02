from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_ai_matches, name='ai-matches-list'),
    path('stats/', views.ai_match_stats, name='ai-matches-stats'),
    path('<int:match_id>/', views.ai_match_detail, name='ai-match-detail'),
    path('<int:match_id>/review/', views.review_ai_match, name='ai-match-review'),
]
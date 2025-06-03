# Create this file: missing/dashboard_views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

class DashboardActivityView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """
        Combined recent activity endpoint for dashboard
        Returns recent cases, reports, and AI matches in a unified format
        """
        try:
            activities = []
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # Get recent cases
            from missing.models import MissingPerson
            recent_cases = MissingPerson.objects.filter(
                date_reported__gte=thirty_days_ago
            ).order_by('-date_reported')[:3]  # Reduced from 8 to 3
            
            for case in recent_cases:
                activities.append({
                    'id': f'case-{case.id}',
                    'type': 'case_created',
                    'title': f'New case submitted: {case.first_name} {case.last_name}',
                    'subtitle': 'AI scan initiated',
                    'timestamp': case.date_reported.isoformat(),
                    'status': case.status,
                    'icon': 'user',
                    'color': 'blue',
                    'case_id': case.id
                })
                
                # Add status change activities for found/investigating cases
                if case.status == 'found':
                    activities.append({
                        'id': f'case-found-{case.id}',
                        'type': 'case_found',
                        'title': f'Case resolved: {case.first_name} {case.last_name} → Found',
                        'subtitle': 'Case successfully closed',
                        'timestamp': case.date_reported.isoformat(),
                        'status': case.status,
                        'icon': 'check',
                        'color': 'green',
                        'case_id': case.id
                    })
                elif case.status == 'under_investigation':
                    activities.append({
                        'id': f'case-investigation-{case.id}',
                        'type': 'case_investigation',
                        'title': f'Case under investigation: {case.first_name} {case.last_name}',
                        'subtitle': 'Status updated by admin',
                        'timestamp': case.date_reported.isoformat(),
                        'status': case.status,
                        'icon': 'search',
                        'color': 'yellow',
                        'case_id': case.id
                    })
            
            # Get recent reports
            from reports.models import Report
            recent_reports = Report.objects.filter(
                date_submitted__gte=thirty_days_ago
            ).select_related('missing_person').order_by('-date_submitted')[:2]  # Reduced from 6 to 2
            
            for report in recent_reports:
                activities.append({
                    'id': f'report-{report.id}',
                    'type': 'report_submitted',
                    'title': f'New report submitted for {report.missing_person.first_name} {report.missing_person.last_name}',
                    'subtitle': self._get_report_subtitle(report.report_status),
                    'timestamp': report.date_submitted.isoformat(),
                    'status': report.report_status,
                    'icon': 'document',
                    'color': self._get_report_color(report.report_status),
                    'report_id': report.id,
                    'case_id': report.missing_person.id
                })
            
            # Get recent AI matches
            try:
                from ai_matches.models import AIMatch
                recent_ai_matches = AIMatch.objects.filter(
                    processing_date__gte=thirty_days_ago
                ).select_related('original_case', 'matched_case').order_by('-processing_date')[:2]  # Reduced from 6 to 2
                
                for match in recent_ai_matches:
                    # AI match found activity
                    confidence_level = match.confidence_level
                    if match.status == 'pending':
                        activities.append({
                            'id': f'ai-match-{match.id}',
                            'type': 'ai_match_found',
                            'title': f'AI found potential match ({match.confidence_score}% confidence)',
                            'subtitle': f'High confidence match for {match.original_case.first_name} {match.original_case.last_name}' if confidence_level == 'high' else f'Match found for {match.original_case.first_name} {match.original_case.last_name}',
                            'timestamp': match.processing_date.isoformat(),
                            'status': match.status,
                            'icon': 'ai',
                            'color': 'purple' if confidence_level == 'high' else 'blue',
                            'match_id': match.id,
                            'case_id': match.original_case.id,
                            'confidence': match.confidence_score
                        })
                    elif match.status == 'confirmed':
                        activities.append({
                            'id': f'ai-match-confirmed-{match.id}',
                            'type': 'ai_match_confirmed',
                            'title': f'AI match confirmed: {match.original_case.first_name} {match.original_case.last_name} → Found',
                            'subtitle': f'Match verified by {match.reviewed_by.username if match.reviewed_by else "admin"}',
                            'timestamp': match.review_date.isoformat() if match.review_date else match.processing_date.isoformat(),
                            'status': match.status,
                            'icon': 'check',
                            'color': 'green',
                            'match_id': match.id,
                            'case_id': match.original_case.id
                        })
                        
            except ImportError:
                print("ai_matches app not available")
            
            # Sort all activities by timestamp (most recent first) and limit to 5
            sorted_activities = sorted(
                activities, 
                key=lambda x: x['timestamp'], 
                reverse=True
            )[:5]  # Changed from 15 to 5
            
            return Response({
                'activities': sorted_activities,
                'count': len(sorted_activities),
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch dashboard activities: {str(e)}',
                'activities': [],
                'count': 0
            }, status=500)
    
    def _get_report_subtitle(self, status):
        """Helper method to get report subtitle based on status"""
        status_map = {
            'new': 'Awaiting review',
            'verified': 'Report verified',
            'unverified': 'Needs verification', 
            'false': 'Marked as false report'
        }
        return status_map.get(status, 'Report submitted')
    
    def _get_report_color(self, status):
        """Helper method to get color based on report status"""
        color_map = {
            'new': 'blue',
            'verified': 'green',
            'unverified': 'orange',
            'false': 'red'
        }
        return color_map.get(status, 'gray')


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Get comprehensive dashboard statistics"""
        try:
            from missing.models import MissingPerson
            from reports.models import Report
            
            # Basic statistics
            total_cases = MissingPerson.objects.count()
            active_cases = MissingPerson.objects.filter(submission_status='active').count()
            pending_cases = MissingPerson.objects.filter(submission_status='in_progress').count()  # Fixed: now correctly uses submission_status
            found_cases = MissingPerson.objects.filter(status='found').count()
            
            total_reports = Report.objects.count()
            unverified_reports = Report.objects.filter(report_status='unverified').count()  # Fixed: now correctly uses report_status
            verified_reports = Report.objects.filter(report_status='verified').count()
            
            # AI Matches statistics
            ai_stats = {'total_matches': 0, 'pending_reviews': 0, 'confirmed_matches': 0, 'false_positives': 0}
            try:
                from ai_matches.models import AIMatch
                ai_stats = {
                    'total_matches': AIMatch.objects.count(),
                    'pending_reviews': AIMatch.objects.filter(status='pending').count(),
                    'confirmed_matches': AIMatch.objects.filter(status='confirmed').count(),
                    'false_positives': AIMatch.objects.filter(status='rejected').count(),
                }
            except ImportError:
                pass
            
            return Response({
                'total_cases': total_cases,
                'active_cases': active_cases,
                'pending_cases': pending_cases,  # Cases with submission_status = 'in_progress'
                'found_cases': found_cases,
                'unverified_reports': unverified_reports,  # Reports with report_status = 'unverified'
                'verified_reports': verified_reports,
                'total_reports': total_reports,
                'ai_matches': ai_stats['total_matches'],
                'ai_pending_reviews': ai_stats['pending_reviews'],
                'ai_confirmed_matches': ai_stats['confirmed_matches'],
                'ai_false_positives': ai_stats['false_positives'],
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch dashboard stats: {str(e)}'
            }, status=500)
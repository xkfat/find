from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import AIMatch
from .serializers import AIMatchSerializer, AIMatchActionSerializer

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_ai_matches(request):
    """List all AI matches with filtering options"""
    queryset = AIMatch.objects.select_related(
        'original_case', 'matched_case', 'reviewed_by'
    ).prefetch_related(
        'original_case__updates', 'matched_case__updates'
    )
    
    # Filters
    status_filter = request.GET.get('status')
    confidence_filter = request.GET.get('confidence')
    search = request.GET.get('search')
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if confidence_filter:
        if confidence_filter == 'high':
            queryset = queryset.filter(confidence_score__gte=90)
        elif confidence_filter == 'medium':
            queryset = queryset.filter(confidence_score__gte=45, confidence_score__lt=90)  # Updated threshold
        elif confidence_filter == 'low':
            queryset = queryset.filter(confidence_score__lt=45)  # Updated threshold
    
    if search:
        queryset = queryset.filter(
            Q(original_case__first_name__icontains=search) |
            Q(original_case__last_name__icontains=search) |
            Q(matched_case__first_name__icontains=search) |
            Q(matched_case__last_name__icontains=search) |
            Q(id__icontains=search)
        )
    
    serializer = AIMatchSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def ai_match_detail(request, match_id):
    """Get detailed information about a specific AI match"""
    match = get_object_or_404(AIMatch, id=match_id)
    serializer = AIMatchSerializer(match, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def review_ai_match(request, match_id):
    """Confirm, reject, or change status of AI match - allows all status transitions"""
    match = get_object_or_404(AIMatch, id=match_id)
    
    # REMOVED: Allow any status to change to any other status for full flexibility
    # Old restrictive code was:
    # if match.status not in ['pending', 'under_review']:
    #     return Response({'error': 'This match has already been finalized'}, 
    #                    status=status.HTTP_400_BAD_REQUEST)
    
    serializer = AIMatchActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    action = serializer.validated_data['action']
    admin_notes = serializer.validated_data.get('admin_notes', '')
    
    # Store old status for logging and response
    old_status = match.status
    
    if action == 'confirm':
        match.confirm_match(request.user, admin_notes)
        message = f"Match confirmed. Case #{match.original_case.id} marked as found."
    elif action == 'reject':
        match.reject_match(request.user, admin_notes)
        message = f"Match rejected and marked as false positive."
    elif action == 'under_review':
        match.status = 'under_review'
        match.reviewed_by = request.user
        match.review_date = timezone.now()
        match.admin_notes = admin_notes
        match.save()
        message = f"Match set to under review for further investigation."
    elif action == 'pending':
        # NEW: Allow resetting to pending status
        match.status = 'pending'
        match.reviewed_by = request.user
        match.review_date = timezone.now()
        match.admin_notes = admin_notes
        # Note: Don't change original case status when resetting to pending
        match.save()
        message = f"Match reset to pending review status."
    else:
        return Response(
            {'error': 'Invalid action. Must be confirm, reject, under_review, or pending'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Log the status change for audit purposes
    print(f"AI Match {match.id} status changed: {old_status} → {match.status} by {request.user.username}")
    
    # Return updated match data
    updated_serializer = AIMatchSerializer(match, context={'request': request})
    return Response({
        'message': message,
        'match': updated_serializer.data,
        'status_change': {
            'from': old_status,
            'to': match.status,
            'changed_by': request.user.username,
            'timestamp': timezone.now().isoformat()
        }
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def ai_match_stats(request):
    """Get AI matching statistics"""
    total_matches = AIMatch.objects.count()
    pending_matches = AIMatch.objects.filter(status='pending').count()
    confirmed_matches = AIMatch.objects.filter(status='confirmed').count()
    rejected_matches = AIMatch.objects.filter(status='rejected').count()
    under_review_matches = AIMatch.objects.filter(status='under_review').count()
    
    # Today's statistics
    from django.utils import timezone
    today = timezone.now().date()
    today_matches = AIMatch.objects.filter(processing_date__date=today).count()
    
    # High confidence pending matches
    high_confidence_pending = AIMatch.objects.filter(
        status='pending', 
        confidence_score__gte=90
    ).count()
    
    return Response({
        'total_matches': total_matches,
        'pending_reviews': pending_matches,
        'confirmed_matches': confirmed_matches,
        'rejected_matches': rejected_matches,
        'under_review_matches': under_review_matches,  # Added this
        'scans_today': today_matches,
        'high_confidence_pending': high_confidence_pending,
        'false_positives': rejected_matches,  # For compatibility with frontend
    })

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_ai_match(request, match_id):
    """Delete an AI match permanently"""
    match = get_object_or_404(AIMatch, id=match_id)
    
    # Optional: Log the deletion for audit purposes
    print(f"Admin {request.user.username} deleted AI match {match.id}: "
          f"{match.original_case.full_name} → {match.matched_case.full_name}")
    
    match.delete()
    return Response(
        {'message': 'AI match deleted successfully'}, 
        status=status.HTTP_204_NO_CONTENT
    )
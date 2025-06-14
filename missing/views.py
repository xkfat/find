from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from django.db.models import Count, Q
from django.conf import settings
from django.db import models
from .serializers import MissingPersonSerializer, CaseUpdateSerializer, SubmittedCaseListSerializer, CaseUpdateCreateSerializer
from .models import MissingPerson, CaseUpdate
from .filters import MissingPersonFilter
import cv2
import numpy as np
import os


def auto_face_match_on_creation(new_person):
    """Automatically check for face matches when a new case is created and store them"""
    try:
        # Import here to avoid circular imports
        from ai_matches.models import AIMatch
        import face_recognition
        
        if not new_person.photo:
            print(f"No photo for {new_person.full_name}, skipping AI matching")
            return []
        
        new_image_path = os.path.join(settings.MEDIA_ROOT, str(new_person.photo))
        
        if not os.path.exists(new_image_path):
            print(f"Image file not found: {new_image_path}")
            return []
        
        existing_persons = MissingPerson.objects.filter(
            photo__isnull=False,
            gender=new_person.gender
        ).exclude(id=new_person.id)
        
        if not existing_persons.exists():
            print(f"No existing cases with same gender ({new_person.gender}) to compare")
            return []
        
        # Load and process new person's image
        try:
            new_img = cv2.imread(new_image_path)
            if new_img is None:
                print(f"Could not load image: {new_image_path}")
                return []
                
            new_img_rgb = cv2.cvtColor(new_img, cv2.COLOR_BGR2RGB)
            new_encodings = face_recognition.face_encodings(new_img_rgb)
            
            if len(new_encodings) == 0:
                print(f"No face detected in {new_person.full_name}'s image")
                return []
            
            new_encoding = new_encodings[0]
            print(f"Face encoding created for {new_person.full_name}")
            
        except Exception as e:
            print(f"Error processing new person's image: {e}")
            return []
        
        matches_found = []
        processed_count = 0
        
        for person in existing_persons:
            try:
                existing_image_path = os.path.join(settings.MEDIA_ROOT, str(person.photo))
                if not os.path.exists(existing_image_path):
                    continue
                    
                existing_img = cv2.imread(existing_image_path)
                if existing_img is None:
                    continue
                    
                existing_img_rgb = cv2.cvtColor(existing_img, cv2.COLOR_BGR2RGB)
                existing_encodings = face_recognition.face_encodings(existing_img_rgb)
                
                if len(existing_encodings) > 0:
                    existing_encoding = existing_encodings[0]
                    
                    distance = face_recognition.face_distance([existing_encoding], new_encoding)[0]
                    similarity = max(0, (1 - distance) * 100)
                    
                    processed_count += 1
                    
                    if similarity >= 40:  # Minimum threshold
                        # Check if match already exists
                        existing_match = AIMatch.objects.filter(
                            original_case=new_person,
                            matched_case=person
                        ).first()
                        
                        if not existing_match:
                            # Create AIMatch record
                            ai_match = AIMatch.objects.create(
                                original_case=new_person,
                                matched_case=person,
                                confidence_score=round(similarity, 1),
                                face_distance=distance,
                                algorithm_used='face_recognition',
                                status='pending'
                            )
                            
                            matches_found.append({
                                'ai_match_id': ai_match.id,
                                'person_id': person.id,
                                'person_name': person.full_name,
                                'similarity_percentage': round(similarity, 1),
                                'status': 'pending',
                                'photo_url': person.photo.url if person.photo else None,
                                'confidence_level': ai_match.confidence_level
                            })
                            
                            print(f"AI Match created: {new_person.full_name} → {person.full_name} ({similarity:.1f}%) [ID: {ai_match.id}]")
                        else:
                            print(f"AI Match already exists: {new_person.full_name} → {person.full_name}")
        
            except Exception as e:
                print(f"Error comparing {new_person.full_name} with {person.full_name}: {e}")
                continue
        
        print(f"AI Processing complete for {new_person.full_name}: {processed_count} comparisons, {len(matches_found)} matches found")
        matches_found.sort(key=lambda x: x['similarity_percentage'], reverse=True)
        return matches_found
        
    except ImportError:
        print("ai_matches app not available, skipping AI match storage")
        return []
    except Exception as e:
        print(f"Error in auto face matching: {e}")
        return []


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def missing_person_list(request):
    if request.method == 'GET':
        queryset = MissingPerson.objects.select_related('reporter').prefetch_related('updates').order_by('-date_reported')
        filtered_qs = MissingPersonFilter(request.GET, queryset=queryset).qs
        
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(filtered_qs, request)

        serializer = MissingPersonSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = MissingPersonSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Create the missing person - this will trigger the signal
        new_person = serializer.save()
        print(f"✅ New missing person case created: {new_person.full_name} (ID: {new_person.id})")
        
        # Prepare response data with success message
        response_data = serializer.data
        response_data['message'] = f"Missing person case for {new_person.full_name} has been successfully created."
        
        # Check if photo exists for AI processing feedback
        if new_person.photo:
            response_data['ai_processing'] = {
                'status': 'initiated',
                'message': 'AI face matching has been started in the background. You will be notified if any matches are found.',
                'note': 'This process may take a few minutes depending on the number of existing cases.'
            }
        else:
            response_data['ai_processing'] = {
                'status': 'skipped',
                'message': 'No photo provided - AI face matching skipped.',
                'note': 'Upload a photo later to enable face matching capabilities.'
            }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
@parser_classes([MultiPartParser, JSONParser, FormParser])
def missing_person_detail(request, pk):
    missing = get_object_or_404(MissingPerson, pk=pk)

    if request.method == 'GET':
        serializer = MissingPersonSerializer(missing, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH', 'DELETE']:
        if not request.user.is_staff:
            return Response({'error': 'Only admins can update or delete'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'PATCH':
            serializer = MissingPersonSerializer(missing, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            old_photo = missing.photo
            updated_person = serializer.save()
            
            # If photo was added or changed, trigger AI matching via signal
            # Note: The signal will handle this automatically when the instance is saved
            if updated_person.photo and (not old_photo or str(updated_person.photo) != str(old_photo)):
                print(f"🔄 Photo updated for {updated_person.full_name}")
                # The post_save signal will handle the AI processing
            
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            missing.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_submitted_cases(request):
    qs = MissingPerson.objects.filter(reporter=request.user).order_by('-date_reported')
    serializer = SubmittedCaseListSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def case_updates(request, pk):
    case = get_object_or_404(MissingPerson, pk=pk)

    if case.reporter != request.user and not request.user.is_staff:
        return Response(
            {'error': 'You do not have permission to view updates for this case'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    updates = CaseUpdate.objects.filter(case=case)
    serializer = CaseUpdateSerializer(updates, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_case_update(request, case_id):
    """
    Enhanced case update endpoint that handles both manual and auto updates
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff can add updates to cases'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    case = get_object_or_404(MissingPerson, pk=case_id)
    
    # Check if case has a reporter
    if not case.reporter:
        return Response(
            {'error': 'Cannot send update - case has no reporter'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = CaseUpdateCreateSerializer(data=request.data, context={'case_id': case_id})

    if serializer.is_valid():
        # Create the case update
        update = serializer.save()
        
        # Update submission status if provided
        if 'submission_status' in request.data:
            old_status = case.submission_status
            new_status = request.data['submission_status']
            case.submission_status = new_status
            case.save()
            
            # Send notification about status change
            try:
                from notifications.signals import send_notification
                
                status_message = f"Your case status has been updated from '{old_status.replace('_', ' ').title()}' to '{new_status.replace('_', ' ').title()}'."
                
                send_notification(
                    users=[case.reporter],
                    message=status_message,
                    target_instance=case,
                    notification_type='case_update',
                    push_title="Case Status Update",
                    push_data={
                        'case_id': str(case.id),
                        'person_name': case.full_name,
                        'old_status': old_status,
                        'new_status': new_status,
                        'action': 'view_case'
                    }
                )
            except Exception as e:
                print(f"Error sending status change notification: {e}")
        
        # Send notification about the case update
        try:
            from notifications.signals import send_notification
            
            update_message = f"New update for {case.full_name}: {update.message}"
            
            send_notification(
                users=[case.reporter],
                message=update_message,
                target_instance=update,
                notification_type='case_update',
                push_title="Case Update",
                push_body=f"Update for {case.full_name}",
                push_data={
                    'case_id': str(case.id),
                    'person_name': case.full_name,
                    'update_id': str(update.id),
                    'action': 'view_update'
                }
            )
            
            print(f"✅ Case update notification sent to {case.reporter.username} for case {case.id}")
            
        except Exception as e:
            print(f"❌ Error sending case update notification: {e}")

        # Prepare response data
        response_data = serializer.data
        response_data.update({
            'success': True,
            'message': f'Case update sent successfully to {case.full_name}\'s reporter ({case.reporter.username})',
            'case_info': {
                'id': case.id,
                'full_name': case.full_name,
                'reporter': case.reporter.username,
                'status': case.status,
                'submission_status': case.submission_status
            }
        })

        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cases_for_updates(request):
    """
    Get cases that have reporters and can receive updates
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Filter cases that have reporters
    queryset = MissingPerson.objects.filter(
        reporter__isnull=False
    ).select_related('reporter').order_by('-date_reported')
    
    # Apply search filter if provided
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(reporter__username__icontains=search) |
            models.Q(last_seen_location__icontains=search)
        )
    
    # Apply pagination
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    serializer = MissingPersonSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def case_detail_with_updates(request, case_id):
    case = get_object_or_404(MissingPerson, pk=case_id)

    if case.reporter != request.user and not request.user.is_staff:
        return Response(
            {'error': 'You do not have permission to view this case'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = MissingPersonSerializer(case, context={'request': request})
    return Response(serializer.data)


# Add this to missing/views.py


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cases_stats(request):
    """Get comprehensive statistics for missing person cases"""
    try:
        # Apply the same filters as the main cases endpoint
        queryset = MissingPerson.objects.all()
        filtered_qs = MissingPersonFilter(request.GET, queryset=queryset).qs
        
        # Calculate stats using database aggregation (much more efficient)
        total_cases = filtered_qs.count()
        
        # Submission status stats
        submission_stats = filtered_qs.aggregate(
            active=Count('id', filter=Q(submission_status='active')),
            in_progress=Count('id', filter=Q(submission_status='in_progress')),
            closed=Count('id', filter=Q(submission_status='closed')),
            rejected=Count('id', filter=Q(submission_status='rejected'))
        )
        
        # Case status stats  
        case_stats = filtered_qs.aggregate(
            missing=Count('id', filter=Q(status='missing')),
            found=Count('id', filter=Q(status='found')),
            investigating=Count('id', filter=Q(status='under_investigation'))
        )
        
        # Gender breakdown
        gender_stats = filtered_qs.aggregate(
            male=Count('id', filter=Q(gender='Male')),
            female=Count('id', filter=Q(gender='Female'))
        )
        
        # Recent cases (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_cases = filtered_qs.filter(date_reported__gte=thirty_days_ago).count()
        
        return Response({
            'total_cases': total_cases,
            'submission_status': {
                'active': submission_stats['active'] or 0,
                'in_progress': submission_stats['in_progress'] or 0,
                'closed': submission_stats['closed'] or 0,
                'rejected': submission_stats['rejected'] or 0
            },
            'case_status': {
                'missing': case_stats['missing'] or 0,
                'found': case_stats['found'] or 0,
                'investigating': case_stats['investigating'] or 0
            },
            'gender': {
                'male': gender_stats['male'] or 0,
                'female': gender_stats['female'] or 0
            },
            'recent_cases_30_days': recent_cases,
            'filters_applied': dict(request.GET),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
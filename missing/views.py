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
    try:
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
                    
                    if similarity >= 40:  
                        existing_match = AIMatch.objects.filter(
                            original_case=new_person,
                            matched_case=person
                        ).first()
                        
                        if not existing_match:
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
        
        new_person = serializer.save()
        
        new_person._current_user = request.user
        new_person.save()  
        
        print(f"✅ New missing person case created: {new_person.full_name} (ID: {new_person.id})")
        
        response_data = serializer.data
        response_data['message'] = f"Missing person case for {new_person.full_name} has been successfully created."
        
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
            
            missing._current_user = request.user
            updated_person = serializer.save()
            
            if updated_person.photo and (not old_photo or str(updated_person.photo) != str(old_photo)):
                print(f"🔄 Photo updated for {updated_person.full_name}")
            
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
  
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff can add updates to cases'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    case = get_object_or_404(MissingPerson, pk=case_id)
    
    if not case.reporter:
        return Response(
            {'error': 'Cannot send update - case has no reporter'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = CaseUpdateCreateSerializer(data=request.data, context={'case_id': case_id})

    if serializer.is_valid():
        update = serializer.save()
        
        update._current_user = request.user
        update.save()  
        
        if 'submission_status' in request.data:
            new_status = request.data['submission_status']
            
            case._current_user = request.user
            case.submission_status = new_status
            case.save()  

        print(f"✅ Case update created for case {case.id}")
        
        response_data = serializer.data
        response_data.update({
            'success': True,
            'message': f'Case update processed successfully for {case.full_name}',
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
 
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    queryset = MissingPerson.objects.filter(
        reporter__isnull=False
    ).select_related('reporter').order_by('-date_reported')
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(reporter__username__icontains=search) |
            models.Q(last_seen_location__icontains=search)
        )
    
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cases_stats(request):
    try:
        queryset = MissingPerson.objects.all()
        filtered_qs = MissingPersonFilter(request.GET, queryset=queryset).qs
        
        total_cases = filtered_qs.count()
        
        submission_stats = filtered_qs.aggregate(
            active=Count('id', filter=Q(submission_status='active')),
            in_progress=Count('id', filter=Q(submission_status='in_progress')),
            closed=Count('id', filter=Q(submission_status='closed')),
            rejected=Count('id', filter=Q(submission_status='rejected'))
        )
        
        case_stats = filtered_qs.aggregate(
            missing=Count('id', filter=Q(status='missing')),
            found=Count('id', filter=Q(status='found')),
            under_investigation=Count('id', filter=Q(status='under_investigation'))
        )
        
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_stats = {
            'total_recent': filtered_qs.filter(date_reported__gte=thirty_days_ago).count(),
            'recent_active': filtered_qs.filter(
                date_reported__gte=thirty_days_ago,
                submission_status='active'
            ).count(),
            'recent_found': filtered_qs.filter(
                date_reported__gte=thirty_days_ago,
                status='found'
            ).count()
        }

        return Response({
            'total_cases': total_cases,
            'submission_stats': submission_stats,
            'case_stats': case_stats,
            'recent_stats': recent_stats,
            'calculated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to calculate statistics: {str(e)}',
            'total_cases': 0,
            'submission_stats': {},
            'case_stats': {},
            'recent_stats': {}
        }, status=500)
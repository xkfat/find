from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from django.conf import settings
from .serializers import MissingPersonSerializer, CaseUpdateSerializer, SubmittedCaseListSerializer, CaseUpdateCreateSerializer
from .models import MissingPerson, CaseUpdate
from .filters import MissingPersonFilter
import cv2
import numpy as np
import os


def auto_face_match_on_creation(new_person):
    """Automatically check for face matches when a new case is created"""
    import face_recognition
    
    if not new_person.photo:
        return []
    
    try:
        new_image_path = os.path.join(settings.MEDIA_ROOT, str(new_person.photo))
        
        existing_persons = MissingPerson.objects.filter(
            photo__isnull=False,
            gender=new_person.gender
        ).exclude(id=new_person.id)
        
        if not existing_persons.exists():
            return []
        
        new_img = cv2.imread(new_image_path)
        new_img_rgb = cv2.cvtColor(new_img, cv2.COLOR_BGR2RGB)
        new_encodings = face_recognition.face_encodings(new_img_rgb)
        
        if len(new_encodings) == 0:
            print("No face detected in new person's image")
            return []
        
        new_encoding = new_encodings[0]
        matches = []
        
        for person in existing_persons:
            try:
                existing_image_path = os.path.join(settings.MEDIA_ROOT, str(person.photo))
                if os.path.exists(existing_image_path):
                    
                    existing_img = cv2.imread(existing_image_path)
                    existing_img_rgb = cv2.cvtColor(existing_img, cv2.COLOR_BGR2RGB)
                    existing_encodings = face_recognition.face_encodings(existing_img_rgb)
                    
                    if len(existing_encodings) > 0:
                        existing_encoding = existing_encodings[0]
                        
                        distance = face_recognition.face_distance([existing_encoding], new_encoding)[0]
                        similarity = max(0, (1 - distance) * 100)
                        
                        if similarity >= 45:
                            matches.append({
                                'person_id': person.id,
                                'person_name': person.full_name,
                                'similarity_percentage': round(similarity, 1),
                                'status': 'pending',
                                'photo_url': person.photo.url if person.photo else None
                            })
                            
                            print(f"Match found: {person.full_name} - {similarity:.1f}%")
            
            except Exception as e:
                print(f"Error comparing with {person.full_name}: {e}")
                continue
        
        matches.sort(key=lambda x: x['similarity_percentage'], reverse=True)
        return matches
        
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
        face_matches = auto_face_match_on_creation(new_person)
        
        response_data = serializer.data
        
        if face_matches:
            response_data['face_matches'] = {
                'found': True,
                'count': len(face_matches),
                'matches': face_matches,
                'message': f'Found {len(face_matches)} potential matches (45%+ similarity, same gender)',
                'note': 'These matches need admin review and verification'
            }
        else:
            response_data['face_matches'] = {
                'found': False,
                'count': 0,
                'matches': [],
                'message': 'No similar faces found'
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
            serializer.save()
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
    serializer = CaseUpdateCreateSerializer(data=request.data, context={'case_id': case_id})

    if serializer.is_valid():
        serializer.save()

        if 'submission_status' in request.data:
            case.submission_status = request.data['submission_status']
            case.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
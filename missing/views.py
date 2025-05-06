from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny,IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from .models import MissingPerson, CaseUpdate
from .serializers import MissingPersonSerializer, CaseUpdateSerializer, SubmittedCaseListSerializer, CaseUpdateCreateSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def missing_person_list(request):
    print("CONTENT-TYPE:", request.content_type)

    if request.method == 'GET':
        queryset = MissingPerson.objects.all().order_by('-date_reported')
        serializer = MissingPersonSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = MissingPersonSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    

        
    
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
@parser_classes([MultiPartParser, JSONParser, FormParser])
def missing_person_detail(request, pk):
    missing = get_object_or_404(MissingPerson, pk=pk)

    if request.method == 'GET':
        serializer = MissingPersonSerializer(missing,context={'request': request})
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
def case_updates(request, case_id):
      case = get_object_or_404(MissingPerson, pk=case_id)

      if case.reporter != request.user and not request.user.is_staff:
            return Response(
                  {'error': 'You do not have permission to view updates for this case'}, status=status.HTTP_403_FORBIDDEN
            )
      updates = CaseUpdate.objects.filter(case=case)
      serializer = CaseUpdateSerializer(updates, many=True)
      return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_case_update(request, case_id):
      if not request.user.is_staff:
            return Response(
                 {'error' : 'Only staff can add updates to cases'}, status=status.HTTP_403_FORBIDDEN 
            )
      case =get_object_or_404(MissingPerson, pk=case_id)
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
                  {'error': 'You do not have permission to view this case'}, status=status.HTTP_403_FORBIDDEN
            )
      serializer = MissingPersonSerializer(case, context={'request': request})
      return Response(serializer.date)
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny,IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from .models import MissingPerson
from .serializers import MissingPersonSerializer
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
       # print(serializer.data)
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
    

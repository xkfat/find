from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import MissingPerson
from .serializers import MissingPersonSerializer


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def missing_person_list(request):
    if request.method == 'GET':
        queryset = MissingPerson.objects.all().order_by('-date_reported')
        serializer = MissingPersonSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = MissingPersonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(reporter=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

        
    
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def missing_person_detail(request, id):
    missing = get_object_or_404(MissingPerson, id=id)

    if request.method == 'GET':
        serializer = MissingPersonSerializer(missing)
       # print(serializer.data)
        return Response(serializer.data)
    
    elif request.method in ['PATCH', 'DELETE']:
            if not request.user.is_authenticated or not request.user.is_staff:
                 return Response({'error': 'Only admins can update or delete'}, status=status.HTTP_403_FORBIDDEN)
            
            if request.method == 'PATCH':
             serializer = MissingPersonSerializer(missing, data=request.data, partial=True)
             if serializer.is_valid():
                  serializer.save()
                  return Response(serializer.data, status=status.HTTP_200_OK)
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
            elif request.method == 'DELETE':
                            missing.delete()
                            return Response(status=status.HTTP_204_NO_CONTENT)
    

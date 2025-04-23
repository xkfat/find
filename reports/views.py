from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Report
from .serializers import ReportSerializer
from missing.models import MissingPerson


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_report(request):
    note = request.data.get('note')
    missing_id = request.data.get('missing_person')
    
    try:
        missing_person = MissingPerson.objects.get(id=missing_id)
    except MissingPerson.DoesNotExist:
        return Response({'error': 'Missing person not found.'}, status=status.HTTP_404_NOT_FOUND)

    report = Report.objects.create(
        user=request.user,
        missing_person=missing_person,
        note=note
    )
    return Response({'message': 'Thank you for trying to help us, we appreciate your helping ^^'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_reports(request):
    reports = Report.objects.all().order_by('-date_submitted')
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def report_detail(request, id):
    report = get_object_or_404(Report, id=id)

    if request.method == 'GET':
        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = ReportSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return  Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
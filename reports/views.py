from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Report
from .serializers import ReportSerializer

@api_view(['POST'])
def submit_report(request):
    print(f"Request data: {request.data}")

    serializer = ReportSerializer(data=request.data)


    if not serializer.is_valid():
        print(f"Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


   
    if request.user.is_authenticated:
        report = serializer.save(user=request.user)
    else:
        report = serializer.save(user=None)

    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_reports(request):
    reports = Report.objects.select_related('user','missing_person').order_by('-date_submitted')
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
    
    
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_report_status(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    new_status = request.data.get('report_status')
    

    valid = {choice[0] for choice in Report.REPORT_CHOICES}
    if new_status not in valid:
        return Response({'error' : 'Invalid report status.'}, status=status.HTTP_400_BAD_REQUEST)
    
    report.report_status = new_status
    report.save()

  

    serializer = ReportSerializer(report)
    return Response(serializer.data, status=status.HTTP_200_OK)
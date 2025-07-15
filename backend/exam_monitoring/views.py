from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from exam_system.exam_monitoring.models import ExamRecord
from .serializers import ExamSerializer

@api_view(['GET'])
def current_exam(request):
    """获取当前考试信息"""
    exam = ExamRecord.objects.filter(student=request.user, status='in_progress').first()
    if not exam:
        return Response({'error': 'No active exam found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ExamSerializer(exam)
    return Response(serializer.data)

@api_view(['POST'])
def submit_exam(request):
    """提交考试答案"""
    exam = ExamRecord.objects.filter(student=request.user, status='in_progress').first()
    if not exam:
        return Response({'error': 'No active exam to submit'}, status=status.HTTP_400_BAD_REQUEST)
    
    exam.status = 'submitted'
    exam.save()
    return Response({'status': 'Exam submitted successfully'})

@api_view(['GET'])
def monitor_exam(request):
    """监控考试状态"""
    exam = ExamRecord.objects.filter(student=request.user, status='in_progress').first()
    if not exam:
        return Response({'error': 'No active exam to monitor'}, status=status.HTTP_404_NOT_FOUND)
    return Response({
        'status': exam.status,
        'exam_id': exam.exam.pk
    })
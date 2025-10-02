"""
判题系统监控视图
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from oj_project.problems.models import Submission
from .audit import get_submission_statistics
import platform


@require_http_methods(["GET"])
def health_check(request):
    """
    健康检查端点
    用于监控系统状态
    """
    try:
        # 检查数据库连接
        from django.db import connection
        connection.ensure_connection()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # 检查Redis连接
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection('default')
        redis_conn.ping()
        redis_status = 'healthy'
    except Exception as e:
        redis_status = f'unhealthy: {str(e)}'
    
    # 检查Celery
    try:
        from oj_project.celery import app
        inspect = app.control.inspect()
        active_tasks = inspect.active()
        celery_status = 'healthy' if active_tasks is not None else 'unhealthy'
    except Exception as e:
        celery_status = f'unhealthy: {str(e)}'
    
    return JsonResponse({
        'status': 'ok' if all([
            db_status == 'healthy',
            redis_status == 'healthy',
            celery_status == 'healthy'
        ]) else 'degraded',
        'timestamp': timezone.now().isoformat(),
        'components': {
            'database': db_status,
            'redis': redis_status,
            'celery': celery_status,
        }
    })


@staff_member_required
@require_http_methods(["GET"])
def system_metrics(request):
    """
    系统指标监控
    仅管理员可访问
    """
    try:
        import psutil
    except ImportError:
        return JsonResponse({
            'error': 'psutil not installed',
            'message': '请安装psutil: pip install psutil'
        }, status=500)
    
    # CPU和内存使用情况
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 获取最近24小时的提交统计
    stats_24h = get_submission_statistics(time_range_hours=24)
    
    # 获取最近1小时的提交统计
    stats_1h = get_submission_statistics(time_range_hours=1)
    
    # 获取Pending的提交数
    pending_submissions = Submission.objects.filter(
        status__in=['Pending', 'Judging']
    ).count()
    
    # 获取最近的错误提交
    recent_errors = Submission.objects.filter(
        status='System Error',
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    return JsonResponse({
        'timestamp': timezone.now().isoformat(),
        'system': {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': cpu_percent,
            'memory': {
                'total_mb': memory.total // (1024 * 1024),
                'available_mb': memory.available // (1024 * 1024),
                'used_percent': memory.percent,
            },
            'disk': {
                'total_gb': disk.total // (1024 * 1024 * 1024),
                'used_gb': disk.used // (1024 * 1024 * 1024),
                'free_gb': disk.free // (1024 * 1024 * 1024),
                'used_percent': disk.percent,
            }
        },
        'submissions': {
            'pending': pending_submissions,
            'recent_errors': recent_errors,
            'last_24h': stats_24h,
            'last_1h': stats_1h,
        }
    })


@staff_member_required
@require_http_methods(["GET"])
def security_dashboard(request):
    """
    安全监控仪表板
    显示最近的安全事件
    """
    # 获取最近24小时被拒绝的提交
    rejected_submissions = Submission.objects.filter(
        status='Compile Error',
        error_info__contains='安全检查失败',
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).select_related('user', 'problem').order_by('-created_at')[:50]
    
    rejected_data = [{
        'id': sub.id,
        'user': sub.user.username,
        'problem': sub.problem.title,
        'language': sub.language,
        'error': sub.error_info,
        'created_at': sub.created_at.isoformat(),
    } for sub in rejected_submissions]
    
    # 统计高频提交用户（可能的异常行为）
    from django.db.models import Count
    frequent_users = Submission.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).values('user__username').annotate(
        count=Count('id')
    ).filter(count__gt=10).order_by('-count')
    
    return JsonResponse({
        'timestamp': timezone.now().isoformat(),
        'rejected_submissions_24h': len(rejected_data),
        'recent_rejections': rejected_data[:10],  # 只返回最近10条
        'frequent_submitters_1h': list(frequent_users),
        'security_level': 'monitoring',
    })


@staff_member_required
@require_http_methods(["POST"])
def clear_judge_queue(request):
    """
    清理判题队列（紧急情况使用）
    """
    try:
        # 将所有Pending和Judging状态改为System Error
        affected = Submission.objects.filter(
            status__in=['Pending', 'Judging']
        ).update(
            status='System Error',
            error_info='判题队列已被管理员清理'
        )
        
        # 清除Celery队列
        from oj_project.celery import app
        app.control.purge()
        
        return JsonResponse({
            'success': True,
            'affected_submissions': affected,
            'message': '判题队列已清理'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

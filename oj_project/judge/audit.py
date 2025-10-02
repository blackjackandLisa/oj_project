"""
判题系统审计日志模块

记录所有判题活动，便于安全审计和问题排查
"""

import logging
from datetime import datetime
from django.contrib.auth.models import User

logger = logging.getLogger('judge.audit')


def log_submission_event(submission, event_type, details=None, user=None):
    """
    记录提交事件审计日志
    
    Args:
        submission: Submission对象
        event_type: 事件类型（created, judging, completed, error, security_check）
        details: 额外的详细信息字典
        user: 用户对象（可选，默认从submission获取）
    """
    if user is None:
        user = submission.user
    
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'submission_id': submission.id,
        'user_id': user.id,
        'username': user.username,
        'problem_id': submission.problem.id,
        'problem_title': submission.problem.title,
        'language': submission.language,
        'status': submission.status,
        'code_length': len(submission.code),
        'ip_address': details.get('ip_address') if details else None,
    }
    
    # 添加额外详情
    if details:
        log_data['details'] = details
    
    # 根据事件类型记录不同级别
    if event_type == 'security_check_failed':
        logger.warning(f"SECURITY_ALERT: {log_data}")
    elif event_type == 'error':
        logger.error(f"AUDIT_ERROR: {log_data}")
    else:
        logger.info(f"AUDIT: {log_data}")
    
    return log_data


def log_security_incident(submission, incident_type, description, severity='HIGH'):
    """
    记录安全事件
    
    Args:
        submission: Submission对象
        incident_type: 事件类型（blacklist_hit, resource_abuse, system_attack）
        description: 事件描述
        severity: 严重程度（LOW, MEDIUM, HIGH, CRITICAL）
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'incident_type': incident_type,
        'severity': severity,
        'submission_id': submission.id,
        'user_id': submission.user.id,
        'username': submission.user.username,
        'problem_id': submission.problem.id,
        'language': submission.language,
        'description': description,
        'code_snippet': submission.code[:200] + '...' if len(submission.code) > 200 else submission.code,
    }
    
    logger.critical(f"SECURITY_INCIDENT: {log_data}")
    
    # TODO: 可以在这里添加告警通知（邮件、短信、webhook等）
    
    return log_data


def log_resource_usage(submission, cpu_time, memory_used, execution_time):
    """
    记录资源使用情况
    
    Args:
        submission: Submission对象
        cpu_time: CPU时间（毫秒）
        memory_used: 内存使用（KB）
        execution_time: 执行时间（毫秒）
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'submission_id': submission.id,
        'user_id': submission.user.id,
        'cpu_time_ms': cpu_time,
        'memory_kb': memory_used,
        'execution_time_ms': execution_time,
        'time_limit_ms': submission.problem.time_limit,
        'memory_limit_mb': submission.problem.memory_limit,
    }
    
    logger.debug(f"RESOURCE_USAGE: {log_data}")
    
    return log_data


def get_submission_statistics(user_id=None, time_range_hours=24):
    """
    获取提交统计（用于监控异常行为）
    
    Args:
        user_id: 用户ID（可选，None表示所有用户）
        time_range_hours: 统计时间范围（小时）
    
    Returns:
        dict: 统计信息
    """
    from django.utils import timezone
    from datetime import timedelta
    from oj_project.problems.models import Submission
    
    time_threshold = timezone.now() - timedelta(hours=time_range_hours)
    
    query = Submission.objects.filter(created_at__gte=time_threshold)
    if user_id:
        query = query.filter(user_id=user_id)
    
    total_submissions = query.count()
    
    stats = {
        'time_range_hours': time_range_hours,
        'user_id': user_id,
        'total_submissions': total_submissions,
        'accepted': query.filter(status='Accepted').count(),
        'wrong_answer': query.filter(status='Wrong Answer').count(),
        'runtime_error': query.filter(status='Runtime Error').count(),
        'compile_error': query.filter(status='Compile Error').count(),
        'time_limit': query.filter(status='Time Limit Exceeded').count(),
        'by_language': {
            'python': query.filter(language='Python').count(),
            'cpp': query.filter(language='C++').count(),
        }
    }
    
    return stats


class AuditMiddleware:
    """
    审计中间件：记录所有HTTP请求
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 记录请求
        if request.path.startswith('/api/') or request.path.startswith('/problems/'):
            logger.debug(f"REQUEST: {request.method} {request.path} from {self.get_client_ip(request)} by {request.user}")
        
        response = self.get_response(request)
        
        # 记录响应
        if response.status_code >= 400:
            logger.warning(f"ERROR_RESPONSE: {request.method} {request.path} -> {response.status_code}")
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


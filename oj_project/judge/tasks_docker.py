"""
Docker容器化判题任务

使用Docker容器进行安全隔离的代码评测
"""

import time
from celery import shared_task
from django.conf import settings
from oj_project.problems.models import Submission, TestCase
from .audit import log_submission_event, log_security_incident, log_resource_usage
from .docker_judge import DockerJudge


@shared_task
def judge_submission_docker(submission_id):
    """
    使用Docker容器判题（安全加固版）
    
    Args:
        submission_id: 提交记录ID
    """
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return {'error': 'Submission not found'}
    
    # 记录：开始判题
    log_submission_event(submission, 'judging_docker', {'start_time': time.time()})
    
    # 更新状态为评测中
    submission.status = 'Judging'
    submission.save()
    
    try:
        # 初始化Docker判题引擎
        try:
            judge = DockerJudge()
        except RuntimeError as e:
            submission.status = 'System Error'
            submission.error_info = f'Docker引擎初始化失败: {str(e)}'
            submission.save()
            log_submission_event(submission, 'docker_init_error', {'error': str(e)})
            return {'error': str(e)}
        
        # 获取题目的测试用例
        problem = submission.problem
        test_cases = problem.test_cases.all().order_by('order')
        
        if not test_cases.exists():
            submission.status = 'System Error'
            submission.error_info = '该题目没有测试用例'
            submission.save()
            return {'error': 'No test cases'}
        
        # 根据语言选择评测方法
        if submission.language == 'Python':
            result = judge_python_docker(judge, submission, test_cases)
        elif submission.language == 'C++':
            result = judge_cpp_docker(judge, submission, test_cases)
        else:
            submission.status = 'System Error'
            submission.error_info = f'不支持的语言: {submission.language}'
            submission.save()
            return {'error': 'Unsupported language'}
        
        # 更新提交结果
        submission.status = result['status']
        submission.score = result.get('score', 0)
        submission.time_used = result.get('time_used', 0)
        submission.memory_used = result.get('memory_used', 0)
        submission.error_info = result.get('error_info', '')
        submission.save()
        
        # 记录资源使用
        log_resource_usage(
            submission,
            submission.time_used,
            submission.memory_used,
            submission.time_used
        )
        
        # 记录：判题完成
        log_submission_event(
            submission,
            'completed_docker',
            {
                'status': submission.status,
                'score': submission.score,
                'time_used': submission.time_used,
                'judge_method': 'docker'
            }
        )
        
        # 如果通过，更新题目统计
        if submission.status == 'Accepted':
            problem.total_accepted += 1
            problem.save()
        
        return result
        
    except Exception as e:
        submission.status = 'System Error'
        submission.error_info = str(e)
        submission.save()
        
        # 记录：系统错误
        log_submission_event(submission, 'error_docker', {'exception': str(e)})
        
        return {'error': str(e)}


def judge_python_docker(judge, submission, test_cases):
    """
    使用Docker容器评测Python代码
    
    Args:
        judge: DockerJudge实例
        submission: 提交记录
        test_cases: 测试用例列表
    
    Returns:
        dict: 评测结果
    """
    problem = submission.problem
    code = submission.code
    
    total_cases = test_cases.count()
    passed_cases = 0
    max_time = 0
    max_memory = 0
    
    for test_case in test_cases:
        try:
            # 使用Docker容器执行
            result = judge.judge_python(
                code=code,
                test_input=test_case.input_data,
                time_limit_ms=problem.time_limit,
                memory_limit_mb=problem.memory_limit
            )
            
            # 更新最大资源使用
            max_time = max(max_time, result.get('time_ms', 0))
            max_memory = max(max_memory, result.get('memory_kb', 0))
            
            # 检查状态
            if result['status'] == 'Runtime Error':
                return {
                    'status': 'Runtime Error',
                    'error_info': f"测试用例 #{test_case.order}\n{result.get('error', '')}",
                    'time_used': max_time,
                    'memory_used': max_memory,
                    'score': int(passed_cases / total_cases * 100)
                }
            
            if result['status'] == 'Time Limit Exceeded':
                return {
                    'status': 'Time Limit Exceeded',
                    'error_info': result.get('error', ''),
                    'time_used': problem.time_limit,
                    'memory_used': max_memory,
                    'score': int(passed_cases / total_cases * 100)
                }
            
            # 比对输出
            output = result.get('output', '').strip()
            expected = test_case.output_data.strip()
            
            if output == expected:
                passed_cases += 1
            else:
                return {
                    'status': 'Wrong Answer',
                    'error_info': f'测试用例 #{test_case.order}\n期望输出:\n{expected}\n实际输出:\n{output}',
                    'time_used': max_time,
                    'memory_used': max_memory,
                    'score': int(passed_cases / total_cases * 100)
                }
                
        except Exception as e:
            return {
                'status': 'System Error',
                'error_info': f'Docker执行错误: {str(e)}',
                'time_used': 0,
                'memory_used': 0,
                'score': 0
            }
    
    # 所有测试用例通过
    return {
        'status': 'Accepted',
        'error_info': '',
        'time_used': max_time,
        'memory_used': max_memory,
        'score': 100
    }


def judge_cpp_docker(judge, submission, test_cases):
    """
    使用Docker容器评测C++代码
    
    Args:
        judge: DockerJudge实例
        submission: 提交记录
        test_cases: 测试用例列表
    
    Returns:
        dict: 评测结果
    """
    problem = submission.problem
    code = submission.code
    
    total_cases = test_cases.count()
    passed_cases = 0
    max_time = 0
    max_memory = 0
    
    # 首先编译检查（使用第一个测试用例的空输入）
    first_result = judge.judge_cpp(
        code=code,
        test_input='',
        time_limit_ms=10000,  # 编译给10秒
        memory_limit_mb=512  # 编译需要更多内存
    )
    
    if first_result['status'] == 'Compile Error':
        return {
            'status': 'Compile Error',
            'error_info': first_result.get('error', ''),
            'time_used': 0,
            'memory_used': 0,
            'score': 0
        }
    
    # 逐个测试用例运行
    for test_case in test_cases:
        try:
            result = judge.judge_cpp(
                code=code,
                test_input=test_case.input_data,
                time_limit_ms=problem.time_limit,
                memory_limit_mb=problem.memory_limit
            )
            
            max_time = max(max_time, result.get('time_ms', 0))
            max_memory = max(max_memory, result.get('memory_kb', 0))
            
            if result['status'] == 'Compile Error':
                return {
                    'status': 'Compile Error',
                    'error_info': result.get('error', ''),
                    'time_used': 0,
                    'memory_used': 0,
                    'score': 0
                }
            
            if result['status'] == 'Runtime Error':
                return {
                    'status': 'Runtime Error',
                    'error_info': f"测试用例 #{test_case.order}\n{result.get('error', '')}",
                    'time_used': max_time,
                    'memory_used': max_memory,
                    'score': int(passed_cases / total_cases * 100)
                }
            
            if result['status'] == 'Time Limit Exceeded':
                return {
                    'status': 'Time Limit Exceeded',
                    'error_info': result.get('error', ''),
                    'time_used': problem.time_limit,
                    'memory_used': max_memory,
                    'score': int(passed_cases / total_cases * 100)
                }
            
            # 比对输出
            output = result.get('output', '').strip()
            expected = test_case.output_data.strip()
            
            # 尝试逐行比较（忽略行尾空格）
            output_lines = [line.rstrip() for line in output.split('\n')]
            expected_lines = [line.rstrip() for line in expected.split('\n')]
            
            if output_lines == expected_lines:
                passed_cases += 1
            else:
                return {
                    'status': 'Wrong Answer',
                    'error_info': f'测试用例 #{test_case.order}\n期望输出:\n{expected}\n\n实际输出:\n{output}',
                    'time_used': max_time,
                    'memory_used': max_memory,
                    'score': int(passed_cases / total_cases * 100)
                }
                
        except Exception as e:
            return {
                'status': 'System Error',
                'error_info': f'Docker执行错误: {str(e)}',
                'time_used': 0,
                'memory_used': 0,
                'score': 0
            }
    
    # 所有测试用例通过
    return {
        'status': 'Accepted',
        'error_info': '',
        'time_used': max_time,
        'memory_used': max_memory,
        'score': 100
    }


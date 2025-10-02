"""
安全加固版判题系统

这是一个改进版本，增加了基本的安全措施：
1. 代码黑名单检查
2. 资源限制（CPU、内存、进程数）
3. 环境变量清理
4. 代码长度限制
5. 工作目录隔离

使用方法：
将此文件内容替换 tasks.py 以启用安全加固
"""

import os
import subprocess
import tempfile
import time
import resource
import re
from celery import shared_task
from django.conf import settings
from oj_project.problems.models import Submission, TestCase


# 安全配置
MAX_CODE_LENGTH = 10000  # 代码最大长度（字符）
MAX_OUTPUT_LENGTH = 10000  # 输出最大长度（字符）

# Python危险操作黑名单
PYTHON_BLACKLIST = [
    r'\bos\.system\b',
    r'\bsubprocess\b',
    r'\beval\b',
    r'\bexec\b',
    r'\b__import__\b',
    r'\bcompile\b',
    r'\breload\b',
    r'\bimport\s+requests\b',
    r'\bimport\s+urllib\b',
    r'\bimport\s+socket\b',
    r'\bimport\s+sys\b',
    r'\bimport\s+shutil\b',
    r'\bopen\s*\(',  # 禁止文件操作
    r'\bfile\s*\(',
]

# C++危险操作黑名单
CPP_BLACKLIST = [
    r'\bsystem\s*\(',
    r'\bexec\w*\s*\(',
    r'\bfork\s*\(',
    r'\b#include\s*<fstream>',
    r'\b#include\s*<sys/',
    r'\bremove\s*\(',
    r'\brename\s*\(',
]


def check_code_security(code, language):
    """
    检查代码是否包含危险操作
    
    Args:
        code: 用户代码
        language: 编程语言
    
    Returns:
        tuple: (是否安全, 错误信息)
    """
    # 检查代码长度
    if len(code) > MAX_CODE_LENGTH:
        return False, f'代码长度超过限制（最大 {MAX_CODE_LENGTH} 字符）'
    
    # 选择对应的黑名单
    blacklist = PYTHON_BLACKLIST if language == 'Python' else CPP_BLACKLIST
    
    # 检查黑名单
    for pattern in blacklist:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f'代码包含不允许的操作（安全限制）'
    
    return True, ''


def set_resource_limits():
    """
    设置子进程的资源限制
    在Unix系统上生效
    """
    try:
        # 限制CPU时间为5秒
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        
        # 限制内存为256MB
        mem_bytes = 256 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        
        # 限制最大进程数
        resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
        
        # 限制文件大小为10MB
        file_bytes = 10 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))
        
        # 限制打开文件数
        resource.setrlimit(resource.RLIMIT_NOFILE, (20, 20))
    except Exception as e:
        # Windows系统不支持resource模块，静默忽略
        pass


@shared_task
def judge_submission(submission_id):
    """
    评测代码提交（安全加固版）
    """
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return {'error': 'Submission not found'}
    
    # 更新状态为评测中
    submission.status = 'Judging'
    submission.save()
    
    try:
        # 安全检查
        is_safe, error_msg = check_code_security(submission.code, submission.language)
        if not is_safe:
            submission.status = 'Compile Error'
            submission.error_info = f'安全检查失败: {error_msg}'
            submission.save()
            return {'error': error_msg}
        
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
            result = judge_python_secure(submission, test_cases)
        elif submission.language == 'C++':
            result = judge_cpp_secure(submission, test_cases)
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
        
        # 如果通过，更新题目统计
        if submission.status == 'Accepted':
            problem.total_accepted += 1
            problem.save()
        
        return result
        
    except Exception as e:
        submission.status = 'System Error'
        submission.error_info = str(e)
        submission.save()
        return {'error': str(e)}


def judge_python_secure(submission, test_cases):
    """
    评测 Python 代码（安全加固版）
    """
    problem = submission.problem
    code = submission.code
    
    total_cases = test_cases.count()
    passed_cases = 0
    max_time = 0
    
    for test_case in test_cases:
        try:
            # 创建临时文件保存代码
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            try:
                # 运行代码（增加安全限制）
                start_time = time.time()
                process = subprocess.run(
                    ['python', code_file],
                    input=test_case.input_data,
                    capture_output=True,
                    text=True,
                    timeout=problem.time_limit / 1000.0,
                    check=False,
                    env={},  # 清空环境变量
                    cwd='/tmp',  # 设置工作目录
                    preexec_fn=set_resource_limits  # 设置资源限制
                )
                end_time = time.time()
                
                execution_time = int((end_time - start_time) * 1000)
                max_time = max(max_time, execution_time)
                
                # 检查输出长度
                if len(process.stdout) > MAX_OUTPUT_LENGTH:
                    return {
                        'status': 'Runtime Error',
                        'error_info': '输出长度超过限制',
                        'time_used': execution_time,
                        'memory_used': 0,
                        'score': int(passed_cases / total_cases * 100)
                    }
                
                # 检查是否有运行时错误
                if process.returncode != 0:
                    # 检查是否是资源限制导致的错误
                    if process.returncode == -9:  # SIGKILL
                        return {
                            'status': 'Memory Limit Exceeded',
                            'error_info': '内存超出限制',
                            'time_used': execution_time,
                            'memory_used': 0,
                            'score': int(passed_cases / total_cases * 100)
                        }
                    
                    return {
                        'status': 'Runtime Error',
                        'error_info': process.stderr[:500],
                        'time_used': execution_time,
                        'memory_used': 0,
                        'score': int(passed_cases / total_cases * 100)
                    }
                
                # 比对输出
                output = process.stdout.strip()
                expected = test_case.output_data.strip()
                
                if output == expected:
                    passed_cases += 1
                else:
                    return {
                        'status': 'Wrong Answer',
                        'error_info': f'测试用例 #{test_case.order}\n期望输出:\n{expected}\n实际输出:\n{output}',
                        'time_used': execution_time,
                        'memory_used': 0,
                        'score': int(passed_cases / total_cases * 100)
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    'status': 'Time Limit Exceeded',
                    'error_info': f'运行超时 (>{problem.time_limit}ms)',
                    'time_used': problem.time_limit,
                    'memory_used': 0,
                    'score': int(passed_cases / total_cases * 100)
                }
            finally:
                # 删除临时文件
                if os.path.exists(code_file):
                    os.remove(code_file)
                    
        except Exception as e:
            return {
                'status': 'System Error',
                'error_info': str(e),
                'time_used': 0,
                'memory_used': 0,
                'score': 0
            }
    
    # 所有测试用例通过
    return {
        'status': 'Accepted',
        'error_info': '',
        'time_used': max_time,
        'memory_used': 0,
        'score': 100
    }


def judge_cpp_secure(submission, test_cases):
    """
    评测 C++ 代码（安全加固版）
    """
    problem = submission.problem
    code = submission.code
    
    total_cases = test_cases.count()
    passed_cases = 0
    max_time = 0
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 保存源代码
        source_file = os.path.join(temp_dir, 'solution.cpp')
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 编译（添加安全选项）
        executable_file = os.path.join(temp_dir, 'solution')
        compile_cmd = [
            'g++',
            '-o', executable_file,
            source_file,
            '-std=c++17',
            '-O2',
            '-Wall',  # 显示警告
            '-static',  # 静态链接
            '-DONLINE_JUDGE',  # 定义在线评测宏
        ]
        
        try:
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                cwd=temp_dir
            )
            
            if compile_result.returncode != 0:
                return {
                    'status': 'Compile Error',
                    'error_info': compile_result.stderr[:500],
                    'time_used': 0,
                    'memory_used': 0,
                    'score': 0
                }
        except subprocess.TimeoutExpired:
            return {
                'status': 'Compile Error',
                'error_info': '编译超时',
                'time_used': 0,
                'memory_used': 0,
                'score': 0
            }
        
        # 运行测试用例（增加安全限制）
        for test_case in test_cases:
            try:
                start_time = time.time()
                process = subprocess.run(
                    [executable_file],
                    input=test_case.input_data,
                    capture_output=True,
                    text=True,
                    timeout=problem.time_limit / 1000.0,
                    check=False,
                    env={},  # 清空环境变量
                    cwd=temp_dir,
                    preexec_fn=set_resource_limits  # 设置资源限制
                )
                end_time = time.time()
                
                execution_time = int((end_time - start_time) * 1000)
                max_time = max(max_time, execution_time)
                
                # 检查输出长度
                if len(process.stdout) > MAX_OUTPUT_LENGTH:
                    return {
                        'status': 'Runtime Error',
                        'error_info': '输出长度超过限制',
                        'time_used': execution_time,
                        'memory_used': 0,
                        'score': int(passed_cases / total_cases * 100)
                    }
                
                # 检查是否有运行时错误
                if process.returncode != 0:
                    if process.returncode == -9:
                        return {
                            'status': 'Memory Limit Exceeded',
                            'error_info': '内存超出限制',
                            'time_used': execution_time,
                            'memory_used': 0,
                            'score': int(passed_cases / total_cases * 100)
                        }
                    
                    return {
                        'status': 'Runtime Error',
                        'error_info': f'程序异常退出 (退出码: {process.returncode})\n{process.stderr[:300]}',
                        'time_used': execution_time,
                        'memory_used': 0,
                        'score': int(passed_cases / total_cases * 100)
                    }
                
                # 比对输出
                output = process.stdout.strip()
                expected = test_case.output_data.strip()
                
                if output == expected:
                    passed_cases += 1
                else:
                    # 检查是否只是行尾空格不同
                    output_lines = [line.rstrip() for line in output.split('\n')]
                    expected_lines = [line.rstrip() for line in expected.split('\n')]
                    
                    if output_lines == expected_lines:
                        passed_cases += 1
                    else:
                        return {
                            'status': 'Wrong Answer',
                            'error_info': f'测试用例 #{test_case.order}\n期望输出:\n{expected}\n\n实际输出:\n{output}',
                            'time_used': execution_time,
                            'memory_used': 0,
                            'score': int(passed_cases / total_cases * 100)
                        }
                        
            except subprocess.TimeoutExpired:
                return {
                    'status': 'Time Limit Exceeded',
                    'error_info': f'运行超时 (>{problem.time_limit}ms)',
                    'time_used': problem.time_limit,
                    'memory_used': 0,
                    'score': int(passed_cases / total_cases * 100)
                }
        
        # 所有测试用例通过
        return {
            'status': 'Accepted',
            'error_info': '',
            'time_used': max_time,
            'memory_used': 0,
            'score': 100
        }
        
    except Exception as e:
        return {
            'status': 'System Error',
            'error_info': str(e),
            'time_used': 0,
            'memory_used': 0,
            'score': 0
        }
    finally:
        # 清理临时文件
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass


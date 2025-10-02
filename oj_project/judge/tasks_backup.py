import os
import subprocess
import tempfile
import time
from celery import shared_task
from django.conf import settings
from oj_project.problems.models import Submission, TestCase


@shared_task
def judge_submission(submission_id):
    """
    评测代码提交
    
    Args:
        submission_id: 提交记录ID
    """
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return {'error': 'Submission not found'}
    
    # 更新状态为评测中
    submission.status = 'Judging'
    submission.save()
    
    try:
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
            result = judge_python(submission, test_cases)
        elif submission.language == 'C++':
            result = judge_cpp(submission, test_cases)
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


def judge_python(submission, test_cases):
    """
    评测 Python 代码
    
    Args:
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
            # 创建临时文件保存代码
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            try:
                # 运行代码
                start_time = time.time()
                process = subprocess.run(
                    ['python', code_file],
                    input=test_case.input_data,
                    capture_output=True,
                    text=True,
                    timeout=problem.time_limit / 1000.0,  # 转换为秒
                    check=False
                )
                end_time = time.time()
                
                execution_time = int((end_time - start_time) * 1000)  # 转换为毫秒
                max_time = max(max_time, execution_time)
                
                # 检查是否有运行时错误
                if process.returncode != 0:
                    return {
                        'status': 'Runtime Error',
                        'error_info': process.stderr[:500],  # 限制错误信息长度
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
        'memory_used': 0,  # Python 内存统计较复杂，暂时设为0
        'score': 100
    }


def judge_cpp(submission, test_cases):
    """
    评测 C++ 代码
    
    Args:
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
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 保存源代码
        source_file = os.path.join(temp_dir, 'solution.cpp')
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 编译
        executable_file = os.path.join(temp_dir, 'solution')
        compile_cmd = ['g++', '-o', executable_file, source_file, '-std=c++17', '-O2']
        
        try:
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=10,  # 编译超时10秒
                check=False
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
        
        # 运行测试用例
        for test_case in test_cases:
            try:
                start_time = time.time()
                process = subprocess.run(
                    [executable_file],
                    input=test_case.input_data,
                    capture_output=True,
                    text=True,
                    timeout=problem.time_limit / 1000.0,  # 转换为秒
                    check=False
                )
                end_time = time.time()
                
                execution_time = int((end_time - start_time) * 1000)  # 转换为毫秒
                max_time = max(max_time, execution_time)
                
                # 检查是否有运行时错误
                if process.returncode != 0:
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


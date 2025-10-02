"""
基于 Judge0 的判题任务
"""
from celery import shared_task
from django.utils import timezone
from .judge0_client import Judge0Client
from oj_project.problems.models import Submission
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def judge_submission_judge0(self, submission_id):
    """
    使用 Judge0 进行代码判题的 Celery 任务
    
    Args:
        submission_id: 提交记录的 ID
    """
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        logger.error(f"提交记录不存在: {submission_id}")
        return
    
    try:
        # 更新状态为判题中
        submission.status = 'Judging'
        submission.save(update_fields=['status'])
        
        # 获取测试用例
        test_cases = submission.problem.test_cases.all()
        if not test_cases:
            submission.status = 'System Error'
            submission.error_info = '没有可用的测试用例'
            submission.save()
            return
        
        # 初始化 Judge0 客户端
        judge0 = Judge0Client()
        
        # 记录开始时间
        start_time = timezone.now()
        
        total_time = 0
        max_memory = 0
        all_passed = True
        error_messages = []
        
        # 逐个运行测试用例
        for i, test_case in enumerate(test_cases):
            try:
                # 计算时间和内存限制
                time_limit = submission.problem.time_limit / 1000.0  # 转换为秒
                memory_limit = submission.problem.memory_limit * 1024  # 转换为 KB
                
                # 使用 Judge0 判题
                result = judge0.judge_code(
                    language=submission.language,
                    source_code=submission.code,
                    stdin=test_case.input_data,
                    expected_output=test_case.expected_output.strip(),
                    cpu_time_limit=time_limit,
                    memory_limit=memory_limit
                )
                
                # 累计时间和内存
                total_time += result['time_used']
                max_memory = max(max_memory, result['memory_used'])
                
                # 检查状态
                if result['status'] != 'Accepted':
                    all_passed = False
                    error_msg = f"测试用例 #{i+1} 失败\n"
                    error_msg += f"状态: {result['status']}\n"
                    if result['error_info']:
                        error_msg += f"详细信息:\n{result['error_info']}\n"
                    error_messages.append(error_msg)
                    
                    # 如果是编译错误或系统错误，直接终止
                    if result['status'] in ['Compilation Error', 'System Error']:
                        break
            
            except Exception as e:
                logger.error(f"测试用例 #{i+1} 执行失败: {str(e)}")
                all_passed = False
                error_messages.append(f"测试用例 #{i+1} 系统错误: {str(e)}")
                break
        
        # 更新提交结果
        if all_passed:
            submission.status = 'Accepted'
            submission.error_info = ''
        else:
            # 确定最终状态
            if error_messages:
                first_error = error_messages[0]
                if 'Compilation Error' in first_error:
                    submission.status = 'Compilation Error'
                elif 'Runtime Error' in first_error:
                    submission.status = 'Runtime Error'
                elif 'Time Limit Exceeded' in first_error:
                    submission.status = 'Time Limit Exceeded'
                elif 'Wrong Answer' in first_error:
                    submission.status = 'Wrong Answer'
                else:
                    submission.status = 'System Error'
            else:
                submission.status = 'System Error'
            
            submission.error_info = '\n\n'.join(error_messages)
        
        submission.time_used = int(total_time)
        submission.memory_used = int(max_memory)
        submission.judged_at = timezone.now()
        submission.save()
        
        # 记录判题时间
        judge_time = (timezone.now() - start_time).total_seconds()
        logger.info(
            f"提交 {submission_id} 判题完成 - "
            f"语言: {submission.language}, "
            f"状态: {submission.status}, "
            f"用时: {submission.time_used}ms, "
            f"内存: {submission.memory_used}KB, "
            f"判题耗时: {judge_time:.2f}s"
        )
    
    except Exception as e:
        logger.error(f"判题任务失败: {str(e)}", exc_info=True)
        try:
            submission = Submission.objects.get(id=submission_id)
            submission.status = 'System Error'
            submission.error_info = f'判题系统错误: {str(e)}'
            submission.judged_at = timezone.now()
            submission.save()
        except Exception:
            pass
        
        # 重试任务
        raise self.retry(exc=e, countdown=5)


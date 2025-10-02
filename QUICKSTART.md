# OJ系统快速启动指南

## Windows 环境快速启动

### 方法一：使用启动脚本（推荐）

1. **确保 Docker Desktop 正在运行**

2. **双击运行 `start.bat`**
   - 脚本会自动启动所有服务
   - 自动运行数据库迁移
   - 提示创建管理员账号
   - 收集静态文件

3. **访问系统**
   - 主页: http://localhost:8000
   - 管理后台: http://localhost:8000/admin
   - API文档: http://localhost:8000/api/docs

### 方法二：手动启动

```powershell
# 1. 启动 Docker 容器
docker-compose up -d

# 2. 等待数据库启动（约10秒）
timeout /t 10

# 3. 运行数据库迁移
docker-compose exec web python manage.py migrate

# 4. 创建超级用户
docker-compose exec web python manage.py createsuperuser

# 5. 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput

# 6. 查看日志
docker-compose logs -f
```

## 本地开发环境设置

### 1. 创建虚拟环境

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果遇到权限问题，请以管理员身份运行 PowerShell：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`：
```powershell
Copy-Item .env.example .env
```

### 4. 启动数据库（仅使用 Docker 运行数据库）

```powershell
docker-compose up -d db redis
```

### 5. 运行迁移

```powershell
python manage.py migrate
```

### 6. 创建超级用户

```powershell
python manage.py createsuperuser
```

### 7. 启动开发服务器

```powershell
# 终端1: Django 服务器
python manage.py runserver

# 终端2: Celery Worker
celery -A oj_project worker -l info --pool=solo

# 终端3: Celery Beat
celery -A oj_project beat -l info
```

注意：Windows 上 Celery 需要添加 `--pool=solo` 参数。

## 常用 Docker 命令

```powershell
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f [服务名]

# 进入容器
docker-compose exec web bash

# 停止服务
docker-compose stop

# 启动服务
docker-compose start

# 重启服务
docker-compose restart

# 完全停止并删除容器
docker-compose down

# 删除容器和数据卷（谨慎使用）
docker-compose down -v
```

## 常用 Django 命令

```powershell
# 创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic

# 启动开发服务器
python manage.py runserver

# 进入 Django Shell
python manage.py shell

# 清空数据库
python manage.py flush
```

## 数据库管理

### 连接数据库

```powershell
# 使用 Docker 容器连接
docker-compose exec db psql -U oj_user -d oj_database

# 在容器中执行 SQL 文件
docker-compose exec -T db psql -U oj_user -d oj_database < backup.sql
```

### 备份和恢复

```powershell
# 备份数据库
docker-compose exec db pg_dump -U oj_user oj_database > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# 恢复数据库
docker-compose exec -T db psql -U oj_user oj_database < backup.sql
```

## 开发工具

### 代码格式化

```powershell
# 安装开发工具（如果还没安装）
pip install black flake8

# 格式化代码
black .

# 检查代码风格
flake8 .
```

### 运行测试

```powershell
# 安装测试工具
pip install pytest pytest-django pytest-cov

# 运行所有测试
pytest

# 运行特定应用的测试
pytest oj_project/users/

# 生成覆盖率报告
pytest --cov=oj_project --cov-report=html
```

## 故障排除

### 1. Docker 容器启动失败

**问题**: 端口被占用
```powershell
# 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# 结束占用进程（将 PID 替换为实际进程ID）
taskkill /PID <进程ID> /F
```

**问题**: Docker Desktop 未运行
- 打开 Docker Desktop 应用程序
- 等待 Docker 完全启动

### 2. 数据库连接失败

```powershell
# 检查数据库容器状态
docker-compose ps db

# 查看数据库日志
docker-compose logs db

# 重启数据库
docker-compose restart db
```

### 3. 静态文件无法加载

```powershell
# 收集静态文件
python manage.py collectstatic --noinput

# 或在 Docker 中
docker-compose exec web python manage.py collectstatic --noinput
```

### 4. Celery 无法启动（Windows）

在 Windows 上运行 Celery Worker 需要添加 `--pool=solo` 参数：
```powershell
celery -A oj_project worker -l info --pool=solo
```

### 5. 权限错误

如果遇到 PowerShell 执行策略限制：
```powershell
# 以管理员身份运行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 项目结构概览

```
oj_project/
├── oj_project/          # 主项目目录
│   ├── settings.py      # 配置文件
│   ├── urls.py          # 路由配置
│   ├── celery.py        # Celery配置
│   ├── users/           # 用户模块
│   ├── problems/        # 题目模块
│   ├── submissions/     # 提交模块
│   ├── contests/        # 比赛模块
│   └── judge/           # 判题模块
├── static/              # 静态文件（CSS, JS等）
├── templates/           # HTML模板
├── media/               # 用户上传文件
├── logs/                # 日志文件
├── requirements.txt     # Python依赖
├── docker-compose.yml   # Docker配置
├── Dockerfile           # Docker镜像
├── start.bat            # Windows启动脚本
└── README.md            # 项目文档
```

## 下一步

1. **访问管理后台** (http://localhost:8000/admin)
   - 使用创建的超级用户登录
   - 添加测试数据

2. **查看 API 文档** (http://localhost:8000/api/docs)
   - 了解可用的 API 端点
   - 测试 API 调用

3. **开始开发**
   - 查看 README.md 了解详细架构
   - 修改模型和视图
   - 添加新功能

## 有用的链接

- Django 文档: https://docs.djangoproject.com/
- DRF 文档: https://www.django-rest-framework.org/
- Bootstrap 文档: https://getbootstrap.com/docs/
- Celery 文档: https://docs.celeryproject.org/

## 技术支持

如有问题，请查看：
1. README.md - 完整项目文档
2. GitHub Issues - 问题追踪
3. Docker 日志 - `docker-compose logs -f`



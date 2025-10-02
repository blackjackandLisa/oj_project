# OJ 系统安装检查清单

## 📋 前置要求检查

- [ ] Python 3.11+ 已安装
- [ ] Docker Desktop 已安装并运行
- [ ] Git 已安装（可选）
- [ ] 文本编辑器/IDE（推荐 VS Code）

## 🚀 快速启动步骤

### 方法 A：使用 Docker（推荐）

#### 1. 启动服务
```powershell
# Windows: 双击 start.bat 或运行
.\start.bat

# 或手动启动
docker-compose up -d
```

#### 2. 等待服务启动
- 等待约 10-15 秒让数据库完全启动

#### 3. 初始化数据库
```powershell
docker-compose exec web python manage.py migrate
```

#### 4. 创建管理员账号
```powershell
docker-compose exec web python manage.py createsuperuser
```
按提示输入：
- 用户名（例如：admin）
- 邮箱（例如：admin@example.com）
- 密码（输入两次）

#### 5. 收集静态文件
```powershell
docker-compose exec web python manage.py collectstatic --noinput
```

#### 6. 访问系统
- [ ] 主页: http://localhost:8000
- [ ] 管理后台: http://localhost:8000/admin
- [ ] API 文档: http://localhost:8000/api/docs

### 方法 B：本地开发环境

#### 1. 创建虚拟环境
```powershell
python -m venv venv
```

#### 2. 激活虚拟环境
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 如果遇到权限错误，运行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. 安装依赖
```powershell
pip install -r requirements.txt
```

#### 4. 配置环境变量
```powershell
# 复制环境变量示例文件
Copy-Item .env.example .env

# 编辑 .env 文件（使用记事本或编辑器）
notepad .env
```

#### 5. 启动数据库服务
```powershell
docker-compose up -d db redis
```

#### 6. 运行数据库迁移
```powershell
python manage.py migrate
```

#### 7. 创建超级用户
```powershell
python manage.py createsuperuser
```

#### 8. 启动开发服务器
```powershell
# 终端 1: Django
python manage.py runserver

# 终端 2: Celery Worker（新开一个终端）
.\venv\Scripts\Activate.ps1
celery -A oj_project worker -l info --pool=solo

# 终端 3: Celery Beat（新开一个终端）
.\venv\Scripts\Activate.ps1
celery -A oj_project beat -l info
```

## ✅ 验证安装

### 1. 检查 Docker 服务状态
```powershell
docker-compose ps
```

应该看到以下服务运行中：
- [x] oj_postgres (healthy)
- [x] oj_redis (healthy)
- [x] oj_web (running)
- [x] oj_celery (running)
- [x] oj_celery_beat (running)

### 2. 检查数据库连接
```powershell
docker-compose exec db psql -U oj_user -d oj_database -c "SELECT version();"
```

应该显示 PostgreSQL 版本信息。

### 3. 检查 Django 状态
访问 http://localhost:8000 应该看到首页。

### 4. 检查管理后台
访问 http://localhost:8000/admin 应该看到登录页面。

### 5. 检查 API 文档
访问 http://localhost:8000/api/docs 应该看到 Swagger UI。

## 🔧 故障排除

### 问题 1: Docker 无法启动
**症状**: `docker-compose up` 失败

**解决方案**:
```powershell
# 检查 Docker Desktop 是否运行
docker info

# 如果未运行，启动 Docker Desktop
# 等待完全启动后再试
```

### 问题 2: 端口冲突
**症状**: "port is already allocated"

**解决方案**:
```powershell
# 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# 停止占用进程或修改 docker-compose.yml 中的端口
```

### 问题 3: 数据库连接失败
**症状**: "could not connect to server"

**解决方案**:
```powershell
# 检查数据库容器状态
docker-compose ps db

# 查看数据库日志
docker-compose logs db

# 重启数据库
docker-compose restart db
```

### 问题 4: 静态文件 404
**症状**: CSS/JS 文件无法加载

**解决方案**:
```powershell
# 收集静态文件
python manage.py collectstatic --noinput

# 或在 Docker 中
docker-compose exec web python manage.py collectstatic --noinput
```

### 问题 5: Celery 无法启动（Windows）
**症状**: Celery worker 报错

**解决方案**:
```powershell
# Windows 需要添加 --pool=solo
celery -A oj_project worker -l info --pool=solo
```

### 问题 6: 权限错误（PowerShell）
**症状**: "cannot be loaded because running scripts is disabled"

**解决方案**:
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📦 依赖安装问题

### pip 安装失败
```powershell
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源（如果下载慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### psycopg2 安装失败
```powershell
# 使用 binary 版本（已在 requirements.txt 中）
pip install psycopg2-binary
```

## 🎯 下一步操作

安装完成后，建议：

1. **熟悉项目结构**
   - [ ] 阅读 `PROJECT_STRUCTURE.md`
   - [ ] 查看各个应用模块

2. **添加测试数据**
   - [ ] 登录管理后台 (http://localhost:8000/admin)
   - [ ] 创建几个测试题目
   - [ ] 创建几个测试用户

3. **测试 API**
   - [ ] 访问 API 文档 (http://localhost:8000/api/docs)
   - [ ] 测试各个 API 端点

4. **开始开发**
   - [ ] 阅读 `README.md` 了解架构
   - [ ] 查看待开发功能列表
   - [ ] 创建新的分支开始开发

## 📚 有用的命令

### Docker 命令
```powershell
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f [服务名]

# 进入容器
docker-compose exec web bash
```

### Django 命令
```powershell
# 创建迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 运行开发服务器
python manage.py runserver

# Django Shell
python manage.py shell

# 收集静态文件
python manage.py collectstatic
```

### 数据库命令
```powershell
# 连接数据库
docker-compose exec db psql -U oj_user -d oj_database

# 备份数据库
docker-compose exec db pg_dump -U oj_user oj_database > backup.sql

# 恢复数据库
docker-compose exec -T db psql -U oj_user oj_database < backup.sql
```

## 📞 获取帮助

如果遇到问题：

1. 查看项目文档：
   - `README.md` - 项目概览
   - `QUICKSTART.md` - 快速入门
   - `PROJECT_STRUCTURE.md` - 项目结构

2. 查看日志：
   ```powershell
   docker-compose logs -f
   ```

3. 检查 GitHub Issues（如果项目有仓库）

4. 查看 Django 官方文档

## ✨ 恭喜！

如果以上步骤都完成了，你的 OJ 系统已经成功搭建！

现在可以开始开发新功能了。祝编码愉快！🎉



# OJ系统 (Online Judge System)

一个基于Django的在线判题系统，支持C++和Python代码评测，具备完整的用户管理、题目管理、提交评测和排行榜功能。

## ✨ 功能特性

### 🎯 核心功能
- **用户系统**: 注册、登录、个人信息管理
- **题目管理**: 题目发布、编辑、分类管理
- **代码评测**: 支持C++和Python代码自动评测
- **排行榜**: 用户排名、题目统计
- **提交记录**: 详细的提交历史和结果

### 🔧 技术特性
- **多判题引擎**: 支持传统subprocess、Docker容器、Judger0专业沙箱
- **异步处理**: 基于Celery的异步任务队列
- **安全沙箱**: 多层安全防护，防止恶意代码
- **RESTful API**: 完整的API接口
- **响应式设计**: 支持移动端访问

### 🛡️ 安全特性
- **代码黑名单**: 防止危险函数调用
- **资源限制**: CPU、内存、文件大小限制
- **容器隔离**: Docker容器级别的代码执行隔离
- **审计日志**: 完整的操作和错误日志记录

## 🚀 快速开始

### 开发环境 (Windows + Docker)

```bash
# 1. 克隆项目
git clone https://github.com/blackjackandLisa/oj_project.git
cd oj_project

# 2. 启动开发环境
docker-compose up -d

# 3. 创建超级用户
docker-compose exec web python manage.py createsuperuser

# 4. 访问系统
# 网站: http://localhost:8000
# 管理后台: http://localhost:8000/admin/
```

### 生产环境 (Linux服务器)

```bash
# 1. 快速部署
wget https://raw.githubusercontent.com/blackjackandLisa/oj_project/main/scripts/quick-deploy.sh
chmod +x quick-deploy.sh
./quick-deploy.sh

# 2. 完整部署
wget https://raw.githubusercontent.com/blackjackandLisa/oj_project/main/scripts/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

## 📋 系统要求

### 开发环境
- Docker 20.10+
- Docker Compose 2.0+
- 4GB内存
- 10GB磁盘空间

### 生产环境
- Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- 2核心CPU + 4GB内存 (推荐8GB)
- 20GB磁盘空间
- 公网IP (可选)

## 🏗️ 技术架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Nginx     │────│  Django     │────│ PostgreSQL  │
│ (反向代理)   │    │ (Web应用)   │    │ (数据库)    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                   ┌─────────────┐    ┌─────────────┐
                   │   Celery    │────│    Redis    │
                   │ (任务队列)   │    │ (缓存/队列) │
                   └─────────────┘    └─────────────┘
```

### 技术栈
- **后端**: Django 4.2 + Django REST Framework
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **任务队列**: Celery + Redis
- **Web服务器**: Nginx + Gunicorn
- **容器化**: Docker + Docker Compose
- **前端**: Bootstrap 5 + jQuery

## 📁 项目结构

```
oj_project/
├── oj_project/              # Django项目配置
│   ├── settings.py          # 项目设置
│   ├── urls.py             # 主URL配置
│   └── celery.py           # Celery配置
├── oj_project/users/        # 用户应用
│   ├── models.py           # 用户模型
│   ├── views.py            # 用户视图
│   └── urls.py             # 用户URL
├── oj_project/problems/     # 题目应用
│   ├── models.py           # 题目模型
│   ├── views.py            # 题目视图
│   └── serializers.py      # API序列化器
├── oj_project/judge/        # 判题系统
│   ├── tasks.py            # 判题任务
│   ├── docker_judge.py     # Docker判题引擎
│   └── judge0_client.py    # Judger0客户端
├── templates/               # HTML模板
├── static/                  # 静态文件
├── nginx/                   # Nginx配置
├── scripts/                 # 部署脚本
├── docs/                    # 项目文档
├── docker-compose.yml       # 开发环境配置
├── docker-compose.prod.yml  # 生产环境配置
└── requirements.txt         # Python依赖
```

## 🔧 配置说明

### 环境变量
```bash
# 基础配置
DEBUG=0
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com,localhost

# 数据库配置
POSTGRES_DB=oj_database
POSTGRES_USER=oj_user
POSTGRES_PASSWORD=your-password

# Redis配置
REDIS_PASSWORD=your-redis-password

# 判题系统配置
JUDGE_METHOD=traditional  # traditional, docker, judge0
```

### 判题引擎选择
- **traditional**: 基于subprocess的传统判题 (开发环境)
- **docker**: 基于Docker容器的判题 (推荐生产环境)
- **judge0**: 基于Judger0的专业判题 (高安全要求)

## 📊 功能演示

### 用户功能
- ✅ 用户注册/登录
- ✅ 个人信息管理
- ✅ 头像上传
- ✅ 密码修改

### 题目功能
- ✅ 题目浏览
- ✅ 题目搜索和筛选
- ✅ 代码提交
- ✅ 实时评测结果

### 管理功能
- ✅ 题目管理
- ✅ 用户管理
- ✅ 系统监控
- ✅ 数据统计

## 🛠️ 开发指南

### 本地开发
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库
python manage.py migrate

# 3. 创建超级用户
python manage.py createsuperuser

# 4. 启动开发服务器
python manage.py runserver

# 5. 启动Celery
celery -A oj_project worker -l info
```

### API开发
```bash
# API文档
http://localhost:8000/api/docs/

# 主要API端点
GET  /api/problems/          # 题目列表
GET  /api/problems/{id}/     # 题目详情
POST /api/problems/{id}/submit/  # 提交代码
GET  /api/submissions/       # 提交记录
GET  /api/users/profile/     # 用户信息
```

## 🚀 部署指南

### 开发环境部署
```bash
# 使用Docker Compose
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 生产环境部署
```bash
# 快速部署
./scripts/quick-deploy.sh

# 完整部署
./scripts/deploy.sh

# 服务管理
./scripts/manage.sh start    # 启动服务
./scripts/manage.sh stop     # 停止服务
./scripts/manage.sh restart  # 重启服务
./scripts/manage.sh status   # 查看状态
./scripts/manage.sh logs     # 查看日志
```

详细部署文档请参考: [Linux部署指南](docs/LINUX_DEPLOYMENT_GUIDE.md)

## 📈 性能特性

### 并发能力
- **开发环境**: 3-5人同时使用
- **生产环境**: 100+人同时使用
- **判题并发**: 8-16个任务同时执行
- **数据库**: 支持高并发读写

### 扩展性
- 支持负载均衡
- 支持数据库集群
- 支持Redis集群
- 支持容器编排

## 🔒 安全特性

### 代码执行安全
- 容器隔离执行
- 资源使用限制
- 危险函数黑名单
- 网络访问控制

### 系统安全
- HTTPS/SSL加密
- 防火墙配置
- 入侵检测 (fail2ban)
- 安全头配置

## 📊 监控和维护

### 系统监控
```bash
# 健康检查
./scripts/manage.sh health

# 资源监控
docker stats

# 日志查看
./scripts/manage.sh logs
```

### 数据备份
```bash
# 自动备份
./scripts/backup.sh

# 定时备份
crontab -e
# 添加: 0 2 * * * /path/to/scripts/backup.sh
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 技术支持

- **问题反馈**: [GitHub Issues](https://github.com/blackjackandLisa/oj_project/issues)
- **功能建议**: [GitHub Discussions](https://github.com/blackjackandLisa/oj_project/discussions)
- **部署文档**: [部署指南](docs/LINUX_DEPLOYMENT_GUIDE.md)

## 🎉 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**项目状态**: ✅ 生产就绪  
**最后更新**: 2025-10-02  
**版本**: 1.0.0
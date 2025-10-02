# OJ 系统项目结构说明

## 完整目录结构

```
oj_project/                          # 项目根目录
│
├── oj_project/                      # Django 项目主配置目录
│   ├── __init__.py                  # Python 包初始化，包含 Celery 配置
│   ├── settings.py                  # Django 项目设置（★核心配置）
│   ├── urls.py                      # 主路由配置
│   ├── wsgi.py                      # WSGI 服务器入口
│   ├── asgi.py                      # ASGI 服务器入口（异步支持）
│   ├── celery.py                    # Celery 配置
│   │
│   ├── users/                       # 用户管理应用
│   │   ├── __init__.py
│   │   ├── admin.py                 # 后台管理配置
│   │   ├── apps.py                  # 应用配置
│   │   ├── models.py                # 数据模型（用户、个人资料等）
│   │   ├── views.py                 # 视图函数/类
│   │   ├── serializers.py           # DRF 序列化器（需创建）
│   │   ├── urls.py                  # URL 路由（需创建）
│   │   ├── tests.py                 # 单元测试
│   │   └── migrations/              # 数据库迁移文件
│   │       └── __init__.py
│   │
│   ├── problems/                    # 题目管理应用
│   │   ├── __init__.py
│   │   ├── admin.py                 # 后台管理（题目、标签等）
│   │   ├── apps.py
│   │   ├── models.py                # 数据模型（题目、测试用例、标签）
│   │   ├── views.py                 # 题目列表、详情等视图
│   │   ├── serializers.py           # API 序列化器（需创建）
│   │   ├── urls.py                  # 路由配置（需创建）
│   │   ├── tests.py
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── submissions/                 # 提交记录应用
│   │   ├── __init__.py
│   │   ├── admin.py                 # 后台管理提交记录
│   │   ├── apps.py
│   │   ├── models.py                # 数据模型（提交、结果）
│   │   ├── views.py                 # 提交记录查看
│   │   ├── serializers.py           # API 序列化器（需创建）
│   │   ├── urls.py                  # 路由配置（需创建）
│   │   ├── tasks.py                 # Celery 异步任务（需创建）
│   │   ├── tests.py
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── contests/                    # 比赛管理应用
│   │   ├── __init__.py
│   │   ├── admin.py                 # 后台管理比赛
│   │   ├── apps.py
│   │   ├── models.py                # 数据模型（比赛、排名）
│   │   ├── views.py                 # 比赛视图
│   │   ├── serializers.py           # API 序列化器（需创建）
│   │   ├── urls.py                  # 路由配置（需创建）
│   │   ├── tests.py
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   └── judge/                       # 判题系统应用
│       ├── __init__.py
│       ├── admin.py                 # 后台管理判题配置
│       ├── apps.py
│       ├── models.py                # 数据模型（判题配置）
│       ├── views.py                 # 判题 API
│       ├── tasks.py                 # Celery 判题任务（需创建）
│       ├── judge_client.py          # 判题客户端（需创建）
│       ├── tests.py
│       └── migrations/
│           └── __init__.py
│
├── static/                          # 静态文件目录
│   ├── css/                         # CSS 样式文件
│   │   └── style.css                # 自定义样式
│   ├── js/                          # JavaScript 文件
│   │   └── main.js                  # 主 JS 文件
│   ├── img/                         # 图片资源（需创建）
│   └── vendor/                      # 第三方库（需创建）
│
├── templates/                       # HTML 模板目录
│   ├── base.html                    # 基础模板
│   ├── index.html                   # 首页模板
│   ├── problems/                    # 题目相关模板（需创建）
│   │   ├── list.html
│   │   └── detail.html
│   ├── submissions/                 # 提交相关模板（需创建）
│   │   ├── list.html
│   │   └── detail.html
│   ├── contests/                    # 比赛相关模板（需创建）
│   │   ├── list.html
│   │   └── detail.html
│   └── users/                       # 用户相关模板（需创建）
│       ├── login.html
│       ├── register.html
│       └── profile.html
│
├── media/                           # 用户上传文件目录
│   ├── problems/                    # 题目相关文件（需创建）
│   ├── avatars/                     # 用户头像（需创建）
│   └── submissions/                 # 提交代码（需创建）
│
├── logs/                            # 日志文件目录
│   └── django.log                   # Django 日志（自动生成）
│
├── venv/                            # Python 虚拟环境（已创建）
│
├── .gitignore                       # Git 忽略文件配置
├── .dockerignore                    # Docker 忽略文件配置
├── .env.example                     # 环境变量示例文件
├── .env                             # 环境变量配置（需手动创建）
│
├── requirements.txt                 # Python 依赖包列表
├── pytest.ini                       # Pytest 配置文件
│
├── Dockerfile                       # Docker 镜像构建文件
├── docker-compose.yml               # Docker Compose 配置
│
├── manage.py                        # Django 管理脚本
├── start.bat                        # Windows 启动脚本
├── start.sh                         # Linux/Mac 启动脚本
│
├── README.md                        # 项目说明文档
├── QUICKSTART.md                    # 快速启动指南
└── PROJECT_STRUCTURE.md             # 本文件（项目结构说明）
```

## 核心文件说明

### 配置文件

| 文件 | 说明 |
|------|------|
| `oj_project/settings.py` | Django 核心配置，包括数据库、中间件、应用配置等 |
| `oj_project/urls.py` | 主路由配置，定义 URL 到视图的映射 |
| `oj_project/celery.py` | Celery 配置，用于异步任务处理 |
| `docker-compose.yml` | Docker 服务编排配置 |
| `requirements.txt` | Python 依赖包列表 |
| `.env` | 环境变量配置（敏感信息） |

### 应用模块

#### 1. users（用户模块）
**功能**: 用户注册、登录、个人信息管理

**需要创建的文件**:
- `serializers.py` - 用户数据序列化
- `urls.py` - 用户相关路由
- `forms.py` - 用户表单

**主要模型**:
- User（扩展 Django 默认用户）
- UserProfile（用户详细信息）

#### 2. problems（题目模块）
**功能**: 题目管理、分类、搜索

**需要创建的文件**:
- `serializers.py` - 题目数据序列化
- `urls.py` - 题目相关路由
- `filters.py` - 题目过滤器

**主要模型**:
- Problem（题目）
- TestCase（测试用例）
- Tag（标签）
- Category（分类）

#### 3. submissions（提交模块）
**功能**: 代码提交、结果查询

**需要创建的文件**:
- `serializers.py` - 提交数据序列化
- `urls.py` - 提交相关路由
- `tasks.py` - Celery 异步任务

**主要模型**:
- Submission（提交记录）
- SubmissionResult（提交结果）

#### 4. contests（比赛模块）
**功能**: 比赛创建、管理、排名

**需要创建的文件**:
- `serializers.py` - 比赛数据序列化
- `urls.py` - 比赛相关路由
- `ranking.py` - 排名计算

**主要模型**:
- Contest（比赛）
- ContestProblem（比赛题目）
- ContestParticipant（参赛者）
- ContestRanking（排名）

#### 5. judge（判题模块）
**功能**: 代码编译、运行、评测

**需要创建的文件**:
- `tasks.py` - Celery 判题任务
- `judge_client.py` - 判题客户端
- `languages.py` - 语言配置
- `result_codes.py` - 结果代码定义

**主要功能**:
- 代码安全执行
- 时间和内存限制
- 多语言支持

## 数据库设计概览

### 用户表 (users_user)
- id, username, email, password
- created_at, updated_at

### 题目表 (problems_problem)
- id, title, description, difficulty
- time_limit, memory_limit
- input_format, output_format
- sample_input, sample_output

### 提交表 (submissions_submission)
- id, user_id, problem_id, code
- language, status, score
- execution_time, memory_used
- created_at

### 比赛表 (contests_contest)
- id, title, description
- start_time, end_time
- type (ACM/OI)

## API 端点规划

### 用户 API
```
POST   /api/users/register/       - 注册
POST   /api/users/login/          - 登录
GET    /api/users/profile/        - 获取个人信息
PUT    /api/users/profile/        - 更新个人信息
```

### 题目 API
```
GET    /api/problems/             - 题目列表
GET    /api/problems/{id}/        - 题目详情
POST   /api/problems/             - 创建题目（管理员）
PUT    /api/problems/{id}/        - 更新题目（管理员）
DELETE /api/problems/{id}/        - 删除题目（管理员）
```

### 提交 API
```
GET    /api/submissions/          - 提交列表
GET    /api/submissions/{id}/     - 提交详情
POST   /api/submissions/          - 提交代码
```

### 比赛 API
```
GET    /api/contests/             - 比赛列表
GET    /api/contests/{id}/        - 比赛详情
GET    /api/contests/{id}/rank/   - 比赛排名
POST   /api/contests/{id}/join/   - 加入比赛
```

## 下一步开发任务

### 阶段一：基础功能（1-2周）
1. 完善用户模型和认证系统
2. 实现题目的 CRUD 操作
3. 创建基本的前端页面
4. 实现代码提交功能

### 阶段二：判题系统（2-3周）
1. 设计判题队列
2. 实现代码编译和运行
3. 添加多语言支持
4. 实现测试用例管理

### 阶段三：高级功能（2-3周）
1. 实现比赛系统
2. 添加实时排名
3. 实现代码高亮和编辑器
4. 添加统计和分析功能

### 阶段四：优化和部署（1-2周）
1. 性能优化
2. 添加缓存
3. 编写测试
4. 部署到生产环境

## 技术栈详细说明

### 后端
- **Django 4.2**: Web 框架
- **Django REST Framework**: RESTful API
- **PostgreSQL**: 关系型数据库
- **Redis**: 缓存和消息队列
- **Celery**: 异步任务队列

### 前端
- **Bootstrap 5**: UI 框架
- **jQuery**: JavaScript 库
- **CodeMirror/Monaco Editor**: 代码编辑器（待集成）

### 开发工具
- **Docker**: 容器化
- **Git**: 版本控制
- **pytest**: 测试框架
- **Black/Flake8**: 代码格式化和检查

## 参考资源

- Django 官方文档: https://docs.djangoproject.com/
- DRF 文档: https://www.django-rest-framework.org/
- PostgreSQL 文档: https://www.postgresql.org/docs/
- Celery 文档: https://docs.celeryproject.org/
- Bootstrap 文档: https://getbootstrap.com/docs/

## 注意事项

1. **安全性**
   - 不要将 `.env` 文件提交到 Git
   - 生产环境使用强密码
   - 启用 HTTPS

2. **性能优化**
   - 使用数据库索引
   - 合理使用缓存
   - 优化 SQL 查询

3. **代码规范**
   - 遵循 PEP 8 规范
   - 编写单元测试
   - 添加代码注释

4. **部署**
   - 使用环境变量管理配置
   - 定期备份数据库
   - 监控系统性能



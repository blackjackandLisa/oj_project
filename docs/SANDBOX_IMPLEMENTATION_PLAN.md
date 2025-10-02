# 🛡️ 安全沙箱渐进式实施计划

## 📋 总体规划

我们将分3个阶段逐步实施完整的安全沙箱，每个阶段都可以独立运行，后续阶段在前一阶段基础上增强。

### 阶段概览

| 阶段 | 方案 | 安全等级 | 预计时间 | 状态 |
|-----|------|---------|---------|------|
| **阶段1** | 快速加固 + 基础限制 | 🟡 中低 | 30分钟 | 🔄 进行中 |
| **阶段2** | Docker容器隔离 | 🟡 中 | 1-2天 | ⏳ 待开始 |
| **阶段3** | Judger0专业沙箱 | 🟢 高 | 1周 | ⏳ 待开始 |

---

## 🎯 阶段1：快速加固 + 基础限制

**目标**：立即提升基础安全性，作为临时保护措施

**时间**：30分钟

### 1.1 应用安全加固代码

**任务清单**：
- [x] 创建安全加固版代码（tasks_secure.py）
- [ ] 备份现有判题代码
- [ ] 应用安全加固版
- [ ] 重启Celery服务
- [ ] 测试判题功能

### 1.2 添加数据库审计日志

**目标**：记录所有提交，便于安全审计

### 1.3 添加实时监控

**目标**：监控资源使用，及时发现异常

### 1.4 配置访问限制

**目标**：限制系统访问，降低风险面

---

## 🐳 阶段2：Docker容器隔离

**目标**：为每次判题创建独立的临时容器，实现强隔离

**时间**：1-2天

### 2.1 准备工作

- [ ] 安装Docker Python SDK
- [ ] 准备判题镜像（Python、C++）
- [ ] 配置Docker守护进程
- [ ] 设计容器生命周期管理

### 2.2 实现Docker判题引擎

- [ ] 创建Docker判题客户端
- [ ] 实现Python容器判题
- [ ] 实现C++容器判题
- [ ] 添加容器资源限制
- [ ] 实现容器清理机制

### 2.3 性能优化

- [ ] 容器镜像缓存
- [ ] 容器复用策略
- [ ] 并发控制
- [ ] 超时处理

### 2.4 测试验证

- [ ] 功能测试
- [ ] 安全测试
- [ ] 性能测试
- [ ] 压力测试

---

## 🏆 阶段3：Judger0专业沙箱

**目标**：集成成熟的Judger0沙箱，达到生产级安全水平

**时间**：1周

### 3.1 部署Judger0

- [ ] 配置docker-compose
- [ ] 部署Judger0服务
- [ ] 配置数据库
- [ ] 验证服务可用性

### 3.2 集成Judger0 API

- [ ] 创建Judger0客户端
- [ ] 实现提交接口
- [ ] 实现结果查询
- [ ] 错误处理

### 3.3 迁移现有系统

- [ ] 适配语言ID映射
- [ ] 适配测试用例格式
- [ ] 迁移历史数据
- [ ] 更新前端交互

### 3.4 监控和维护

- [ ] 健康检查
- [ ] 性能监控
- [ ] 日志收集
- [ ] 告警配置

---

## 📅 详细实施步骤

## 阶段1详细步骤（今天完成）

### 步骤1.1：应用安全加固版本 ⏱️ 5分钟

```bash
# 1. 备份原文件
docker-compose exec web cp oj_project/judge/tasks.py oj_project/judge/tasks_backup.py

# 2. 应用安全版本
docker-compose exec web cp oj_project/judge/tasks_secure.py oj_project/judge/tasks.py

# 3. 重启Celery
docker-compose restart celery celery-beat

# 4. 查看日志确认启动
docker-compose logs celery | tail -20
```

### 步骤1.2：添加提交审计日志 ⏱️ 10分钟

创建 `oj_project/judge/audit.py`：

```python
import logging
from datetime import datetime

logger = logging.getLogger('judge.audit')

def log_submission(submission, event, details=None):
    """记录提交审计日志"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'submission_id': submission.id,
        'user_id': submission.user.id,
        'username': submission.user.username,
        'problem_id': submission.problem.id,
        'language': submission.language,
        'status': submission.status,
        'event': event,
        'details': details or {}
    }
    logger.info(f"AUDIT: {log_data}")
```

### 步骤1.3：添加监控端点 ⏱️ 10分钟

创建健康检查和监控视图

### 步骤1.4：配置访问控制 ⏱️ 5分钟

- 限制注册（需要邀请码）
- 添加验证码
- 限流（rate limiting）

---

## 阶段2详细步骤（明天-后天）

### 步骤2.1：安装依赖 ⏱️ 5分钟

```bash
# 添加到requirements.txt
docker==6.1.3

# 安装
docker-compose exec web pip install docker==6.1.3
```

### 步骤2.2：创建Docker判题引擎 ⏱️ 4小时

详细代码见后续章节

### 步骤2.3：测试和优化 ⏱️ 3小时

### 步骤2.4：文档和部署 ⏱️ 1小时

---

## 阶段3详细步骤（下周）

### 步骤3.1：部署Judger0 ⏱️ 2小时

```yaml
# docker-compose.yml 添加
judger0-server:
  image: judge0/judge0:1.13.0
  volumes:
    - ./judger0.conf:/judge0.conf:ro
  privileged: true
  <<: *logging
  restart: always

judger0-workers:
  image: judge0/judge0:1.13.0
  command: ["./scripts/workers"]
  privileged: true
  restart: always
```

### 步骤3.2-3.4：集成和优化 ⏱️ 1-2天

---

## 🎯 立即开始阶段1

让我们现在开始执行阶段1的第一步！

准备好了吗？我将：
1. ✅ 备份现有代码
2. ✅ 应用安全加固版
3. ✅ 重启服务
4. ✅ 测试验证
5. ✅ 添加审计日志
6. ✅ 添加监控端点

---

**下一步行动**：
- 立即执行阶段1（30分钟内完成）
- 今天完成基础安全加固
- 明天开始Docker容器隔离
- 下周集成Judger0

**当前优先级**：🔴 高 - 立即执行
**预期完成时间**：今天


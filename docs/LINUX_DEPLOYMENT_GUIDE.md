# OJ系统Linux服务器部署指南

## 📋 部署概述

本指南将帮助您在Linux服务器上部署OJ系统，包括自动安装、配置和启动所有必要的服务。

### 🎯 部署架构

```
Internet → Nginx (反向代理) → Gunicorn (Django) → PostgreSQL + Redis
                                    ↓
                              Celery Workers (判题)
```

### ✅ 支持的系统

- **Ubuntu 20.04+** (推荐)
- **CentOS 7+**
- **Debian 10+**

### 📊 系统要求

- **CPU**: 2核心以上
- **内存**: 4GB以上 (推荐8GB)
- **磁盘**: 20GB以上可用空间
- **网络**: 公网IP (可选，用于域名访问)

---

## 🚀 快速部署

### 方法1: 一键自动部署 (推荐)

```bash
# 1. 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/oj_project/main/scripts/deploy.sh
chmod +x deploy.sh

# 2. 运行部署脚本
./deploy.sh
```

### 方法2: 手动部署

```bash
# 1. 克隆代码
git clone https://github.com/your-username/oj_project.git
cd oj_project

# 2. 配置环境变量
cp env.prod.template .env.prod
vim .env.prod  # 编辑配置

# 3. 运行部署脚本
./scripts/deploy.sh
```

---

## 📝 详细部署步骤

### 步骤1: 系统准备

#### 1.1 更新系统
```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.2 安装基础工具
```bash
sudo apt install -y curl wget git vim htop
```

### 步骤2: 安装Docker

#### 2.1 安装Docker Engine
```bash
# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER
```

#### 2.2 安装Docker Compose
```bash
# 获取最新版本
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)

# 下载并安装
sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose
```

### 步骤3: 配置环境

#### 3.1 创建部署目录
```bash
sudo mkdir -p /opt/oj-system
sudo chown $USER:$USER /opt/oj-system
cd /opt/oj-system
```

#### 3.2 克隆代码
```bash
git clone https://github.com/your-username/oj_project.git
cd oj_project
```

#### 3.3 配置环境变量
```bash
# 复制环境变量模板
cp env.prod.template .env.prod

# 编辑环境变量
vim .env.prod
```

**重要配置项:**
```bash
# 基础配置
DEBUG=0
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost,127.0.0.1

# 数据库配置
POSTGRES_PASSWORD=your-secure-database-password

# Redis配置
REDIS_PASSWORD=your-secure-redis-password

# 域名配置
DOMAIN_NAME=your-domain.com
SSL_EMAIL=your-email@domain.com
```

### 步骤4: SSL证书配置

#### 4.1 使用Let's Encrypt (推荐)
```bash
# 安装certbot
sudo apt install -y certbot

# 生成证书
sudo certbot certonly --standalone -d your-domain.com --non-interactive --agree-tos --email your-email@domain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/cert.pem ssl/key.pem
```

#### 4.2 使用自签名证书 (开发环境)
```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
```

### 步骤5: 启动服务

#### 5.1 构建和启动
```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

#### 5.2 初始化数据库
```bash
# 运行迁移
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 创建超级用户
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 收集静态文件
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 步骤6: 配置防火墙

```bash
# 启用UFW
sudo ufw enable

# 允许SSH
sudo ufw allow ssh

# 允许HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许Flower监控 (可选)
sudo ufw allow 5555/tcp
```

---

## 🔧 服务管理

### 使用管理脚本

```bash
# 查看帮助
./scripts/manage.sh help

# 启动服务
./scripts/manage.sh start

# 停止服务
./scripts/manage.sh stop

# 重启服务
./scripts/manage.sh restart

# 查看状态
./scripts/manage.sh status

# 查看日志
./scripts/manage.sh logs

# 健康检查
./scripts/manage.sh health

# 进入Web容器
./scripts/manage.sh shell

# 进入数据库
./scripts/manage.sh db-shell
```

### 手动管理

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart web

# 进入容器
docker-compose -f docker-compose.prod.yml exec web bash
```

---

## 📊 监控和维护

### 系统监控

#### 1. 服务健康检查
```bash
# 检查所有服务
./scripts/manage.sh health

# 检查Web服务
curl -f http://localhost/health/

# 检查数据库
docker-compose -f docker-compose.prod.yml exec db pg_isready -U oj_user -d oj_database

# 检查Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

#### 2. 资源监控
```bash
# 查看容器资源使用
docker stats

# 查看系统资源
htop

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

#### 3. 日志监控
```bash
# 查看应用日志
tail -f logs/django.log

# 查看Nginx日志
docker-compose -f docker-compose.prod.yml logs -f nginx

# 查看Celery日志
docker-compose -f docker-compose.prod.yml logs -f celery
```

### 数据备份

#### 1. 自动备份
```bash
# 运行备份脚本
./scripts/backup.sh

# 设置定时备份 (crontab)
crontab -e
# 添加: 0 2 * * * /opt/oj-system/oj_project/scripts/backup.sh
```

#### 2. 手动备份
```bash
# 备份数据库
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U oj_user -d oj_database > backup.sql

# 备份媒体文件
tar -czf media_backup.tar.gz media/

# 备份配置文件
tar -czf config_backup.tar.gz .env.prod nginx/ ssl/
```

### 数据恢复

```bash
# 恢复数据库
docker-compose -f docker-compose.prod.yml exec -T db psql -U oj_user -d oj_database < backup.sql

# 恢复媒体文件
tar -xzf media_backup.tar.gz

# 恢复配置文件
tar -xzf config_backup.tar.gz
```

---

## 🔒 安全配置

### 1. 防火墙配置
```bash
# 配置UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2ban配置
```bash
# 安装fail2ban
sudo apt install -y fail2ban

# 配置fail2ban
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
EOF

# 重启fail2ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

### 3. SSL/TLS配置
- 使用Let's Encrypt免费证书
- 配置HSTS安全头
- 启用TLS 1.2+协议
- 使用强加密套件

### 4. 数据库安全
- 使用强密码
- 限制网络访问
- 定期备份
- 监控异常访问

---

## 🚀 性能优化

### 1. 数据库优化
```sql
-- PostgreSQL配置优化
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

### 2. Nginx优化
```nginx
# 启用Gzip压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;

# 启用HTTP/2
listen 443 ssl http2;

# 配置缓存
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Gunicorn优化
```bash
# 调整worker数量
--workers 4
--threads 2
--worker-class gthread
--max-requests 1000
--max-requests-jitter 100
```

### 4. Celery优化
```bash
# 调整并发数
--concurrency 16
--prefetch-multiplier 1
--max-tasks-per-child 1000
```

---

## 🔧 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs

# 检查端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# 检查磁盘空间
df -h
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml exec db pg_isready -U oj_user -d oj_database

# 检查环境变量
docker-compose -f docker-compose.prod.yml exec web env | grep DATABASE

# 重启数据库
docker-compose -f docker-compose.prod.yml restart db
```

#### 3. 静态文件404
```bash
# 重新收集静态文件
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 检查Nginx配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 重启Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

#### 4. 判题系统异常
```bash
# 检查Celery状态
docker-compose -f docker-compose.prod.yml exec celery celery -A oj_project inspect ping

# 检查Redis连接
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# 重启Celery
docker-compose -f docker-compose.prod.yml restart celery
```

### 日志分析

#### 1. 应用日志
```bash
# 查看Django日志
tail -f logs/django.log

# 查看错误日志
grep "ERROR" logs/django.log

# 查看访问日志
tail -f logs/access.log
```

#### 2. 系统日志
```bash
# 查看系统日志
sudo journalctl -u docker

# 查看Nginx日志
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## 📈 扩展部署

### 1. 负载均衡
```nginx
# 多实例配置
upstream oj_backend {
    server web1:8000;
    server web2:8000;
    server web3:8000;
    keepalive 32;
}
```

### 2. 数据库集群
```yaml
# PostgreSQL主从配置
services:
  db-master:
    image: postgres:15-alpine
    environment:
      POSTGRES_REPLICATION_MODE: master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: replicator_password
  
  db-slave:
    image: postgres:15-alpine
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_HOST: db-master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: replicator_password
```

### 3. Redis集群
```yaml
# Redis哨兵配置
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes
  
  redis-slave:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379
  
  redis-sentinel:
    image: redis:7-alpine
    command: redis-sentinel /usr/local/etc/redis/sentinel.conf
```

---

## 📞 技术支持

### 获取帮助

1. **查看日志**: `./scripts/manage.sh logs`
2. **健康检查**: `./scripts/manage.sh health`
3. **查看状态**: `./scripts/manage.sh status`
4. **进入容器**: `./scripts/manage.sh shell`

### 常用命令

```bash
# 快速重启
./scripts/manage.sh restart

# 查看资源使用
docker stats

# 清理无用资源
./scripts/manage.sh clean

# 备份数据
./scripts/backup.sh

# 更新系统
./scripts/manage.sh update
```

---

## 🎉 部署完成

部署完成后，您可以访问：

- **网站**: http://your-domain.com (或 http://localhost)
- **管理后台**: http://your-domain.com/admin/
- **Flower监控**: http://your-domain.com:5555/
- **API文档**: http://your-domain.com/api/docs/

### 下一步

1. 修改默认密码
2. 配置邮件服务
3. 设置定时备份
4. 配置监控告警
5. 优化性能参数

---

**最后更新**: 2025-10-02  
**版本**: 1.0.0  
**状态**: ✅ 生产就绪

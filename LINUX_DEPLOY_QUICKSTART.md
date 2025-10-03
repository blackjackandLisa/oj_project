# Linux服务器部署快速指南

## 🚀 一键部署命令

```bash
# 方法1: 快速部署（推荐新手）
curl -fsSL https://raw.githubusercontent.com/blackjackandLisa/oj_project/main/scripts/quick-deploy.sh | bash

# 方法2: 完整部署（推荐生产环境）
curl -fsSL https://raw.githubusercontent.com/blackjackandLisa/oj_project/main/scripts/deploy.sh | bash
```

## 📋 手动部署步骤

### 步骤1: 环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git vim htop

# 安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以使docker组生效
newgrp docker
```

### 步骤2: 克隆项目

```bash
# 创建部署目录
sudo mkdir -p /opt/oj-system
sudo chown $USER:$USER /opt/oj-system
cd /opt/oj-system

# 克隆项目
git clone https://github.com/blackjackandLisa/oj_project.git
cd oj_project
```

### 步骤3: 配置环境

```bash
# 复制环境配置
cp env.prod.template .env.prod

# 编辑配置文件
nano .env.prod
```

**重要配置项：**
```bash
# 基础配置
DEBUG=0
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# 数据库配置
POSTGRES_PASSWORD=your-secure-database-password

# Redis配置  
REDIS_PASSWORD=your-secure-redis-password

# 判题系统配置（选择一种）
JUDGE_METHOD=judge0        # 推荐：专业级安全
# JUDGE_METHOD=docker      # 备选：容器隔离
# JUDGE_METHOD=traditional # 开发：快速判题

# 域名配置（如果有域名）
DOMAIN_NAME=your-domain.com
SSL_EMAIL=your-email@domain.com
```

### 步骤4: 生成SSL证书

**有域名的情况：**
```bash
# 安装certbot
sudo apt install -y certbot

# 生成Let's Encrypt证书
sudo certbot certonly --standalone -d your-domain.com --email your-email@domain.com --agree-tos --non-interactive

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/cert.pem ssl/key.pem
```

**没有域名的情况：**
```bash
# 生成自签名证书
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
```

### 步骤5: 启动服务

```bash
# 构建并启动服务
docker-compose -f docker-compose.prod.yml up -d --build

# 等待服务启动（约2-3分钟）
sleep 120

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 步骤6: 初始化数据库

```bash
# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 创建超级用户
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 收集静态文件
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 步骤7: 配置防火墙

```bash
# 启用防火墙
sudo ufw enable

# 允许必要端口
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5555/tcp  # Flower监控（可选）

# 检查防火墙状态
sudo ufw status
```

## ✅ 验证部署

### 健康检查

```bash
# 检查所有服务状态
curl -f http://localhost/health/ || echo "服务未就绪"

# 检查Judger0（如果启用）
curl -f http://localhost:2358/system_info || echo "Judger0未就绪"

# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

### 测试功能

```bash
# 运行Judger0测试（如果启用）
docker-compose -f docker-compose.prod.yml exec web python test_judge0.py

# 检查系统指标
curl -f http://localhost:8000/judge/health/
```

## 🌐 访问系统

部署成功后，您可以访问：

- **网站**: http://your-domain.com (或 http://服务器IP)
- **管理后台**: http://your-domain.com/admin/
- **Flower监控**: http://your-domain.com:5555/
- **Judger0状态**: http://your-domain.com:2358/system_info

## 🔧 服务管理

```bash
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

# 数据备份
./scripts/backup.sh
```

## 🚨 故障排除

### 常见问题

1. **服务启动失败**
```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs

# 检查端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

2. **Judger0启动缓慢**
```bash
# Judger0需要下载大量镜像，首次启动需要5-10分钟
docker-compose -f docker-compose.prod.yml logs judge0-server -f
```

3. **数据库连接失败**
```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml exec db pg_isready -U oj_user -d oj_database

# 重启数据库
docker-compose -f docker-compose.prod.yml restart db
```

4. **内存不足**
```bash
# 检查内存使用
free -h
docker stats

# 如果内存不足，可以禁用Judger0
echo "JUDGE_METHOD=docker" >> .env.prod
docker-compose -f docker-compose.prod.yml restart
```

## 📊 性能优化

### 小型服务器（2GB内存）
```bash
# 使用Docker判题，关闭Judger0
echo "JUDGE_METHOD=docker" >> .env.prod

# 减少worker数量
sed -i 's/--concurrency=16/--concurrency=8/g' docker-compose.prod.yml
```

### 大型服务器（8GB+内存）
```bash
# 使用Judger0专业判题
echo "JUDGE_METHOD=judge0" >> .env.prod

# 增加worker数量
sed -i 's/--concurrency=16/--concurrency=32/g' docker-compose.prod.yml
```

## 🔒 安全建议

1. **修改默认密码**
2. **设置强密码**
3. **定期备份数据**
4. **监控系统日志**
5. **及时更新系统**

## 📞 获取帮助

- **项目文档**: [GitHub仓库](https://github.com/blackjackandLisa/oj_project)
- **部署指南**: `docs/LINUX_DEPLOYMENT_GUIDE.md`
- **判题架构**: `docs/JUDGE_SYSTEM_ARCHITECTURE.md`
- **问题反馈**: [GitHub Issues](https://github.com/blackjackandLisa/oj_project/issues)

---

**部署版本**: 1.0.0  
**最后更新**: 2025-10-02  
**支持系统**: Ubuntu 20.04+, CentOS 7+, Debian 10+

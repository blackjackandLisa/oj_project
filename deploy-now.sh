#!/bin/bash

# OJ系统快速部署脚本（简化版）
# 在项目目录中执行：bash deploy-now.sh

set -e

echo "🚀 开始OJ系统一键部署..."
echo "================================"

# 检查是否在项目目录
if [[ ! -f "docker-compose.prod.yml" ]]; then
    echo "❌ 请在OJ项目根目录中运行此脚本"
    exit 1
fi

# 1. 安装Docker和Docker Compose
echo "📦 安装Docker和Docker Compose..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "✅ Docker安装完成"
else
    echo "✅ Docker已安装"
fi

if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    echo "✅ Docker Compose安装完成"
else
    echo "✅ Docker Compose已安装"
fi

# 2. 获取服务器信息
echo "🌐 获取服务器信息..."
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "$SERVER_IP")
echo "服务器IP: $SERVER_IP"
echo "公网IP: $PUBLIC_IP"

# 3. 创建环境配置
echo "⚙️  创建环境配置..."
cat > .env.prod << EOF
# 快速部署配置
DEBUG=0
SECRET_KEY=django-secret-$(openssl rand -hex 32)
ALLOWED_HOSTS=$PUBLIC_IP,$SERVER_IP,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://$PUBLIC_IP

# 数据库配置
POSTGRES_DB=oj_database
POSTGRES_USER=oj_user
POSTGRES_PASSWORD=oj_db_$(openssl rand -hex 16)

# Redis配置
REDIS_PASSWORD=oj_redis_$(openssl rand -hex 16)

# 判题系统配置
JUDGE_METHOD=docker
DOCKER_JUDGE_ENABLED=True
DOCKER_PYTHON_IMAGE=oj-python-judge
DOCKER_CPP_IMAGE=oj-cpp-judge

# Judger0配置
JUDGE_SERVER_URL=http://judge0-server:2358
JUDGE_TOKEN=

# 域名配置
DOMAIN_NAME=$PUBLIC_IP
SSL_EMAIL=admin@$PUBLIC_IP
EOF
echo "✅ 环境配置创建完成"

# 4. 生成SSL证书
echo "🔒 生成SSL证书..."
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=CN/ST=State/L=City/O=OJ-System/CN=$PUBLIC_IP" > /dev/null 2>&1
echo "✅ SSL证书生成完成"

# 5. 配置防火墙
echo "🛡️  配置防火墙..."
sudo ufw --force enable > /dev/null 2>&1
sudo ufw allow ssh > /dev/null 2>&1
sudo ufw allow 80/tcp > /dev/null 2>&1
sudo ufw allow 443/tcp > /dev/null 2>&1
sudo ufw allow 5555/tcp > /dev/null 2>&1
echo "✅ 防火墙配置完成"

# 6. 构建Docker镜像
echo "🐳 构建Docker判题镜像..."
docker build -f judge_images/Dockerfile.python -t oj-python-judge . > /dev/null 2>&1
docker build -f judge_images/Dockerfile.cpp -t oj-cpp-judge . > /dev/null 2>&1
echo "✅ Docker镜像构建完成"

# 7. 启动服务
echo "🚀 启动所有服务..."
docker-compose -f docker-compose.prod.yml up -d --build
echo "⏳ 等待服务启动（30秒）..."
sleep 30

# 8. 初始化数据库
echo "💾 初始化数据库..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput > /dev/null 2>&1

# 创建管理员账户
echo "👨‍💼 创建管理员账户..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('管理员账户创建成功')
else:
    print('管理员账户已存在')
"

# 9. 健康检查
echo "🔍 执行健康检查..."
sleep 10
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    echo "✅ 系统健康检查通过"
else
    echo "⚠️  系统可能仍在启动中，请稍后检查"
fi

# 10. 显示部署结果
echo ""
echo "🎉 部署完成！"
echo "================================"
echo "📋 访问信息："
echo "  网站首页: http://$PUBLIC_IP"
echo "  管理后台: http://$PUBLIC_IP/admin/"
echo "  系统监控: http://$PUBLIC_IP:5555/"
echo ""
echo "👨‍💼 管理员账户："
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "🔧 常用命令："
echo "  查看状态: docker-compose -f docker-compose.prod.yml ps"
echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "📚 更多帮助："
echo "  ./scripts/manage.sh help"
echo "  cat docs/LINUX_DEPLOYMENT_GUIDE.md"
echo ""
echo "✨ 现在您可以开始使用OJ系统了！"

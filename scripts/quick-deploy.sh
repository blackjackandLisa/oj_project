#!/bin/bash

# OJ系统快速部署脚本
# 适用于快速测试和演示环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 创建环境配置
create_env_config() {
    log_info "创建环境配置..."
    
    if [[ ! -f ".env.prod" ]]; then
        cat > .env.prod << EOF
# 快速部署配置
DEBUG=0
SECRET_KEY=django-insecure-quick-deploy-key-change-in-production-$(date +%s)
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,$(hostname -I | awk '{print $1}')
CORS_ALLOWED_ORIGINS=http://localhost:3000

# 数据库配置
POSTGRES_DB=oj_database
POSTGRES_USER=oj_user
POSTGRES_PASSWORD=oj_password_2024

# Redis配置
REDIS_PASSWORD=redis_password_2024

# 判题系统配置
JUDGE_METHOD=docker
DOCKER_JUDGE_ENABLED=True
DOCKER_PYTHON_IMAGE=oj-python-judge
DOCKER_CPP_IMAGE=oj-cpp-judge

# Judger0配置（备用）
JUDGE_SERVER_URL=http://judge0-server:2358
JUDGE_TOKEN=

# 域名配置
DOMAIN_NAME=localhost
SSL_EMAIL=admin@localhost
EOF
        log_success "环境配置文件已创建"
    else
        log_warning "环境配置文件已存在，跳过创建"
    fi
}

# 生成自签名证书
generate_ssl_cert() {
    log_info "生成自签名SSL证书..."
    
    mkdir -p ssl
    
    if [[ ! -f "ssl/cert.pem" ]]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem \
            -out ssl/cert.pem \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
        log_success "SSL证书生成完成"
    else
        log_warning "SSL证书已存在，跳过生成"
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 停止现有服务
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # 构建并启动
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    log_success "服务启动完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    sleep 10
    
    # 运行迁移
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
    
    # 创建超级用户
    log_info "创建超级用户..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('超级用户创建成功: admin/admin123')
else:
    print('超级用户已存在')
"
    
    # 收集静态文件
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
    
    log_success "数据库初始化完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local failed=0
    
    # 检查Web服务
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        log_success "✓ Web服务正常"
    else
        log_error "✗ Web服务异常"
        failed=1
    fi
    
    # 检查数据库
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U oj_user -d oj_database > /dev/null 2>&1; then
        log_success "✓ 数据库正常"
    else
        log_error "✗ 数据库异常"
        failed=1
    fi
    
    # 检查Redis
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "✓ Redis正常"
    else
        log_error "✗ Redis异常"
        failed=1
    fi
    
    if [[ $failed -eq 0 ]]; then
        log_success "所有服务健康检查通过"
        return 0
    else
        log_error "部分服务健康检查失败"
        return 1
    fi
}

# 显示部署信息
show_info() {
    log_success "快速部署完成！"
    echo
    log_info "访问信息:"
    log_info "  网站地址: http://localhost"
    log_info "  管理后台: http://localhost/admin/"
    log_info "  用户名: admin"
    log_info "  密码: admin123"
    log_info "  Flower监控: http://localhost:5555/"
    echo
    log_info "服务管理:"
    log_info "  查看状态: docker-compose -f docker-compose.prod.yml ps"
    log_info "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
    log_info "  停止服务: docker-compose -f docker-compose.prod.yml down"
    echo
    log_warning "注意: 这是快速部署配置，仅适用于测试环境！"
    log_warning "生产环境请使用完整的部署脚本并修改默认密码！"
}

# 主函数
main() {
    log_info "开始快速部署OJ系统..."
    
    check_docker
    create_env_config
    generate_ssl_cert
    start_services
    init_database
    
    if health_check; then
        show_info
    else
        log_error "部署失败，请检查日志"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

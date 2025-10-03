#!/bin/bash

# OJ系统一键自动部署脚本
# 适用于已克隆项目的Linux服务器

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_cmd() {
    echo -e "${CYAN}[CMD]${NC} $1"
}

# 显示欢迎信息
show_welcome() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    OJ系统一键自动部署                        ║"
    echo "║                                                              ║"
    echo "║  🚀 功能特性：                                               ║"
    echo "║     • 用户管理系统                                           ║"
    echo "║     • 题目管理和代码判题                                     ║"
    echo "║     • 三种判题引擎（Traditional/Docker/Judger0）             ║"
    echo "║     • 完整的监控和日志系统                                   ║"
    echo "║                                                              ║"
    echo "║  📋 系统要求：                                               ║"
    echo "║     • Ubuntu 20.04+ / CentOS 7+ / Debian 10+                ║"
    echo "║     • 2核心CPU + 4GB内存 (推荐8GB)                          ║"
    echo "║     • 20GB磁盘空间                                           ║"
    echo "║                                                              ║"
    echo "║  ⏱️  预计部署时间：5-10分钟                                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查系统要求
check_system_requirements() {
    log_step "检查系统要求..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "不支持的操作系统"
        exit 1
    fi
    
    . /etc/os-release
    log_info "操作系统: $NAME $VERSION"
    
    # 检查内存
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    log_info "系统内存: ${MEMORY}MB"
    if [[ $MEMORY -lt 2048 ]]; then
        log_warning "内存少于2GB，可能影响性能，建议使用Docker判题引擎"
        RECOMMENDED_JUDGE_METHOD="docker"
    elif [[ $MEMORY -lt 4096 ]]; then
        log_warning "内存少于4GB，推荐使用Docker判题引擎"
        RECOMMENDED_JUDGE_METHOD="docker"
    else
        log_info "内存充足，可以使用Judger0判题引擎"
        RECOMMENDED_JUDGE_METHOD="judge0"
    fi
    
    # 检查磁盘空间
    DISK_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    log_info "可用磁盘空间: ${DISK_SPACE}GB"
    if [[ $DISK_SPACE -lt 10 ]]; then
        log_warning "磁盘空间少于10GB，可能不够用"
    fi
    
    # 检查是否为root用户
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户部署"
    fi
    
    log_success "系统要求检查完成"
}

# 安装依赖
install_dependencies() {
    log_step "安装系统依赖..."
    
    # 更新包管理器
    log_cmd "sudo apt update"
    sudo apt update -qq
    
    # 安装基础工具
    log_cmd "安装基础工具..."
    sudo apt install -y curl wget git vim htop ufw net-tools openssl > /dev/null 2>&1
    
    log_success "系统依赖安装完成"
}

# 安装Docker
install_docker() {
    log_step "安装Docker..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker已安装: $(docker --version)"
        return 0
    fi
    
    log_cmd "curl -fsSL https://get.docker.com | sh"
    curl -fsSL https://get.docker.com | sh > /dev/null 2>&1
    
    # 添加用户到docker组
    log_cmd "sudo usermod -aG docker $USER"
    sudo usermod -aG docker $USER
    
    # 启动Docker服务
    log_cmd "sudo systemctl start docker"
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_step "安装Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose已安装: $(docker-compose --version)"
        return 0
    fi
    
    # 获取最新版本
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    log_info "安装Docker Compose版本: $COMPOSE_VERSION"
    
    log_cmd "下载Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose > /dev/null 2>&1
    
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose安装完成"
}

# 获取服务器信息
get_server_info() {
    log_step "获取服务器信息..."
    
    # 获取公网IP
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")
    
    # 获取内网IP
    PRIVATE_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
    
    # 获取主机名
    HOSTNAME=$(hostname)
    
    log_info "服务器信息:"
    log_info "  主机名: $HOSTNAME"
    log_info "  内网IP: $PRIVATE_IP"
    log_info "  公网IP: $PUBLIC_IP"
    
    # 设置默认域名
    if [[ "$PUBLIC_IP" != "unknown" ]]; then
        DEFAULT_DOMAIN="$PUBLIC_IP"
    else
        DEFAULT_DOMAIN="$PRIVATE_IP"
    fi
}

# 交互式配置
interactive_config() {
    log_step "配置部署参数..."
    
    echo
    echo -e "${YELLOW}请根据您的需求配置以下参数（直接回车使用默认值）：${NC}"
    echo
    
    # 域名配置
    echo -e "${CYAN}1. 域名配置${NC}"
    read -p "请输入域名或IP地址 [默认: $DEFAULT_DOMAIN]: " DOMAIN_INPUT
    DOMAIN_NAME=${DOMAIN_INPUT:-$DEFAULT_DOMAIN}
    
    # 判题引擎选择
    echo -e "\n${CYAN}2. 判题引擎选择${NC}"
    echo "  1) Traditional - 传统判题（速度快，安全性中等）"
    echo "  2) Docker     - 容器判题（平衡安全性和性能）"
    echo "  3) Judger0    - 专业判题（最高安全性，支持50+语言）"
    echo
    read -p "请选择判题引擎 [推荐: $RECOMMENDED_JUDGE_METHOD] (1/2/3): " JUDGE_CHOICE
    
    case $JUDGE_CHOICE in
        1) JUDGE_METHOD="traditional" ;;
        2) JUDGE_METHOD="docker" ;;
        3) JUDGE_METHOD="judge0" ;;
        *) JUDGE_METHOD="$RECOMMENDED_JUDGE_METHOD" ;;
    esac
    
    # 管理员配置
    echo -e "\n${CYAN}3. 管理员账户配置${NC}"
    read -p "管理员用户名 [默认: admin]: " ADMIN_USERNAME
    ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
    
    read -s -p "管理员密码 [默认: admin123]: " ADMIN_PASSWORD
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
    echo
    
    read -p "管理员邮箱 [默认: admin@${DOMAIN_NAME}]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@${DOMAIN_NAME}}
    
    # 生成随机密码
    DB_PASSWORD="oj_db_$(openssl rand -hex 16)"
    REDIS_PASSWORD="oj_redis_$(openssl rand -hex 16)"
    SECRET_KEY="django-secret-$(openssl rand -hex 32)"
    
    echo
    log_info "配置完成！"
    log_info "  域名: $DOMAIN_NAME"
    log_info "  判题引擎: $JUDGE_METHOD"
    log_info "  管理员: $ADMIN_USERNAME"
    echo
}

# 创建环境配置
create_env_config() {
    log_step "创建环境配置文件..."
    
    cat > .env.prod << EOF
# OJ系统生产环境配置
# 自动生成时间: $(date)

# ===================
# 基础配置
# ===================
DEBUG=0
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN_NAME,localhost,127.0.0.1,$PRIVATE_IP
CORS_ALLOWED_ORIGINS=http://$DOMAIN_NAME,https://$DOMAIN_NAME

# ===================
# 数据库配置
# ===================
POSTGRES_DB=oj_database
POSTGRES_USER=oj_user
POSTGRES_PASSWORD=$DB_PASSWORD

# ===================
# Redis配置
# ===================
REDIS_PASSWORD=$REDIS_PASSWORD

# ===================
# 判题系统配置
# ===================
JUDGE_METHOD=$JUDGE_METHOD
DOCKER_JUDGE_ENABLED=True
DOCKER_PYTHON_IMAGE=oj-python-judge
DOCKER_CPP_IMAGE=oj-cpp-judge

# Judger0配置
JUDGE_SERVER_URL=http://judge0-server:2358
JUDGE_TOKEN=

# ===================
# 域名和SSL配置
# ===================
DOMAIN_NAME=$DOMAIN_NAME
SSL_EMAIL=$ADMIN_EMAIL

# ===================
# 邮件配置 (可选)
# ===================
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=$ADMIN_EMAIL

# ===================
# 日志配置
# ===================
LOG_LEVEL=INFO
LOG_FILE=/app/logs/django.log
EOF
    
    log_success "环境配置文件创建完成"
}

# 生成SSL证书
generate_ssl_certificate() {
    log_step "生成SSL证书..."
    
    mkdir -p ssl
    
    # 检查是否为有效域名（不是IP地址）
    if [[ $DOMAIN_NAME =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_info "检测到IP地址，生成自签名证书..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem \
            -out ssl/cert.pem \
            -subj "/C=CN/ST=State/L=City/O=OJ-System/CN=$DOMAIN_NAME" > /dev/null 2>&1
        
        log_success "自签名SSL证书生成完成"
    else
        log_info "检测到域名，尝试生成Let's Encrypt证书..."
        
        # 检查域名是否解析到当前服务器
        RESOLVED_IP=$(nslookup $DOMAIN_NAME 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}' || echo "")
        
        if [[ "$RESOLVED_IP" == "$PUBLIC_IP" ]] || [[ "$RESOLVED_IP" == "$PRIVATE_IP" ]]; then
            log_info "域名解析正确，安装certbot..."
            
            sudo apt install -y certbot > /dev/null 2>&1
            
            log_cmd "sudo certbot certonly --standalone -d $DOMAIN_NAME"
            if sudo certbot certonly --standalone -d $DOMAIN_NAME --email $ADMIN_EMAIL --agree-tos --non-interactive > /dev/null 2>&1; then
                sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem ssl/cert.pem
                sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem ssl/key.pem
                sudo chown $USER:$USER ssl/cert.pem ssl/key.pem
                log_success "Let's Encrypt证书生成完成"
            else
                log_warning "Let's Encrypt证书生成失败，使用自签名证书"
                openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                    -keyout ssl/key.pem \
                    -out ssl/cert.pem \
                    -subj "/C=CN/ST=State/L=City/O=OJ-System/CN=$DOMAIN_NAME" > /dev/null 2>&1
            fi
        else
            log_warning "域名未正确解析到当前服务器，使用自签名证书"
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/key.pem \
                -out ssl/cert.pem \
                -subj "/C=CN/ST=State/L=City/O=OJ-System/CN=$DOMAIN_NAME" > /dev/null 2>&1
            log_success "自签名SSL证书生成完成"
        fi
    fi
}

# 配置防火墙
configure_firewall() {
    log_step "配置防火墙..."
    
    # 启用防火墙
    log_cmd "sudo ufw --force enable"
    sudo ufw --force enable > /dev/null 2>&1
    
    # 允许必要端口
    sudo ufw allow ssh > /dev/null 2>&1
    sudo ufw allow 80/tcp > /dev/null 2>&1
    sudo ufw allow 443/tcp > /dev/null 2>&1
    sudo ufw allow 5555/tcp > /dev/null 2>&1  # Flower监控
    
    log_success "防火墙配置完成"
}

# 构建Docker镜像
build_docker_images() {
    if [[ "$JUDGE_METHOD" == "docker" ]]; then
        log_step "构建Docker判题镜像..."
        
        log_cmd "构建Python判题镜像..."
        docker build -f judge_images/Dockerfile.python -t oj-python-judge . > /dev/null 2>&1
        
        log_cmd "构建C++判题镜像..."
        docker build -f judge_images/Dockerfile.cpp -t oj-cpp-judge . > /dev/null 2>&1
        
        log_success "Docker判题镜像构建完成"
    fi
}

# 启动服务
start_services() {
    log_step "启动所有服务..."
    
    log_cmd "docker-compose -f docker-compose.prod.yml up -d --build"
    docker-compose -f docker-compose.prod.yml up -d --build
    
    log_info "等待服务启动..."
    sleep 10
    
    # 显示服务状态
    log_info "服务状态:"
    docker-compose -f docker-compose.prod.yml ps
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_step "等待服务完全就绪..."
    
    local max_wait=300  # 5分钟
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if curl -f http://localhost/health/ > /dev/null 2>&1; then
            log_success "Web服务已就绪"
            break
        fi
        
        echo -n "."
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_warning "服务启动超时，但继续部署..."
    fi
    
    # 如果启用了Judger0，等待其就绪
    if [[ "$JUDGE_METHOD" == "judge0" ]]; then
        log_info "等待Judger0服务就绪（可能需要5-10分钟）..."
        
        local judge0_wait=0
        local judge0_max_wait=600  # 10分钟
        
        while [ $judge0_wait -lt $judge0_max_wait ]; do
            if curl -f http://localhost:2358/system_info > /dev/null 2>&1; then
                log_success "Judger0服务已就绪"
                break
            fi
            
            echo -n "."
            sleep 10
            judge0_wait=$((judge0_wait + 10))
        done
        
        if [ $judge0_wait -ge $judge0_max_wait ]; then
            log_warning "Judger0启动超时，您可以稍后检查状态"
        fi
    fi
}

# 初始化数据库
initialize_database() {
    log_step "初始化数据库..."
    
    # 运行迁移
    log_cmd "python manage.py migrate"
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
    
    # 创建超级用户
    log_cmd "创建超级用户..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print('超级用户创建成功')
else:
    print('超级用户已存在')
"
    
    # 收集静态文件
    log_cmd "python manage.py collectstatic --noinput"
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput > /dev/null 2>&1
    
    log_success "数据库初始化完成"
}

# 健康检查
health_check() {
    log_step "执行系统健康检查..."
    
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
    
    # 检查Celery
    if docker-compose -f docker-compose.prod.yml exec -T celery celery -A oj_project inspect ping > /dev/null 2>&1; then
        log_success "✓ Celery正常"
    else
        log_warning "⚠ Celery状态异常，但可能正在启动中"
    fi
    
    # 检查Judger0（如果启用）
    if [[ "$JUDGE_METHOD" == "judge0" ]]; then
        if curl -f http://localhost:2358/system_info > /dev/null 2>&1; then
            log_success "✓ Judger0正常"
        else
            log_warning "⚠ Judger0未就绪，可能仍在初始化中"
        fi
    fi
    
    if [[ $failed -eq 0 ]]; then
        log_success "系统健康检查通过"
        return 0
    else
        log_warning "部分服务异常，请检查日志"
        return 1
    fi
}

# 显示部署结果
show_deployment_result() {
    clear
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 部署完成！                             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${CYAN}📋 系统信息:${NC}"
    echo "  服务器: $HOSTNAME ($PRIVATE_IP)"
    echo "  域名: $DOMAIN_NAME"
    echo "  判题引擎: $JUDGE_METHOD"
    echo "  管理员: $ADMIN_USERNAME"
    echo
    
    echo -e "${CYAN}🌐 访问地址:${NC}"
    if [[ $DOMAIN_NAME =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "  网站首页: http://$DOMAIN_NAME"
        echo "  管理后台: http://$DOMAIN_NAME/admin/"
        echo "  系统监控: http://$DOMAIN_NAME:5555/"
        if [[ "$JUDGE_METHOD" == "judge0" ]]; then
            echo "  Judger0状态: http://$DOMAIN_NAME:2358/system_info"
        fi
    else
        echo "  网站首页: https://$DOMAIN_NAME"
        echo "  管理后台: https://$DOMAIN_NAME/admin/"
        echo "  系统监控: https://$DOMAIN_NAME:5555/"
        if [[ "$JUDGE_METHOD" == "judge0" ]]; then
            echo "  Judger0状态: https://$DOMAIN_NAME:2358/system_info"
        fi
    fi
    echo
    
    echo -e "${CYAN}👨‍💼 管理员账户:${NC}"
    echo "  用户名: $ADMIN_USERNAME"
    echo "  密码: $ADMIN_PASSWORD"
    echo "  邮箱: $ADMIN_EMAIL"
    echo
    
    echo -e "${CYAN}🔧 服务管理命令:${NC}"
    echo "  查看状态: ./scripts/manage.sh status"
    echo "  查看日志: ./scripts/manage.sh logs"
    echo "  重启服务: ./scripts/manage.sh restart"
    echo "  健康检查: ./scripts/manage.sh health"
    echo "  数据备份: ./scripts/backup.sh"
    echo
    
    echo -e "${CYAN}📚 帮助文档:${NC}"
    echo "  部署指南: docs/LINUX_DEPLOYMENT_GUIDE.md"
    echo "  判题架构: docs/JUDGE_SYSTEM_ARCHITECTURE.md"
    echo "  项目仓库: https://github.com/blackjackandLisa/oj_project"
    echo
    
    if [[ "$JUDGE_METHOD" == "judge0" ]]; then
        echo -e "${YELLOW}⚠️  注意事项:${NC}"
        echo "  • Judger0首次启动可能需要5-10分钟完全就绪"
        echo "  • 如果Judger0未就绪，可以稍后访问判题功能"
        echo "  • 可以运行 'docker-compose -f docker-compose.prod.yml logs judge0-server -f' 查看启动进度"
        echo
    fi
    
    echo -e "${GREEN}🎯 部署成功！现在您可以开始使用OJ系统了！${NC}"
}

# 主函数
main() {
    # 检查是否在项目目录中
    if [[ ! -f "docker-compose.prod.yml" ]]; then
        log_error "请在OJ项目根目录中运行此脚本"
        exit 1
    fi
    
    show_welcome
    
    echo -e "${YELLOW}按回车键开始部署，或按Ctrl+C取消...${NC}"
    read -p ""
    
    check_system_requirements
    install_dependencies
    install_docker
    install_docker_compose
    get_server_info
    interactive_config
    create_env_config
    generate_ssl_certificate
    configure_firewall
    build_docker_images
    start_services
    wait_for_services
    initialize_database
    
    if health_check; then
        show_deployment_result
    else
        log_warning "部署完成但部分服务可能未完全就绪，请稍后检查"
        show_deployment_result
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

#!/bin/bash

# OJ系统自动部署脚本
# 适用于Linux服务器部署

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "建议不要使用root用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "不支持的操作系统"
        exit 1
    fi
    
    . /etc/os-release
    log_info "操作系统: $NAME $VERSION"
    
    # 检查内存
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [[ $MEMORY -lt 2048 ]]; then
        log_warning "系统内存少于2GB，可能影响性能"
    fi
    
    # 检查磁盘空间
    DISK_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $DISK_SPACE -lt 10 ]]; then
        log_warning "磁盘空间少于10GB，可能不够用"
    fi
    
    log_success "系统检查完成"
}

# 安装Docker
install_docker() {
    log_info "检查Docker安装..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker已安装: $(docker --version)"
    else
        log_info "安装Docker..."
        
        # 更新包索引
        sudo apt-get update
        
        # 安装依赖
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release
        
        # 添加Docker官方GPG密钥
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # 添加Docker仓库
        echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
            $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # 安装Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
        
        # 启动Docker服务
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # 添加当前用户到docker组
        sudo usermod -aG docker $USER
        
        log_success "Docker安装完成"
        log_warning "请重新登录以使docker组权限生效"
    fi
}

# 安装Docker Compose
install_docker_compose() {
    log_info "检查Docker Compose安装..."
    
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose已安装: $(docker-compose --version)"
    else
        log_info "安装Docker Compose..."
        
        # 获取最新版本
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
        
        # 下载并安装
        sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        
        # 添加执行权限
        sudo chmod +x /usr/local/bin/docker-compose
        
        # 创建软链接
        sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        
        log_success "Docker Compose安装完成"
    fi
}

# 安装其他依赖
install_dependencies() {
    log_info "安装其他依赖..."
    
    sudo apt-get update
    sudo apt-get install -y \
        git \
        curl \
        wget \
        unzip \
        htop \
        vim \
        ufw \
        fail2ban
    
    log_success "依赖安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 启用UFW
    sudo ufw --force enable
    
    # 允许SSH
    sudo ufw allow ssh
    
    # 允许HTTP和HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # 允许Flower监控 (可选)
    sudo ufw allow 5555/tcp
    
    log_success "防火墙配置完成"
}

# 配置fail2ban
configure_fail2ban() {
    log_info "配置fail2ban..."
    
    # 创建fail2ban配置
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

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF
    
    # 重启fail2ban
    sudo systemctl restart fail2ban
    sudo systemctl enable fail2ban
    
    log_success "fail2ban配置完成"
}

# 创建部署目录
create_deploy_directory() {
    log_info "创建部署目录..."
    
    DEPLOY_DIR="/opt/oj-system"
    
    if [[ ! -d "$DEPLOY_DIR" ]]; then
        sudo mkdir -p "$DEPLOY_DIR"
        sudo chown $USER:$USER "$DEPLOY_DIR"
    fi
    
    cd "$DEPLOY_DIR"
    log_success "部署目录: $DEPLOY_DIR"
}

# 克隆代码
clone_code() {
    log_info "克隆代码..."
    
    if [[ -d "oj_project" ]]; then
        log_warning "代码目录已存在，是否更新? (y/N)"
        read -p "" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd oj_project
            git pull origin main
            cd ..
        fi
    else
        # 这里需要替换为实际的Git仓库地址
        log_warning "请手动克隆代码到 $DEPLOY_DIR/oj_project"
        log_info "示例: git clone https://github.com/your-username/oj_project.git"
        read -p "按回车键继续..."
    fi
    
    log_success "代码准备完成"
}

# 配置环境变量
configure_environment() {
    log_info "配置环境变量..."
    
    cd oj_project
    
    if [[ ! -f ".env.prod" ]]; then
        if [[ -f "env.prod.template" ]]; then
            cp env.prod.template .env.prod
            log_warning "请编辑 .env.prod 文件配置环境变量"
            log_info "重要配置项:"
            log_info "  - SECRET_KEY: Django密钥"
            log_info "  - POSTGRES_PASSWORD: 数据库密码"
            log_info "  - REDIS_PASSWORD: Redis密码"
            log_info "  - ALLOWED_HOSTS: 允许的主机"
            log_info "  - DOMAIN_NAME: 域名"
            
            read -p "配置完成后按回车键继续..."
        else
            log_error "找不到环境变量模板文件"
            exit 1
        fi
    fi
    
    log_success "环境变量配置完成"
}

# 生成SSL证书
generate_ssl_certificate() {
    log_info "生成SSL证书..."
    
    # 检查是否有域名配置
    if [[ -f ".env.prod" ]]; then
        DOMAIN_NAME=$(grep "DOMAIN_NAME=" .env.prod | cut -d'=' -f2)
        if [[ -n "$DOMAIN_NAME" && "$DOMAIN_NAME" != "your-domain.com" ]]; then
            log_info "检测到域名: $DOMAIN_NAME"
            
            # 安装certbot
            sudo apt-get install -y certbot
            
            # 生成证书
            sudo certbot certonly --standalone -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "$(grep "SSL_EMAIL=" .env.prod | cut -d'=' -f2)"
            
            # 复制证书到项目目录
            sudo cp "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ssl/cert.pem
            sudo cp "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" ssl/key.pem
            sudo chown $USER:$USER ssl/cert.pem ssl/key.pem
            
            log_success "SSL证书生成完成"
        else
            log_warning "未配置域名，使用自签名证书"
            generate_self_signed_cert
        fi
    else
        log_warning "未找到环境配置文件，使用自签名证书"
        generate_self_signed_cert
    fi
}

# 生成自签名证书
generate_self_signed_cert() {
    log_info "生成自签名证书..."
    
    mkdir -p ssl
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
    
    log_success "自签名证书生成完成"
}

# 构建和启动服务
build_and_start() {
    log_info "构建和启动服务..."
    
    # 停止现有服务
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # 构建镜像
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # 启动服务
    docker-compose -f docker-compose.prod.yml up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    docker-compose -f docker-compose.prod.yml ps
    
    log_success "服务启动完成"
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
    
    # 创建超级用户
    log_info "创建超级用户..."
    docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser --noinput --username admin --email admin@example.com || true
    
    log_success "数据库迁移完成"
}

# 收集静态文件
collect_static() {
    log_info "收集静态文件..."
    
    docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
    
    log_success "静态文件收集完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查Web服务
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        log_success "Web服务健康检查通过"
    else
        log_error "Web服务健康检查失败"
        return 1
    fi
    
    # 检查数据库
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U oj_user -d oj_database > /dev/null 2>&1; then
        log_success "数据库健康检查通过"
    else
        log_error "数据库健康检查失败"
        return 1
    fi
    
    # 检查Redis
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis健康检查通过"
    else
        log_error "Redis健康检查失败"
        return 1
    fi
    
    log_success "所有服务健康检查通过"
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo
    log_info "访问信息:"
    log_info "  网站地址: http://localhost (或您的域名)"
    log_info "  管理后台: http://localhost/admin/"
    log_info "  Flower监控: http://localhost:5555/"
    echo
    log_info "服务管理:"
    log_info "  查看状态: docker-compose -f docker-compose.prod.yml ps"
    log_info "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
    log_info "  重启服务: docker-compose -f docker-compose.prod.yml restart"
    log_info "  停止服务: docker-compose -f docker-compose.prod.yml down"
    echo
    log_info "重要文件:"
    log_info "  环境配置: $DEPLOY_DIR/oj_project/.env.prod"
    log_info "  Nginx配置: $DEPLOY_DIR/oj_project/nginx/"
    log_info "  日志目录: $DEPLOY_DIR/oj_project/logs/"
    echo
    log_warning "请记住修改默认密码和配置！"
}

# 主函数
main() {
    log_info "开始部署OJ系统..."
    
    check_root
    check_system
    install_docker
    install_docker_compose
    install_dependencies
    configure_firewall
    configure_fail2ban
    create_deploy_directory
    clone_code
    configure_environment
    generate_ssl_certificate
    build_and_start
    run_migrations
    collect_static
    health_check
    show_deployment_info
    
    log_success "部署完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

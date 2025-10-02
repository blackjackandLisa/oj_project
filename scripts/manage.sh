#!/bin/bash

# OJ系统服务管理脚本

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

# 检查是否在项目目录
check_project_dir() {
    if [[ ! -f "docker-compose.prod.yml" ]]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "OJ系统服务管理脚本"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    查看服务状态"
    echo "  logs      查看服务日志"
    echo "  shell     进入Web容器shell"
    echo "  db-shell  进入数据库shell"
    echo "  backup    备份数据库"
    echo "  restore   恢复数据库"
    echo "  update    更新代码并重启"
    echo "  health    健康检查"
    echo "  clean     清理无用资源"
    echo "  help      显示此帮助信息"
    echo
}

# 启动服务
start_services() {
    log_info "启动服务..."
    docker-compose -f docker-compose.prod.yml up -d
    log_success "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose -f docker-compose.prod.yml down
    log_success "服务停止完成"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    docker-compose -f docker-compose.prod.yml restart
    log_success "服务重启完成"
}

# 查看服务状态
show_status() {
    log_info "服务状态:"
    docker-compose -f docker-compose.prod.yml ps
    echo
    log_info "资源使用情况:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 查看日志
show_logs() {
    local service=${1:-""}
    if [[ -n "$service" ]]; then
        log_info "查看 $service 服务日志:"
        docker-compose -f docker-compose.prod.yml logs -f "$service"
    else
        log_info "查看所有服务日志:"
        docker-compose -f docker-compose.prod.yml logs -f
    fi
}

# 进入Web容器shell
enter_web_shell() {
    log_info "进入Web容器shell..."
    docker-compose -f docker-compose.prod.yml exec web bash
}

# 进入数据库shell
enter_db_shell() {
    log_info "进入数据库shell..."
    docker-compose -f docker-compose.prod.yml exec db psql -U oj_user -d oj_database
}

# 备份数据库
backup_database() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "备份数据库到 $backup_file..."
    
    mkdir -p backups
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U oj_user -d oj_database > "backups/$backup_file"
    
    log_success "数据库备份完成: backups/$backup_file"
}

# 恢复数据库
restore_database() {
    local backup_file=$1
    if [[ -z "$backup_file" ]]; then
        log_error "请指定备份文件"
        echo "可用备份文件:"
        ls -la backups/*.sql 2>/dev/null || echo "无备份文件"
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_warning "这将覆盖当前数据库，是否继续? (y/N)"
    read -p "" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消恢复"
        exit 0
    fi
    
    log_info "恢复数据库从 $backup_file..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U oj_user -d oj_database < "$backup_file"
    
    log_success "数据库恢复完成"
}

# 更新代码并重启
update_system() {
    log_info "更新系统..."
    
    # 备份数据库
    backup_database
    
    # 拉取最新代码
    if [[ -d ".git" ]]; then
        log_info "拉取最新代码..."
        git pull origin main
    else
        log_warning "不是Git仓库，跳过代码更新"
    fi
    
    # 重新构建镜像
    log_info "重新构建镜像..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # 重启服务
    restart_services
    
    # 运行迁移
    log_info "运行数据库迁移..."
    docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
    
    # 收集静态文件
    log_info "收集静态文件..."
    docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
    
    log_success "系统更新完成"
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
    
    # 检查Celery
    if docker-compose -f docker-compose.prod.yml exec -T celery celery -A oj_project inspect ping > /dev/null 2>&1; then
        log_success "✓ Celery正常"
    else
        log_error "✗ Celery异常"
        failed=1
    fi
    
    if [[ $failed -eq 0 ]]; then
        log_success "所有服务健康检查通过"
    else
        log_error "部分服务健康检查失败"
        exit 1
    fi
}

# 清理无用资源
clean_resources() {
    log_info "清理无用资源..."
    
    # 清理停止的容器
    docker container prune -f
    
    # 清理无用的镜像
    docker image prune -f
    
    # 清理无用的网络
    docker network prune -f
    
    # 清理无用的卷
    docker volume prune -f
    
    # 清理构建缓存
    docker builder prune -f
    
    log_success "资源清理完成"
}

# 主函数
main() {
    check_project_dir
    
    case "${1:-help}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        shell)
            enter_web_shell
            ;;
        db-shell)
            enter_db_shell
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$2"
            ;;
        update)
            update_system
            ;;
        health)
            health_check
            ;;
        clean)
            clean_resources
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

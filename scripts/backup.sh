#!/bin/bash

# OJ系统备份脚本

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

# 配置
BACKUP_DIR="/opt/oj-backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        sudo mkdir -p "$BACKUP_DIR"
        sudo chown $USER:$USER "$BACKUP_DIR"
    fi
}

# 备份数据库
backup_database() {
    local backup_file="$BACKUP_DIR/database_$DATE.sql"
    log_info "备份数据库到 $backup_file..."
    
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U oj_user -d oj_database > "$backup_file"
    
    # 压缩备份文件
    gzip "$backup_file"
    log_success "数据库备份完成: ${backup_file}.gz"
}

# 备份媒体文件
backup_media() {
    local backup_file="$BACKUP_DIR/media_$DATE.tar.gz"
    log_info "备份媒体文件到 $backup_file..."
    
    if [[ -d "media" ]]; then
        tar -czf "$backup_file" media/
        log_success "媒体文件备份完成: $backup_file"
    else
        log_warning "媒体目录不存在，跳过媒体文件备份"
    fi
}

# 备份配置文件
backup_config() {
    local backup_file="$BACKUP_DIR/config_$DATE.tar.gz"
    log_info "备份配置文件到 $backup_file..."
    
    tar -czf "$backup_file" \
        .env.prod \
        nginx/ \
        postgres/ \
        ssl/ \
        docker-compose.prod.yml \
        Dockerfile.prod 2>/dev/null || true
    
    log_success "配置文件备份完成: $backup_file"
}

# 备份代码
backup_code() {
    local backup_file="$BACKUP_DIR/code_$DATE.tar.gz"
    log_info "备份代码到 $backup_file..."
    
    # 排除不需要的文件
    tar -czf "$backup_file" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env*' \
        --exclude='logs' \
        --exclude='media' \
        --exclude='staticfiles' \
        --exclude='node_modules' \
        --exclude='.DS_Store' \
        .
    
    log_success "代码备份完成: $backup_file"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理 $RETENTION_DAYS 天前的备份文件..."
    
    find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    log_success "旧备份清理完成"
}

# 上传到云存储 (可选)
upload_to_cloud() {
    if command -v aws &> /dev/null && [[ -n "$AWS_S3_BUCKET" ]]; then
        log_info "上传备份到S3..."
        
        aws s3 sync "$BACKUP_DIR" "s3://$AWS_S3_BUCKET/oj-backups/" \
            --delete \
            --storage-class STANDARD_IA
        
        log_success "备份上传到S3完成"
    else
        log_warning "未配置AWS S3，跳过云存储上传"
    fi
}

# 显示备份信息
show_backup_info() {
    log_info "备份完成！"
    echo
    log_info "备份文件:"
    ls -lh "$BACKUP_DIR"/*_$DATE.* 2>/dev/null || echo "无备份文件"
    echo
    log_info "备份目录: $BACKUP_DIR"
    log_info "保留天数: $RETENTION_DAYS 天"
    echo
    log_info "恢复命令示例:"
    log_info "  数据库: gunzip -c $BACKUP_DIR/database_$DATE.sql.gz | docker-compose -f docker-compose.prod.yml exec -T db psql -U oj_user -d oj_database"
    log_info "  媒体文件: tar -xzf $BACKUP_DIR/media_$DATE.tar.gz"
    log_info "  配置文件: tar -xzf $BACKUP_DIR/config_$DATE.tar.gz"
}

# 主函数
main() {
    log_info "开始备份OJ系统..."
    
    create_backup_dir
    backup_database
    backup_media
    backup_config
    backup_code
    cleanup_old_backups
    upload_to_cloud
    show_backup_info
    
    log_success "备份完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

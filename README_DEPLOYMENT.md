# OJ系统Linux部署指南

## 🚀 快速开始

### 一键部署 (推荐)

```bash
# 下载并运行快速部署脚本
wget https://raw.githubusercontent.com/your-repo/oj_project/main/scripts/quick-deploy.sh
chmod +x quick-deploy.sh
./quick-deploy.sh
```

### 完整部署

```bash
# 下载并运行完整部署脚本
wget https://raw.githubusercontent.com/your-repo/oj_project/main/scripts/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

## 📋 部署前准备

### 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **CPU**: 2核心以上
- **内存**: 4GB以上 (推荐8GB)
- **磁盘**: 20GB以上可用空间
- **网络**: 公网IP (可选，用于域名访问)

### 必要软件
- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl/wget

## 🎯 部署方式选择

### 1. 快速部署 (测试/演示)
- ✅ 自动安装Docker
- ✅ 自动配置环境
- ✅ 使用自签名证书
- ✅ 默认密码: admin/admin123
- ⚠️ 仅适用于测试环境

### 2. 完整部署 (生产环境)
- ✅ 完整的安全配置
- ✅ SSL证书自动申请
- ✅ 防火墙配置
- ✅ 监控和备份
- ✅ 性能优化
- ✅ 生产级配置

## 📁 部署文件说明

```
oj_project/
├── docker-compose.prod.yml    # 生产环境Docker配置
├── Dockerfile.prod            # 生产环境Dockerfile
├── env.prod.template          # 环境变量模板
├── nginx/                     # Nginx配置
│   ├── nginx.conf
│   └── conf.d/oj.conf
├── postgres/                  # 数据库配置
│   └── init.sql
├── ssl/                       # SSL证书目录
├── scripts/                   # 部署脚本
│   ├── deploy.sh             # 完整部署脚本
│   ├── quick-deploy.sh       # 快速部署脚本
│   ├── manage.sh             # 服务管理脚本
│   └── backup.sh             # 备份脚本
└── docs/                      # 文档
    └── LINUX_DEPLOYMENT_GUIDE.md
```

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

# 备份数据
./scripts/manage.sh backup

# 更新系统
./scripts/manage.sh update

# 清理资源
./scripts/manage.sh clean
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

## 🌐 访问地址

部署完成后，您可以访问：

- **网站**: http://your-domain.com (或 http://localhost)
- **管理后台**: http://your-domain.com/admin/
- **Flower监控**: http://your-domain.com:5555/
- **API文档**: http://your-domain.com/api/docs/

## 🔒 安全配置

### 默认配置
- 防火墙已配置 (UFW)
- Fail2ban已安装
- SSL/TLS已启用
- 安全头已配置

### 重要提醒
1. **修改默认密码**: 部署后立即修改admin密码
2. **配置域名**: 修改ALLOWED_HOSTS和域名配置
3. **定期备份**: 设置自动备份任务
4. **监控日志**: 定期检查系统日志

## 📊 监控和维护

### 健康检查
```bash
# 检查所有服务
./scripts/manage.sh health

# 检查Web服务
curl -f http://localhost/health/

# 检查数据库
docker-compose -f docker-compose.prod.yml exec db pg_isready -U oj_user -d oj_database
```

### 数据备份
```bash
# 自动备份
./scripts/backup.sh

# 设置定时备份
crontab -e
# 添加: 0 2 * * * /opt/oj-system/oj_project/scripts/backup.sh
```

### 日志查看
```bash
# 查看应用日志
./scripts/manage.sh logs

# 查看特定服务日志
./scripts/manage.sh logs web
./scripts/manage.sh logs celery
./scripts/manage.sh logs nginx
```

## 🚨 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 查看详细日志
   docker-compose -f docker-compose.prod.yml logs
   
   # 检查端口占用
   netstat -tlnp | grep :80
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker-compose -f docker-compose.prod.yml exec db pg_isready -U oj_user -d oj_database
   
   # 重启数据库
   docker-compose -f docker-compose.prod.yml restart db
   ```

3. **静态文件404**
   ```bash
   # 重新收集静态文件
   docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   ```

4. **判题系统异常**
   ```bash
   # 检查Celery状态
   docker-compose -f docker-compose.prod.yml exec celery celery -A oj_project inspect ping
   
   # 重启Celery
   docker-compose -f docker-compose.prod.yml restart celery
   ```

## 📈 性能优化

### 系统优化
- 数据库连接池已配置
- Nginx缓存已启用
- Gzip压缩已启用
- 静态文件CDN就绪

### 扩展配置
- 支持负载均衡
- 支持数据库集群
- 支持Redis集群
- 支持容器编排

## 📞 技术支持

### 获取帮助
1. 查看详细文档: `docs/LINUX_DEPLOYMENT_GUIDE.md`
2. 查看服务状态: `./scripts/manage.sh status`
3. 查看系统日志: `./scripts/manage.sh logs`
4. 执行健康检查: `./scripts/manage.sh health`

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

## 🎉 部署完成

恭喜！您的OJ系统已成功部署。

### 下一步
1. 修改默认密码
2. 配置域名和SSL
3. 设置定时备份
4. 配置监控告警
5. 优化性能参数

---

**部署脚本版本**: 1.0.0  
**最后更新**: 2025-10-02  
**状态**: ✅ 生产就绪

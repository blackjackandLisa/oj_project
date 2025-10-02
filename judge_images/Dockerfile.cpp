# C++判题镜像
# 包含GCC编译器的精简环境

FROM alpine:3.19

# 安装GCC和必要的工具
RUN apk add --no-cache \
    g++ \
    libstdc++ \
    && rm -rf /var/cache/apk/*

# 设置工作目录
WORKDIR /judge

# 创建非特权用户
RUN adduser -D -u 1001 judger && \
    chown -R judger:judger /judge

# 切换到非特权用户
USER judger

# 健康检查
HEALTHCHECK NONE

# 默认命令（会被覆盖）
CMD ["/bin/sh"]


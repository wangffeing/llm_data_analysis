#!/bin/bash

# 定时重启脚本
APP_DIR="/home/ps/myproject/2025/api"
LOG_DIR="$APP_DIR/logs"
RESTART_LOG="$LOG_DIR/restart.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录重启时间
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始定时重启服务" >> "$RESTART_LOG"

# 切换到应用目录
cd "$APP_DIR"

# 执行重启
./api.sh restart >> "$RESTART_LOG" 2>&1

# 检查重启结果
if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务重启成功" >> "$RESTART_LOG"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务重启失败" >> "$RESTART_LOG"
fi

# 保持最近30天的重启日志
find "$LOG_DIR" -name "restart.log" -mtime +30 -delete 2>/dev/null || true

echo "$(date '+%Y-%m-%d %H:%M:%S') - 定时重启完成" >> "$RESTART_LOG"
echo "----------------------------------------" >> "$RESTART_LOG"
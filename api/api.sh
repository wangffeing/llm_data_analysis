#!/bin/bash

# 配置变量
APP_NAME="llm-data-analysis"
APP_DIR="/home/ps/myproject/2025/api"
CONDA_ENV="base"
PORT=15000
WORKERS=6
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/$APP_NAME.pid"
LOG_FILE="$LOG_DIR/$APP_NAME.log"

# 函数：检查服务状态
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "$APP_NAME is running (PID: $PID)"
            return 0
        else
            echo "$APP_NAME is not running (stale PID file)"
            rm "$PID_FILE"
            return 1
        fi
    else
        echo "$APP_NAME is not running"
        return 1
    fi
}

# 函数：启动服务
start_service() {
    if check_status > /dev/null 2>&1; then
        echo "$APP_NAME is already running!"
        exit 1
    fi
    
    echo "Starting $APP_NAME..."
    
    # 创建必要目录
    mkdir -p "$LOG_DIR"
    
    # 切换到应用目录
    cd "$APP_DIR"
    
    # 启动服务
    nohup /bin/bash -c "
        source /home/ps/anaconda3/bin/activate $CONDA_ENV;
        uvicorn main_sse:app --host 0.0.0.0 --port $PORT --workers $WORKERS
    " > "$LOG_FILE" 2>&1 &
    
    # 保存PID
    echo $! > "$PID_FILE"
    
    # 等待一下确保启动成功
    sleep 2
    
    if check_status > /dev/null 2>&1; then
        echo "$APP_NAME started successfully!"
        echo "PID: $(cat $PID_FILE)"
        echo "Port: $PORT"
        echo "Log: $LOG_FILE"
        echo "URL: http://localhost:$PORT"
    else
        echo "Failed to start $APP_NAME"
        exit 1
    fi
}

# 函数：停止服务
stop_service() {
    echo "Stopping $APP_NAME..."

    # 先尝试用 PID 文件
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null || true
        rm -f "$PID_FILE"
    fi

    # 强制杀死所有相关 python/uvicorn 进程
    pkill -f "uvicorn main_sse:app" || true
    pkill -f ":$PORT" || true

    sleep 2
    echo "$APP_NAME stopped."
}

# 主逻辑
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 5
        start_service
        ;;
    status)
        check_status
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac

# 使用 ARM64 架构的 Nginx
FROM arm64v8/nginx:alpine

# 设置工作目录
WORKDIR /usr/share/nginx/html

# 复制预编译的前端文件
COPY frontend-build.tar.gz .

# 解压并部署
RUN tar -xzf frontend-build.tar.gz --strip-components=1 && \
    rm frontend-build.tar.gz

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
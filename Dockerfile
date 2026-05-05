FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ .

# 复制前端文件
COPY frontend/ /app/static/

# 创建数据目录
RUN mkdir -p /data

# 环境变量
ENV STORAGE_ROOT=/data/物品存储
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

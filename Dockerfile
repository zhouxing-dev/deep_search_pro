# ============================================
# 阶段1: 构建阶段 - 安装依赖
# ============================================
FROM python:3.12.7-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

# ============================================
# 阶段2: 运行阶段 - 最小化镜像
# ============================================
FROM python:3.12.7-slim AS runtime

# 生产环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 时区 + 健康检查工具
RUN apt-get update && apt-get install -y --no-install-recommends tzdata wget && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /install /usr/local

# 复制应用代码（项目入口为根目录 main.py，复制全部业务目录）
COPY main.py ./
COPY agent/ ./agent/
COPY api/ ./api/
COPY clients/ ./clients/
COPY repositories/ ./repositories/
COPY utils/ ./utils/
COPY prompt/ ./prompt/
COPY static/ ./static/

# 修正文件所有权（关键！否则非root用户可能读不到）
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1

# 启动命令（生产级）
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--proxy-headers"]
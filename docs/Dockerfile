# 使用官方 Python 3.11 的 arm64 架构镜像（适用于 Apple Silicon）
FROM python:3.11-slim

# 安装依赖（建议提前准备好 requirements.txt）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.7.1
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple faiss-cpu==1.9.0 \
    sentence_transformers==5.0.0 \
    streamlit==1.46.1 \
    PyMuPDF==1.26.3 \
    python-pptx==1.0.2

# 设置工作目录
WORKDIR /app

# 复制所有文件（包括模型文件）到容器中
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动 Streamlit 应用
CMD ["streamlit", "run", "streamlit_app.py", "--server.headless=true"]
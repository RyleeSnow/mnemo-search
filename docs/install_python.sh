#!/usr/bin/env bash
set -e

# 🔧 可配置变量
PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
VENV_DIR="${HOME}/mnemo_venv"

# 1. 检查指定 Python 是否存在
if [ ! -x "${PYTHON_PATH}" ]; then
  echo "错误：未找到 Python 可执行文件 ' ${PYTHON_PATH} '"
  exit 1
fi

# 2. 验证 Python 版本
echo "Python 版本检查："
"${PYTHON_PATH}" --version

# 3. 创建虚拟环境
echo "创建虚拟环境：${VENV_DIR}"
"${PYTHON_PATH}" -m venv "${VENV_DIR}"

# 4. 激活环境
source "${VENV_DIR}/bin/activate"

# 5. 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 7. 安装指定包
pip install --no-cache-dir \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  torch==2.7.1

pip install --no-cache-dir \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  faiss-cpu==1.9.0 \
  sentence_transformers==5.0.0 \
  streamlit==1.46.1 \
  PyMuPDF==1.26.3 \
  python-pptx==1.0.2

deactivate
echo "✅ 安装完成! 请牢记以下路径: ${VENV_DIR}/bin/activate"
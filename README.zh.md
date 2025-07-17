# Mnemo - 智能文档搜索系统

> **Language**: [English](README.md) | [中文](README.zh.md)

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.46+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

一个基于AI的本地文档管理和搜索系统，支持文件的智能索引、摘要生成和语义搜索。

<br>

## ✨ 功能特性

- 🔒 **本地安全**: 文件识别、入库、搜索全在本地完成，文件信息安全可靠
- 🖥️ **友好界面**: 基于Streamlit的直观Web界面
- 📝 **自动摘要生成**: 利用大语言模型自动生成文档摘要和关键词
- 🎯 **快速匹配**: 使用FAISS向量数据库实现高效相似度搜索
- 🔄 **增量更新**: 智能识别已处理文件，避免重复索引
- 📊 **多格式支持**: 支持PDF和PPT文件解析

<br>

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Ollama (用于本地LLM)
- 目前程序仅在 Apple M4 芯片进行测试，如果使用其他系统或者芯片，可能需要相应的修改

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/RyleeSnow/mnemo-search.git
   cd mnemo-search
   ```

2. **安装依赖**
   ```bash
   pip install -e .
   ```

3. **启动并配置Ollama**

```bash
   ollama pull modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M
   ollama cp "modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M" Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M
   ollama rm "modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M"

   ollama pull "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"
   ollama cp "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M" Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M
   ollama rm "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"
```

- 在 `Terminal` 中输入命令行 `ollama list` 并回车，如果显示模型 `Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M` 和 `Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M`, 说明设置成功。

4. **启动应用**
   ```bash
   mnemo-v1
   ```

<br>

## 📖 使用指南

### 1. 初始化数据库

首次使用时需要初始化数据库：

1. 在侧边栏选择 `initialize`
2. 输入数据库存储路径
3. 点击 `initialize` 按钮

### 2. 文档入库

将文档添加到搜索索引：

1. 选择 `organize` 选项
2. 指定包含文档的文件夹路径
3. 选择文件类型（PDF/PPT）
4. 选择LLM模型质量（`Quality`/`Speed`）
5. 点击 `start` 开始处理

**注意事项：**
- 建议首次使用时选择少量文件进行测试
- 每次会默认入库文件夹中的所有符合要求的文件，如果已经入库过会跳过。同个文件名但是不同文件夹的文件，会被当成一个文件，只入库一次。
- 建议一次性不要入库过多文件，以免一次耗时过长。
  - 如果左侧 `Chooose LLM model` 菜单选择 `quality`，会启用 `Mistral-Small-3.2-24B-Instruct-2506:Q4_K_M` 模型，提供更高精度但处理时间较长
  - 如果左侧 `Chooose LLM model` 菜单选择 `speed`，会启用 `Nous-Hermes-2-Mistral-7B-DPO:Q4_K_M` 模型，处理速度更快但精度稍低
  - 经过测试，一般来说建议使用 `quality` 模型
- 目前阶段仅支持 `ppt` 和 `pdf` 文件（可勾选）。如果同个文件内容有 `ppt` 和 `pdf` 两个版本，建议使用 `ppt` 版本，能更准确捕捉文本内容，耗时也相对更短。
- 如果在运行过程中想临时终止，可点击左侧菜单的 `Stop` 按钮

### 3. 文档搜索

完成文档入库后，在左侧菜单栏选择 `search`，填入你想搜索的内容即可，系统会按照相关性从上至下显示文件名。

如果使用 Mac，则可点击文件名直接打开文件。

### 4. 结束使用
- 关闭网页
- 退出 ollama 客户端
- 在运行 `mnemo-v1` 的窗口 ，CTRL+C 终止进程

<br>

## 🏗️ 系统架构

```
src/mnemo/v1/
├── app.py              # Streamlit主应用
├── run.py              # 应用入口点
├── config/
│   └── config.json     # 配置文件
├── core/
│   ├── document_parser.py      # 文档解析
│   └── extract_and_summarize.py # 摘要生成
│   ├── embedding_and_save.py   # 向量嵌入和存储
│   ├── search_files.py         # 搜索功能
└── scripts/
    └── app_funcs.py    # 应用辅助函数
```

<br>

## 📁 数据存储

系统会在指定的数据库文件夹中创建以下文件：
- `faiss_index.bin`: FAISS向量索引
- `metadata_with_id.json`: 文档元数据
- `model_fingerprint.json`: 模型指纹信息

<br>

## 🎯 适用场景

- 📚 学术研究文献管理
- 📋 企业文档知识库
- 📖 个人资料整理

<br>

## 🛠️ 配置说明

主要配置项位于 `src/mnemo/v1/config/config.json`：

```python
{
    "embedding_model_name": "intfloat/multilingual-e5-large",  # 如果想使用其他 embedding 模型可在这里替换
    "database_folder": "/path/to/your/database",  # 会根据你的 `initialize` 输入自动生成
    "metadata_with_id_path": "/path/to/metadata_with_id.json",  # 会根据你的 `initialize` 输入自动生成
    "model_fingerprint_path": "/path/to/model_fingerprint.json",  # 会根据你的 `initialize` 输入自动生成
    "faiss_index_path": "/path/to/faiss_index.bin"  # 会根据你的 `initialize` 输入自动生成
}
```

<br>

## 📝 许可证

本项目采用MIT许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

**注意**: 本项目需要本地部署Ollama和相关模型，请确保有足够的计算资源。

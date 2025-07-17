# Mnemo - Intelligent Document Search System

> **Language**: [English](README.md) | [中文](README.zh.md)

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.46+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

An AI-powered local document management and search system that supports intelligent indexing, summary generation, and semantic search for PDF and PPT files.

<br>

## ✨ Features

- 🔒 **Local Security**: File identification, indexing, and search all completed locally, ensuring file information security and reliability
- 🖥️ **User-friendly Interface**: Intuitive web interface built with Streamlit
- 📝 **Automatic Summary Generation**: Generate document summaries and keywords using large language models
- 🎯 **Precise Matching**: Efficient similarity search using FAISS vector database
- 🔄 **Incremental Updates**: Smart identification of processed files to avoid duplicate indexing
- 📊 **Multi-format Support**: Parse PDF and PPT files

<br>

## 🚀 Quick Start

### Requirements

- Python 3.10+
- Ollama (for local LLM)
- Currently tested only on Apple M4 chip, modifications may be needed for other systems or chips

### Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/RyleeSnow/mnemo-search.git
   cd mnemo-search
   ```

2. **Install Dependencies**
   ```bash
   pip install -e .
   ```

3. **Start and Configure Ollama**

   ```bash
   ollama pull modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M
   ollama cp "modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M" Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M
   ollama rm "modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M"

   ollama pull "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"
   ollama cp "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M" Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M
   ollama rm "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"
   ```

   - In the `Terminal`, enter the command `ollama list` and press Enter. If you see models `Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M` and `Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M`, the setup is successful.

4. **Launch Application**
   ```bash
   mnemo-v1
   ```

<br>

## 📖 User Guide

### 1. Initialize Database

Initialize the database on first use:

1. Select `initialize` in the sidebar
2. Specify the database storage path
3. Click the `initialize` button

### 2. Document Indexing

Add documents to the search index:

1. Select `organize` option
2. Specify the folder path containing documents
3. Select file types (PDF/PPT)
4. Choose LLM model quality (`Quality`/`Speed`)
5. Click `start` to begin processing

**Notes:**
- Recommended to select a small number of files for initial testing
- By default, all eligible files in the folder will be indexed each time. Previously indexed files will be skipped. Files with the same filename in different folders will be treated as one file and indexed only once.
- It's recommended not to index too many files at once to avoid excessively long processing times.
  - If you select `Quality` in the left `Choose LLM model` menu, it will use the `Mistral-Small-3.2-24B-Instruct-2506:Q4_K_M` model, providing higher accuracy but longer processing time
  - If you select `Speed` in the left `Choose LLM model` menu, it will use the `Nous-Hermes-2-Mistral-7B-DPO:Q4_K_M` model, processing faster but with slightly lower accuracy
  - Through testing, it's generally recommended to use the `Quality` model
- Currently, only `ppt` and `pdf` files are supported (can be selected). If the same content has both `ppt` and `pdf` versions, it's recommended to use the `ppt` version, which can more accurately capture text content and takes relatively less time.
- If you want to temporarily stop during processing, you can click the `Stop` button in the left menu

### 3. Document Search

After completing document indexing, select `search` in the left menu bar, enter your search query, and the system will display file names sorted by relevance from top to bottom.

If you're using Mac, you can click on the file names to open the files directly.

### 4. Ending Usage
- Close the webpage
- Exit the ollama client
- In the window where you ran `mnemo-v1`, press CTRL+C to terminate the process

<br>

## 🏗️ System Architecture

```
src/mnemo/v1/
├── app.py              # Streamlit main application
├── run.py              # Application entry point
├── config/
│   └── config.json     # Configuration file
├── core/
│   ├── document_parser.py      # Document parsing
│   ├── extract_and_summarize.py # Summary generation
│   ├── embedding_and_save.py   # Vector embedding and storage
│   └── search_files.py         # Search functionality
└── scripts/
    └── app_funcs.py    # Application helper functions
```

<br>

## 📁 Data Storage

The system creates the following files in the specified database folder:
- `faiss_index.bin`: FAISS vector index
- `metadata_with_id.json`: Document metadata
- `model_fingerprint.json`: Model fingerprint information

<br>

## 🎯 Use Cases

- 📚 Academic research literature management
- 📋 Enterprise document knowledge base
- 📖 Personal files organization

<br>

## 🛠️ Configuration

Main configuration options in `src/mnemo/v1/config/config.json`:

```python
{
    "embedding_model_name": "intfloat/multilingual-e5-large",  # can be replaced with other embedding models
    "database_folder": "/path/to/your/database",  # automatically generated based on your initialize input
    "metadata_with_id_path": "/path/to/metadata_with_id.json",  # automatically generated based on your initialize input
    "model_fingerprint_path": "/path/to/model_fingerprint.json",  # automatically generated based on your initialize input
    "faiss_index_path": "/path/to/faiss_index.bin"  # automatically generated based on your initialize input
}
```

<br>

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Note**: This project requires local deployment of Ollama and related models. Please ensure you have sufficient computational resources.

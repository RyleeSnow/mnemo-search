#!/usr/bin/env bash
set -e

# 安装 Ollama
echo "【开始下载 Ollama 模型】"

# 拉取所需模型
ollama pull modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M
ollama cp "modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M" Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M
ollama rm "modelscope.cn/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF:Q4_K_M"

ollama pull "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"
ollama cp "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M" Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M
ollama rm "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"

echo "✅ 下载完成"

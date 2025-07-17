### show all models
ollama list

### load local model
cd `model_folder`
echo "FROM ./`model_file`" > Modelfile
ollama create `model_name` -f Modelfile

### pull model
ollama pull "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"
ollama cp "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M" Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M
ollama rm "modelscope.cn/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q4_K_M"

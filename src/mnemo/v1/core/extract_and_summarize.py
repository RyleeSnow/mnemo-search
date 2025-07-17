import json
import re
import socket

import requests
import torch
from sentence_transformers import SentenceTransformer


def select_top_text_blocks(blocks: list[str], topk: int, embedding_model: SentenceTransformer) -> list[str]:
    """
    select top k text blocks based on their embeddings and cosine similarity to the average embedding

    Args:
        blocks (list[str]): list of text blocks to select from.
        topk (int): number of top blocks to select.
        embedding_model (SentenceTransformer): the embedding model to be used for calculating embeddings.
    Returns:
        list[str]: list of top k text blocks based on their embeddings.
    """

    emb = embedding_model.encode(blocks, convert_to_tensor=True)  # encode the blocks to get their embeddings
    avg = emb.mean(dim=0)  # calculate the average embedding vector

    scores = torch.cosine_similarity(emb, avg.unsqueeze(0))  # calculate cosine similarity between each block and the average embedding
    idxs = torch.topk(scores, k=min(topk, len(blocks))).indices  # get the indices of the top k blocks based on cosine similarity

    return [blocks[i] for i in idxs]


def call_ollama_for_summarization(prompt: str, ollama_model_name: str, ollama_url: str) -> str:
    """
    call the Ollama API to get the summarization output

    Args:
        prompt (str): the prompt to send to the Ollama API.
        ollama_model_name (str): the name of the Ollama model to use.
        ollama_url (str): the URL of the Ollama API.
    Returns:
        str: the output text from the Ollama API.
    """

    payload = {
        "model": ollama_model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,  # controls randomness, lower is more deterministic
            "num_predict": 512  # max tokens to generate
        }
    }

    try:
        response = requests.post(ollama_url, json=payload)
        result = response.json()
        output_text = result.get("response", "").strip()
        return output_text

    except requests.RequestException as e:
        return "http_request_error"
    except Exception as e:
        return "unknown_ollama_error"


def summarize_file_by_llm(text_blocks: list[str], file_name: str, llm_model_name: str) -> str:
    """
    summarize the content of a file using an LLM model

    Args:
        text_blocks (list[str]): list of text blocks to summarize.
        file_name (str): name of the file being summarized.
        llm_model_name (str): name of the LLM model to use for summarization.
        ollama_url (str): URL of the Ollama API, default is "http://localhost:11434/api/generate".
    Returns:
        tuple: a tuple containing the Chinese summary and the English summary.
    """
    try:
        socket.gethostbyname("host.docker.internal")
        ollama_url = "http://host.docker.internal:11434/api/generate"
    except socket.gaierror:
        ollama_url = "http://localhost:11434/api/generate"

    prompt_template = """
        你是文档分析专家。请根据下面标记为“原文内容”的部分, 提取3-5个**关键词**, 并分别生成一段高质量的**中文摘要**。

        要求如下：

        - 内容需**忠实于原文，不要编造**
        - 摘要为**一段连贯自然的话**, 讲述核心内容**不要用套话**, 不要重复文件名
        - 参考文件名，但**不要仅凭文件名判断内容**
        - **不要基于文件作者或机构介绍写摘要**（如公司历史、机构信息、埃森哲、麦肯锡）

        ---

        现在内容如下：

        文件名：{file_name}

        原文内容：▋
        {blocks_str}
        ▋

        ⚠️ 输出格式要求：
        仅返回有效的 JSON 格式内容，格式如下：
        {{
        "keywords": ["", "", ""],
        "summary": ""
        }}

        ❌ 不要加入解释、markdown、标题
        ❌ 不要重复 instructions 中的内容
        ❌ 摘要中不要包含文件名或机构介绍
        """.strip()

    blocks_str = "\n".join(f"- {b}" for b in text_blocks)  # format blocks as a bullet list
    prompt = prompt_template.format(file_name=file_name, blocks_str=blocks_str)  # format the prompt with file name and blocks

    # get the LLM output with retry for short summaries
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        llm_output = call_ollama_for_summarization(prompt, ollama_model_name=llm_model_name, ollama_url=ollama_url)
        if llm_output and len(llm_output) >= 100:  # check if the output is long enough
            break
        retry_count += 1

    if llm_output in ["http_request_error", "unknown_ollama_error"]:
        return llm_output, None, None

    # parse the JSON response
    match = re.search(r'\{.*\}', llm_output, re.DOTALL)
    if not match:
        return "json_parse_error", None, None
    json_str = match.group()

    info = json.loads(json_str)

    try:
        summary = info["summary"].strip()  # get the summary from the JSON response
        keywords = info["keywords"]  # get the summary from the JSON response
        summary = summary.replace(file_name, "").strip()  # remove file name from summary
        if len(summary) < 50 or len(keywords) < 1:
            return "invalid_output_error", None, None
    except (KeyError, TypeError, json.JSONDecodeError):
        return "json_parse_error", None, None

    return "valid_output", keywords, summary

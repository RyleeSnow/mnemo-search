import json


def call_ollama_for_summarization_mock(prompt, ollama_model_name, ollama_url):
    return "这是一个模拟的摘要结果。"


def summarize_pages(blocks, prompt_template, page_list):
    chunk = [b for b in blocks if b["page"] in page_list]
    if not chunk:
        return ""
    prompt = prompt_template.replace("{{blocks_json}}", json.dumps(chunk, ensure_ascii=False))
    return call_ollama_for_summarization_mock(prompt, ollama_model_name="test_model", ollama_url="http://localhost:11434/api/generate")


def map_reduce_summary(all_blocks, prompt_template):
    num_pages = max(b["page"] for b in all_blocks)
    summaries = []
    num_pages_per_request = 1

    for i in range(1, num_pages + 1, num_pages_per_request):
        pages = list(range(i, min(i + num_pages_per_request, num_pages + 1)))
        summaries.append(summarize_pages(all_blocks, prompt_template, pages))

    combined = "\n".join(summaries)

    reduce_prompt = f"""
        请将以下几段摘要合并成一个简洁段落，关注核心内容，不要分条，只输出一段：
        {combined}
        """
    return call_ollama_for_summarization_mock(
        reduce_prompt, ollama_model_name="test_model", ollama_url="http://localhost:11434/api/generate"
        )

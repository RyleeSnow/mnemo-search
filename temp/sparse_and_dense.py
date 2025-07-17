import json
import os
import re
from pathlib import Path
from typing import List

import jieba
from langchain.embeddings.base import Embeddings
from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer


def mixed_tokenizer(text):
   # 使用 jieba 分词
   tokens = jieba.cut(text, cut_all=False)
   result = []
   for token in tokens:
       # 用正则进一步拆分中间可能包含的英文段落
       sub_tokens = re.findall(r"[a-zA-Z]+(?:[-'][a-zA-Z]+)?|\d+|\w+", token)
       result.extend(sub_tokens if sub_tokens else [token])
   return result

class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_path: str):
        self.model = SentenceTransformer(model_path, local_files_only=True)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()

if __name__ == "__main__":
    main_folder = str(Path(__file__).resolve().parents[2].absolute())
    metadata_path = os.path.join(main_folder, "data", "metadata.json")
    faiss_index_path = os.path.join(main_folder, "data", "faiss_index.bin")
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # 1️⃣ 构造文档列表
    docs = []
    for item in metadata:
        fname = item.get("file_name", "")
        summary = item.get("summary_zh", "")
        text = f"这个文件 {fname} 的主要内容是关于: {summary}"
        docs.append(Document(page_content=text, metadata={"filename": fname}))

    # 2️⃣ 初始化 BM25 稀疏检索器
    bm25 = BM25Retriever.from_documents(docs, tokenizer=mixed_tokenizer)
    bm25.k = 5
 
    # 3️⃣ 初始化 FAISS + embedding 的 dense 检索器
    local_model_path = r"C:\\github\\mcp_search_local_files\\local_embedding_models\\multilingual-e5-small"
    emb = SentenceTransformerEmbeddings(local_model_path)
    faiss_store = FAISS.from_documents(docs, embedding=emb)
    faiss_retriever = faiss_store.as_retriever(search_kwargs={"k": 5})

    query_lst = [
        "请提供数字化门店或展厅规划相关的文件",
        "请提供数字化旅程和用户体验规划相关的文件",
        "请提供出海规划相关的文件",
        "请提供车企研发相关的文件",
        "请提供电池技术相关的调研或报告文件",
        "请提供商用车行业研究或公司研究相关的文件"
    ]

    # 4️⃣ 构建混合检索器
    hybrid_1 = EnsembleRetriever(
        retrievers=[bm25, faiss_retriever],
        weights=[0.5, 0.5]
    )

    hybrid_2 = EnsembleRetriever(
        retrievers=[bm25, faiss_retriever],
        weights=[0, 1]
    )

    # 5️⃣ 执行查询，获取 filename
    for query in query_lst:
        results_1 = hybrid_1.invoke(query)
        results_2 = hybrid_2.invoke(query)

        filenames_1 = []
        seen_1 = set()
        for doc in results_1:
            fn = doc.metadata["filename"]
            if fn not in seen_1:
                filenames_1.append(fn)

        filenames_2 = []
        seen_2 = set()
        for doc in results_2:
            fn = doc.metadata["filename"]
            if fn not in seen_2:
                filenames_2.append(fn)
                seen_2.add(fn)

        print(f"\n=========== Query: {query} ==========")
        print(f"mix == ")
        for i, fn in enumerate(filenames_1):
            if i <= 4:
                print(f"  {i+1}: {fn}")

        print(f"faiss == ")
        for i, fn in enumerate(filenames_2):
            if i <= 4:
                print(f"  {i+1}: {fn}")
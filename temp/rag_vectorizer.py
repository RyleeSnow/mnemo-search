#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG向量化和存储模块
使用FAISS作为向量数据库，sentence-transformers作为嵌入模型
"""

import json
import os
import pickle
from datetime import datetime
from typing import Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class RAGVectorizer:
    """
    RAG向量化器，负责文档的向量化、存储和检索
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "faiss_index", use_local_model: bool = True):
        """
        初始化RAG向量化器
        
        Args:
            model_name (str): sentence-transformers模型名称
            index_path (str): FAISS索引保存路径
            use_local_model (bool): 是否使用本地模型
        """
        print(f"🚀 初始化RAG向量化器...")
        print(f"📊 加载嵌入模型: {model_name}")
        
        # 确定模型路径
        if use_local_model:
            local_model_path = f"./models/{model_name}"
            if os.path.exists(local_model_path):
                model_path = local_model_path
                print(f"📁 使用本地模型: {local_model_path}")
            else:
                print(f"⚠️ 本地模型不存在: {local_model_path}")
                print(f"💡 请创建目录并下载模型文件到: {local_model_path}")
                print("需要的文件:")
                required_files = [
                    "config.json", "pytorch_model.bin", "tokenizer.json",
                    "tokenizer_config.json", "vocab.txt", "special_tokens_map.json",
                    "modules.json", "sentence_bert_config.json", "config_sentence_transformers.json"
                ]
                for file in required_files:
                    print(f"  - {file}")
                model_path = model_name  # 回退到在线下载
        else:
            model_path = model_name
        
        # 初始化sentence-transformers模型
        try:
            if not use_local_model or not os.path.exists(local_model_path):
                # 处理SSL问题用于在线下载
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
            
            self.model = SentenceTransformer(model_path, device='cpu')
            print(f"✅ 模型加载成功: {model_path}")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print("🔄 尝试备用方案...")
            
            # 备用方案：使用更简单的配置
            try:
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2', device='cpu')
                print("✅ 使用备用模型: paraphrase-MiniLM-L6-v2")
            except:
                print("❌ 无法加载任何sentence-transformers模型")
                print("💡 建议使用简化版本: python simple_rag_test.py")
                raise
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ 模型向量维度: {self.embedding_dim}")
        
        # FAISS索引相关
        self.index = None
        self.index_path = index_path
        self.metadata_path = f"{index_path}_metadata.pkl"
        
        # 存储文档块的元数据
        self.chunks_metadata = []
        self.document_chunks = []
        
        # 创建FAISS索引
        self._create_index()
    
    def _create_index(self):
        """创建FAISS索引"""
        print(f"🔧 创建FAISS索引...")
        # 使用L2距离的平面索引，适合中小规模数据
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        print(f"✅ FAISS索引创建完成")
    
    def add_overlap_to_chunks(self, chunks: List[Dict], overlap_chars: int = 100) -> List[Dict]:
        """
        为文档块添加重叠，保持上下文连续性
        
        Args:
            chunks (List[Dict]): 原始文档块列表
            overlap_chars (int): 重叠字符数
        
        Returns:
            List[Dict]: 添加重叠后的文档块列表
        """
        print(f"🔄 为文档块添加重叠 (重叠字符数: {overlap_chars})")
        
        if not chunks:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            content = chunk['content']
            metadata = chunk['metadata'].copy()
            
            # 添加前置重叠（来自前一个chunk的结尾）
            prefix = ""
            if i > 0:
                prev_content = chunks[i-1]['content']
                if len(prev_content) >= overlap_chars:
                    prefix = "..." + prev_content[-overlap_chars:]
                else:
                    prefix = "..." + prev_content
            
            # 添加后置重叠（来自后一个chunk的开头）
            suffix = ""
            if i < len(chunks) - 1:
                next_content = chunks[i+1]['content']
                if len(next_content) >= overlap_chars:
                    suffix = next_content[:overlap_chars] + "..."
                else:
                    suffix = next_content + "..."
            
            # 构建带重叠的内容
            overlapped_content = f"{prefix} {content} {suffix}".strip()
            
            # 更新元数据
            metadata['has_overlap'] = True
            metadata['original_content'] = content
            metadata['overlap_chars'] = overlap_chars
            
            overlapped_chunk = {
                'chunk_id': chunk['chunk_id'],
                'content': overlapped_content,
                'metadata': metadata
            }
            
            overlapped_chunks.append(overlapped_chunk)
        
        print(f"✅ 重叠添加完成，处理了 {len(overlapped_chunks)} 个文档块")
        return overlapped_chunks
    
    def embed_chunks(self, chunks: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """
        将文档块向量化
        
        Args:
            chunks (List[Dict]): 文档块列表
        
        Returns:
            Tuple[np.ndarray, List[Dict]]: (向量矩阵, 元数据列表)
        """
        print(f"🔄 开始向量化 {len(chunks)} 个文档块...")
        
        # 提取文本内容
        texts = [chunk['content'] for chunk in chunks]
        
        # 批量向量化
        model_name = getattr(self.model, 'model_name', getattr(self.model, '_model_name', 'sentence-transformer'))
        print(f"📊 使用 {model_name} 进行向量化...")
        embeddings = self.model.encode(texts, 
                                     show_progress_bar=True,
                                     batch_size=32,
                                     convert_to_numpy=True)
        
        print(f"✅ 向量化完成，生成 {embeddings.shape} 向量矩阵")
        
        # 准备元数据
        metadata_list = []
        for chunk in chunks:
            metadata = chunk['metadata'].copy()
            metadata['chunk_id'] = chunk['chunk_id']
            metadata['embedding_timestamp'] = datetime.now().isoformat()
            metadata_list.append(metadata)
        
        return embeddings, metadata_list
    
    def add_documents_to_index(self, rag_content: Dict, overlap_chars: int = 100):
        """
        将RAG内容添加到FAISS索引
        
        Args:
            rag_content (Dict): RAG格式的文档内容
            overlap_chars (int): 重叠字符数
        """
        # 获取文件信息
        file_name = rag_content['document_metadata'].get('file_name', 'Unknown')
        file_path = rag_content['document_metadata'].get('file_path', 'Unknown')
        
        print(f"\n📚 开始处理文档: {file_name}")
        print(f"📁 文件路径: {file_path}")
        
        chunks = rag_content['chunks']
        if not chunks:
            print("⚠️ 未找到文档块，跳过处理")
            return
        
        # 添加重叠
        overlapped_chunks = self.add_overlap_to_chunks(chunks, overlap_chars)
        
        # 向量化
        embeddings, metadata_list = self.embed_chunks(overlapped_chunks)
        
        # 添加到FAISS索引
        print(f"💾 将向量添加到FAISS索引...")
        self.index.add(embeddings.astype('float32'))
        
        # 保存元数据
        current_index = len(self.chunks_metadata)
        for i, (chunk, metadata) in enumerate(zip(overlapped_chunks, metadata_list)):
            metadata['faiss_index'] = current_index + i
            self.chunks_metadata.append(metadata)
            self.document_chunks.append(chunk)
        
        print(f"✅ 成功添加 {len(overlapped_chunks)} 个向量到索引")
        print(f"📊 当前索引总量: {self.index.ntotal} 个向量")
    
    def save_index(self):
        """保存FAISS索引和元数据"""
        print(f"\n💾 保存FAISS索引到: {self.index_path}")
        
        # 创建保存目录
        os.makedirs(os.path.dirname(self.index_path) if os.path.dirname(self.index_path) else ".", exist_ok=True)
        
        # 保存FAISS索引
        faiss.write_index(self.index, f"{self.index_path}.faiss")
        
        # 保存元数据
        metadata_to_save = {
            'chunks_metadata': self.chunks_metadata,
            'document_chunks': self.document_chunks,
            'model_name': getattr(self.model, 'model_name', getattr(self.model, '_model_name', 'sentence-transformer')),
            'embedding_dim': self.embedding_dim,
            'created_at': datetime.now().isoformat(),
            'total_vectors': self.index.ntotal
        }
        
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(metadata_to_save, f)
        
        print(f"✅ 索引保存完成")
        print(f"  - FAISS索引: {self.index_path}.faiss")
        print(f"  - 元数据: {self.metadata_path}")
    
    def load_index(self) -> bool:
        """
        加载已保存的FAISS索引和元数据
        
        Returns:
            bool: 是否成功加载
        """
        faiss_file = f"{self.index_path}.faiss"
        
        if not os.path.exists(faiss_file) or not os.path.exists(self.metadata_path):
            print(f"⚠️ 未找到已保存的索引文件")
            return False
        
        try:
            print(f"📂 加载FAISS索引: {faiss_file}")
            self.index = faiss.read_index(faiss_file)
            
            print(f"📂 加载元数据: {self.metadata_path}")
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.chunks_metadata = metadata['chunks_metadata']
            self.document_chunks = metadata['document_chunks']
            
            print(f"✅ 索引加载完成")
            print(f"  - 向量数量: {self.index.ntotal}")
            print(f"  - 文档块数量: {len(self.chunks_metadata)}")
            print(f"  - 创建时间: {metadata.get('created_at', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 加载索引失败: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, file_filter: str = None) -> List[Dict]:
        """
        在索引中搜索相关文档块
        
        Args:
            query (str): 查询文本
            top_k (int): 返回的结果数量
            file_filter (str): 可选的文件名过滤器
        
        Returns:
            List[Dict]: 搜索结果列表
        """
        if self.index.ntotal == 0:
            print("⚠️ 索引为空，无法搜索")
            return []
        
        print(f"🔍 搜索查询: '{query}' (top_k={top_k})")
        if file_filter:
            print(f"📁 文件过滤: {file_filter}")
        
        # 对查询向量化
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # 在FAISS中搜索 - 先搜索更多结果以便过滤
        search_k = top_k * 3 if file_filter else top_k
        distances, indices = self.index.search(query_embedding.astype('float32'), search_k)
        
        # 构建结果
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0 and idx < len(self.chunks_metadata):
                metadata = self.chunks_metadata[idx]
                
                # 如果有文件过滤器，检查文件名
                if file_filter:
                    file_name = metadata.get('file_name', '')
                    if file_filter.lower() not in file_name.lower():
                        continue
                
                result = {
                    'rank': len(results) + 1,
                    'score': float(distance),
                    'similarity': 1 / (1 + float(distance)),  # 转换为相似度分数
                    'chunk': self.document_chunks[idx],
                    'metadata': metadata
                }
                results.append(result)
                
                # 如果已经找到足够的结果就停止
                if len(results) >= top_k:
                    break
        
        print(f"✅ 找到 {len(results)} 个相关结果")
        return results
    
    def get_file_statistics(self) -> Dict:
        """获取按文件分组的统计信息"""
        file_stats = {}
        
        for metadata in self.chunks_metadata:
            file_name = metadata.get('file_name', 'Unknown')
            if file_name not in file_stats:
                file_stats[file_name] = {
                    'chunk_count': 0,
                    'file_path': metadata.get('file_path', 'Unknown'),
                    'pages': set()
                }
            
            file_stats[file_name]['chunk_count'] += 1
            if 'page_number' in metadata:
                file_stats[file_name]['pages'].add(metadata['page_number'])
        
        # 转换页面集合为列表
        for file_name in file_stats:
            file_stats[file_name]['pages'] = sorted(list(file_stats[file_name]['pages']))
            file_stats[file_name]['page_count'] = len(file_stats[file_name]['pages'])
        
        return file_stats
    
    def print_file_statistics(self):
        """打印按文件分组的统计信息"""
        file_stats = self.get_file_statistics()
        
        print(f"\n📁 文件统计信息:")
        for file_name, stats in file_stats.items():
            print(f"  📄 {file_name}:")
            print(f"    - 文档块数: {stats['chunk_count']}")
            print(f"    - 页面数: {stats['page_count']}")
            print(f"    - 文件路径: {stats['file_path']}")
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'embedding_dimension': self.embedding_dim,
            'total_chunks': len(self.chunks_metadata),
            'model_name': getattr(self.model, 'model_name', getattr(self.model, '_model_name', 'sentence-transformer')),
            'index_path': self.index_path
        }
    
    def print_stats(self):
        """打印索引统计信息"""
        stats = self.get_stats()
        print(f"\n📊 RAG向量库统计信息:")
        print(f"  - 向量总数: {stats['total_vectors']}")
        print(f"  - 向量维度: {stats['embedding_dimension']}")
        print(f"  - 文档块数: {stats['total_chunks']}")
        print(f"  - 嵌入模型: {stats['model_name']}")
        print(f"  - 索引路径: {stats['index_path']}")
        
        # 同时打印文件统计信息
        self.print_file_statistics()


def load_rag_content(json_file: str) -> Dict:
    """
    从JSON文件加载RAG内容
    
    Args:
        json_file (str): JSON文件路径
    
    Returns:
        Dict: RAG内容
    """
    print(f"📂 加载RAG内容: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        content = json.load(f)
    print(f"✅ 加载完成，包含 {len(content.get('chunks', []))} 个文档块")
    return content


def main():
    """主函数：演示RAG向量化流程"""
    print("🚀 RAG向量化系统演示")
    print("=" * 50)
    
    # 初始化向量化器
    vectorizer = RAGVectorizer(
        model_name="all-MiniLM-L6-v2",
        index_path="./rag_index/faiss_index"
    )
    
    # 尝试加载已有索引
    if vectorizer.load_index():
        print("📂 使用已有索引")
    else:
        print("🆕 创建新索引")
        
        # 加载PDF提取的RAG内容
        # 使用tmall_pnp_method_sop_rag_ready.json作为示例
        rag_files = [
            "tmall_pnp_method_sop_rag_ready.json"
        ]
        
        for rag_file in rag_files:
            if os.path.exists(rag_file):
                try:
                    rag_content = load_rag_content(rag_file)
                    vectorizer.add_documents_to_index(rag_content, overlap_chars=100)
                except Exception as e:
                    print(f"❌ 处理文件 {rag_file} 失败: {e}")
            else:
                print(f"⚠️ 文件不存在: {rag_file}")
        
        # 保存索引
        vectorizer.save_index()
    
    # 打印统计信息
    vectorizer.print_stats()
    
    # 演示搜索功能
    print("\n" + "=" * 50)
    print("🔍 搜索演示")
    
    test_queries = [
        "weekly split units 如何计算",
        "monthly promo price 设置方法", 
        "daily units 处理流程",
        "促销价格计算",
        "weekly promo price bau"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = vectorizer.search(query, top_k=3)
        
        for result in results:
            print(f"  {result['rank']}. 相似度: {result['similarity']:.3f}")
            print(f"     文件: {result['metadata'].get('file_name', 'Unknown')}")
            print(f"     页面: {result['metadata']['page_number']}")
            print(f"     内容: {result['chunk']['content'][:100]}...")
            if 'original_content' in result['metadata']:
                print(f"     原文: {result['metadata']['original_content'][:80]}...")
            print()


if __name__ == "__main__":
    main()

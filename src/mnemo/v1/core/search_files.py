import gc
import json
import os

import faiss
from sentence_transformers import SentenceTransformer


def search_by_embedding(query: str, embedding_model: SentenceTransformer, metadata_with_id_path: str, faiss_index_path: str, top_k=5) -> list[dict]:
    """
    search for the most relevant documents in the FAISS index based on a query.

    Args:
        query (str): the search query string
        metadata_with_id_path (str): the path to the metadata file with document IDs
        faiss_index_path (str): the path to the FAISS index file
        top_k (int): the number of top results to return (default is 5)
    Returns:
        list: a list of dictionaries containing the metadata of the top-k results
    """

    if not os.path.exists(faiss_index_path) or not os.path.exists(metadata_with_id_path):
        raise FileNotFoundError(f"🚫 there is no vector database built {faiss_index_path}, please run index_documents() first.")

    try:
        query_vec = embedding_model.encode(
            [query],
            normalize_embeddings=True,  # fix: ensure normalization
            batch_size=32,  # fix: fixed batch size to avoid memory impact
            show_progress_bar=False,  # fix: disable progress bar
            convert_to_numpy=True  # fix: ensure output format consistency
        )  # encode the query using the same model and parameters

        index = faiss.read_index(faiss_index_path)
        scores, doc_ids = index.search(query_vec.astype('float32'), top_k)
    finally:
        del query_vec  # free memory
        del index  # free memory
        gc.collect()  # force garbage collection

    with open(metadata_with_id_path, 'r', encoding='utf-8') as f:
        metadata_with_id = json.load(f)

    searched_result = []
    for doc_id, score in zip(doc_ids[0], scores[0]):
        if doc_id == -1:
            continue
        result = metadata_with_id[str(doc_id)].copy()
        result['search_score'] = score
        searched_result.append(result)

    return searched_result

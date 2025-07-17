import hashlib
import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def get_model_fingerprint(embedding_model_name: str, embedding_model: SentenceTransformer) -> str:
    """
    define a lightweight model fingerprint that only checks core parameters

    Args:
        embedding_model_name (str): the name of the embedding model
        embedding_model (SentenceTransformer): the SentenceTransformer model instance
    Returns:
        str: a short MD5 hash representing the model fingerprint
    """

    core_info = f"{embedding_model_name}_{embedding_model.get_sentence_embedding_dimension()}_normalize_True"
    return hashlib.md5(core_info.encode()).hexdigest()[:8]


def compute_document_id(file_path: str) -> int:
    """compute a unique document ID based on the file path"""

    hash_obj = hashlib.md5(file_path.encode('utf-8'))
    return int(hash_obj.hexdigest()[:8], 16)


def build_text_for_embedding(metadata_dict: dict) -> str:
    """
    extract metadata and build a text for embedding

    Args:
        metadata_dict (dict): a dictionary containing document metadata, expected keys:
            - file_name (str): the name of the file
            - keywords (list[str]): a list of keywords associated with the document
            - summary (str): the Chinese summary of the document
    Returns:
        str: a formatted string containing the file name, keywords, and summary
    """

    file_name = metadata_dict['file_name']
    summary = metadata_dict['summary']
    keywords = metadata_dict['keywords']
    keywords = [kw.strip() for kw in keywords if kw.strip()]  # clean up keywords
    keywords = keywords[:(min(len(keywords), 5))]  # limit to max 5 keywords

    keywords_str = ', '.join(keywords) if keywords else ''
    file_name_str = file_name.split('.')[0]  # remove file extension for cleaner text

    return f"passage: {file_name_str} - {keywords_str} - {summary}"


def encode_texts_lst(texts_lst: list[str], embedding_model: SentenceTransformer) -> tuple[np.ndarray, list[int]] | tuple[None, None]:
    """
    encode input texts using the embedding model, with consistent parameters

    Args:
        texts_lst (list[str]): a list of input texts to be encoded
        embedding_model (SentenceTransformer): the SentenceTransformer model instance
    Returns:
        tuple: (np.ndarray, list[int]) if successful, where np.ndarray contains the encoded vectors
               and list[int] contains the corresponding text indices.
        tuple: (None, None) if no valid vectors are found.
    """

    assert len(texts_lst) > 0, "input texts list cannot be empty."

    # fix core parameters to ensure consistency
    vectors = embedding_model.encode(
        texts_lst,
        normalize_embeddings=True,  # fix: ensure normalization
        batch_size=32,  # fix: fixed batch size to avoid memory impact
        show_progress_bar=False,  # fix: disable progress bar
        convert_to_numpy=True  # fix: ensure output format consistency
    )

    valid_vectors = []
    valid_indices = []

    # filter out invalid vectors (NaN or all zeros)
    for i, v in enumerate(vectors):
        if np.any(np.isnan(v)) or np.allclose(v, 0):
            continue
        valid_vectors.append(v)
        valid_indices.append(i)

    if not valid_vectors:
        return None, None

    return np.array(valid_vectors), valid_indices


def load_index(embedding_model_name: str, embedding_model: SentenceTransformer, faiss_index_path: str, model_fingerprint_path: str) -> tuple[faiss.IndexIDMap2, str]:
    """
    load existing FAISS index and do a model consistency check

    Args:
        embedding_model_name (str): the name of the embedding model
        embedding_model (SentenceTransformer): the SentenceTransformer model instance
        faiss_index_path (str): the path to the FAISS index file
        model_fingerprint_path (str): the path to the model fingerprint JSON file
    Returns:
        tuple: (faiss.IndexIDMap2, str) if successful, where the first element is the loaded FAISS index
               and the second is the model consistency status ("consistent" or "changed").
    """

    # read from FAISS index file
    index = faiss.read_index(faiss_index_path)

    # read model fingerprint from JSON file
    with open(model_fingerprint_path, "r", encoding="utf-8") as f:  # read metadata from JSON file
        model_fingerprint = json.load(f)

    # check model consistency
    model_consistency = "consistent"  # default to consistent

    if isinstance(model_fingerprint, dict) and "fingerprint" in model_fingerprint:
        stored_fingerprint = model_fingerprint["fingerprint"]
        current_fingerprint = get_model_fingerprint(embedding_model_name, embedding_model)  # compute current fingerprint

        if stored_fingerprint != current_fingerprint:
            model_consistency = "changed"  # mark model_consistency as `changed`
            print(f"⚠️ detected model change! if search results are abnormal, please consider rebuilding the index.")
        else:
            print(f"✅ model consistency check passed.")

    return index, model_consistency


def save_index_and_metadata(index: faiss.IndexIDMap2, metadata_with_id: dict, embedding_model_name: str, embedding_model: SentenceTransformer,
                            faiss_index_path: str, metadata_with_id_path: str, model_fingerprint_path: str) -> None:
    """
    save the FAISS index, metadata with document IDs, and model fingerprint to disk

    Args:
        index (faiss.IndexIDMap2): the FAISS index to save
        metadata_with_id (dict): the metadata dictionary with document IDs as keys
        embedding_model_name (str): the name of the embedding model
        embedding_model (SentenceTransformer): the SentenceTransformer model instance
        faiss_index_path (str): the path to the FAISS index file
        metadata_with_id_path (str): the path to save the metadata with ID file
        model_fingerprint_path (str): the path to save the model fingerprint JSON file
    Returns:
        None
    """

    # ensure directories exist
    os.makedirs(os.path.dirname(faiss_index_path), exist_ok=True)
    os.makedirs(os.path.dirname(model_fingerprint_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_with_id_path), exist_ok=True)

    # write index
    faiss.write_index(index, faiss_index_path)

    # write metadata with ID to JSON file
    with open(metadata_with_id_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_with_id, f, ensure_ascii=False, indent=4)

    # write lightweight metadata structure with fingerprint
    model_fingerprint = {"fingerprint": get_model_fingerprint(embedding_model_name=embedding_model_name, embedding_model=embedding_model)}
    with open(model_fingerprint_path, "w", encoding="utf-8") as f:
        json.dump(model_fingerprint, f, ensure_ascii=False, indent=4)


def index_files(doc_metadata_list: list[dict[str, str]], embedding_model_name: str, embedding_model: SentenceTransformer, faiss_index_path: str,
                metadata_with_id_path: str, model_fingerprint_path: str,
                ) -> tuple[str, list]:
    """
    create or update FAISS index from a list of document metadata, handling both new index creation and incremental updates

    Args:
        doc_metadata_list (list): a list of document metadata dictionaries, each containing:
            - file_name: str, the name of the file
            - file_path: str, the full path of the file
            - keywords: list[str], a list of keywords associated with the document
            - summary: str, the Chinese summary of the document
        embedding_model_name (str): the name of the embedding model
        embedding_model (SentenceTransformer): the SentenceTransformer model instance
        faiss_index_path (str): the path to save the FAISS index file
        metadata_with_id_path (str): the path to save the metadata with ID file
        model_fingerprint_path (str): the path to save the model fingerprint JSON file
    Returns:
        tuple: (status_string, list_of_invalid_files)
    """

    assert len(doc_metadata_list) > 0, "document metadata list cannot be empty."

    # check if index and metadata already exist
    index_exists = os.path.exists(faiss_index_path)
    metadata_with_id_exists = os.path.exists(metadata_with_id_path)
    model_fingerprint_exists = os.path.exists(model_fingerprint_path)

    if index_exists and metadata_with_id_exists and model_fingerprint_exists:
        print(f'📦 Loading existing index and adding {len(doc_metadata_list)} new files...')

        # load existing index
        faiss_index, model_consistency = load_index(faiss_index_path=faiss_index_path, model_fingerprint_path=model_fingerprint_path,
                                                    embedding_model_name=embedding_model_name, embedding_model=embedding_model)

        # if model consistency check fails, return error
        if model_consistency == "changed":
            invalid_files = [doc_meta['file_name'] for doc_meta in doc_metadata_list]
            return "model_changed_error", invalid_files

        # load existing metadata
        with open(metadata_with_id_path, 'r', encoding='utf-8') as f:
            existing_metadata_dict = json.load(f)

        # convert string keys back to int for comparison
        existing_doc_ids = set(int(k) for k in existing_metadata_dict.keys())

    else:
        print(f'📦 Creating new index for {len(doc_metadata_list)} files...')
        model_consistency = "new_index"

        # create new index
        dim = embedding_model.get_sentence_embedding_dimension()
        base_index = faiss.IndexFlatIP(dim)
        faiss_index = faiss.IndexIDMap2(base_index)
        existing_metadata_dict = {}
        existing_doc_ids = set()
        model_consistency = "consistent"

    # process new documents
    new_ebd_texts_lst = []
    new_doc_ids = []
    new_metadata_dict = {}
    invalid_files = []

    for doc_meta in doc_metadata_list:
        # create a unique document ID based on the file path
        doc_id = compute_document_id(doc_meta['file_path'])
        assert doc_id not in existing_doc_ids, f"Document ID {doc_id} already exists in index."

        # build text for embedding
        ebd_text = build_text_for_embedding(metadata_dict=doc_meta)

        # add to new lists
        new_ebd_texts_lst.append(ebd_text)
        new_doc_ids.append(doc_id)
        new_metadata_dict[doc_id] = doc_meta

    # encode new texts
    assert len(new_ebd_texts_lst) == len(doc_metadata_list), "new embedding texts list length must match document metadata list length."
    valid_vectors, valid_indices = encode_texts_lst(new_ebd_texts_lst, embedding_model=embedding_model)

    # if no valid vectors are found, return error
    if valid_vectors is None:
        invalid_files = [doc_meta['file_name'] for doc_meta in doc_metadata_list]
        return "no_valid_vectors_error", invalid_files

    # if there are more document metadata than valid vectors, track invalid files
    if len(doc_metadata_list) > len(valid_vectors):
        invalid_files = [doc_metadata_list[i]['file_name'] for i in range(len(doc_metadata_list)) if i not in valid_indices]

    # get valid doc_ids and metadata_dict
    valid_doc_ids = [new_doc_ids[i] for i in valid_indices]
    valid_metadata_dict = {str(doc_id): new_metadata_dict[doc_id] for doc_id in valid_doc_ids}

    # add new vectors to index
    faiss_index.add_with_ids(valid_vectors.astype('float32'), np.array(valid_doc_ids, dtype='int64'))

    # ensure all keys in existing_metadata_dict are strings for consistency
    existing_metadata_dict_str_keys = {str(k): v for k, v in existing_metadata_dict.items()}

    # merge metadata dictionaries
    combined_metadata_dict = existing_metadata_dict_str_keys | valid_metadata_dict
    # check if index has same length with metadata
    assert faiss_index.ntotal == len(combined_metadata_dict), "FAISS index and metadata length mismatch."

    # save updated index and metadata
    save_index_and_metadata(index=faiss_index, metadata_with_id=combined_metadata_dict, embedding_model_name=embedding_model_name,
                            embedding_model=embedding_model, faiss_index_path=faiss_index_path, metadata_with_id_path=metadata_with_id_path,
                            model_fingerprint_path=model_fingerprint_path)

    if model_consistency == "new_index":
        print(f"✅ New index created with {len(valid_doc_ids)} documents")
    else:
        print(f"✅ Index updated: {len(valid_doc_ids)} new documents added, {len(combined_metadata_dict)} total documents")

    return "valid_output", invalid_files

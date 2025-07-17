import json
import os
import subprocess
from pathlib import Path

import streamlit as st
from sentence_transformers import SentenceTransformer
from sympy import im

from mnemo.v1.core.document_parser import parse_document
from mnemo.v1.core.embedding_and_save import index_files
from mnemo.v1.core.extract_and_summarize import (
    select_top_text_blocks,
    summarize_file_by_llm,
)
from mnemo.v1.core.search_files import search_by_embedding


def initialize_config(database_folder: str) -> None:
    """
    initialize the data folder and update the config file

    Args:
        database_folder (str): the folder where the database will be stored
    Returns:
        None
    """

    # load config json
    with open(os.path.join(str(Path(__file__).parents[1].joinpath("config").absolute()), "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)

    if not os.path.exists(database_folder):
        os.makedirs(database_folder, exist_ok=True)

    # update the parameters in config
    config["database_folder"] = database_folder
    config["metadata_path"] = os.path.join(database_folder, "metadata.json")
    config["metadata_with_id_path"] = os.path.join(database_folder, "metadata_with_id.json")
    config["model_fingerprint_path"] = os.path.join(database_folder, "model_fingerprint_path.json")
    config["faiss_index_path"] = os.path.join(database_folder, "faiss_index.bin")

    # save the updated config back to the file
    with open(os.path.join(str(Path(__file__).parents[1].joinpath("config").absolute()), "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def filter_files_by_type(full_files_lst: list[str], incl_file_types: list[str]) -> list[str]:
    """
    filter files by the specified types

    Args:
        full_files_lst (list[str]): list of all files in the folder
        incl_file_types (list[str]): list of file types to include
    Returns:
        list[str]: list of files that match the specified types and are not already indexed
    """

    if not full_files_lst:
        return []

    # filter files by the specified types
    filtered_by_type = set([file for file in full_files_lst if any(file.endswith(ext) for ext in incl_file_types)])

    # load config json
    with open(os.path.join(str(Path(__file__).parents[1].joinpath("config").absolute()), "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)
    metadata_with_id_path = config["metadata_with_id_path"]

    # check if metadata_with_id_path exists and load existing files
    if os.path.exists(metadata_with_id_path):
        existing_files = set()
        with open(metadata_with_id_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            for _, info in metadata.items():
                existing_files.add(info["file_name"])
    else:
        existing_files = set()

    # filter out files that are already indexed
    filtered_file_lst = list(filtered_by_type - existing_files)

    return filtered_file_lst


def summarize_file(file_folder: str, file_name: str, embedding_model: SentenceTransformer, summarize_llm_model_name: str) -> tuple[str, list[str], str]:
    """
    organize files by parsing, embedding, and summarizing them

    Args:
        file_folder (str): the folder where the files are located
        file_name (str): the name of the file to be processed
        embedding_model (SentenceTransformer): the embedding model to be used for text blocks
    Returns:
        tuple: a tuple containing the output tag, keywords, and summary of the file
    """

    # load config json
    with open(os.path.join(str(Path(__file__).parents[1].joinpath("config").absolute()), "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)

    # get the parameters from config
    metadata_with_id_path = config["metadata_with_id_path"]

    # parse the document and extract text blocks
    text_blocks = parse_document(os.path.join(file_folder, file_name), metadata_with_id_path=metadata_with_id_path)

    if text_blocks is None:
        return "text_blocks_error", None, None

    # select top text blocks based on file type
    try:
        if file_name.endswith(".pptx"):
            selected_blocks = select_top_text_blocks(text_blocks, topk=10, embedding_model=embedding_model)
        elif file_name.endswith(".pdf"):
            selected_blocks = select_top_text_blocks(text_blocks, topk=20, embedding_model=embedding_model)
        else:
            return "file_type_error", None, None
    except ValueError as e:
        return "top_text_blocks_error", None, None

    output_tag, keywords, summary = summarize_file_by_llm(text_blocks=selected_blocks, file_name=file_name, llm_model_name=summarize_llm_model_name)

    return output_tag, keywords, summary


def organize_files(doc_metadata_list: list[dict[str, str]], embedding_model: SentenceTransformer) -> tuple[str, list[str]]:
    """
    organize files by embedding and saving the index and metadata

    Args:
        doc_metadata_list (list[dict[str, str]]): list of document metadata dictionaries
        embedding_model (SentenceTransformer): the embedding model to be used
    Returns:
        tuple: a tuple containing the status string and a list of invalid files
    """

    with open(os.path.join(str(Path(__file__).parents[1].joinpath("config").absolute()), "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)

    # get the parameters from config
    embedding_model_name = config["embedding_model_name"]
    faiss_index_path = config["faiss_index_path"]
    metadata_with_id_path = config["metadata_with_id_path"]
    model_fingerprint_path = config["model_fingerprint_path"]

    # embedding and save the index and metadata
    status_str, invalid_files = index_files(doc_metadata_list=doc_metadata_list, embedding_model_name=embedding_model_name, embedding_model=embedding_model,
                                            faiss_index_path=faiss_index_path, metadata_with_id_path=metadata_with_id_path,
                                            model_fingerprint_path=model_fingerprint_path)

    return status_str, invalid_files


def cut_text(text: str, max_length: int = 70) -> str:
    """cut text to a specified length, considering multi-byte characters"""

    def calculate_length(s):
        return sum(2 if ord(c) > 127 else 1 for c in s)

    if calculate_length(text) <= max_length:
        return text
    else:
        truncated_text = ""
        current_length = 0
        for char in text:
            char_length = 2 if ord(char) > 127 else 1
            if current_length + char_length > max_length:
                break
            truncated_text += char
            current_length += char_length
        return truncated_text + "..."


def open_file_in_finder(file_path):
    """open the file in the system's file explorer"""

    subprocess.run(["open", str(Path(file_path).absolute())])


def search_files(query: str, top_k: int, embedding_model: SentenceTransformer) -> list[dict[str, str]]:
    """
    search files based on the query and return the results

    Args:
        query (str): the search query
        top_k (int): the number of top results to return
        embedding_model (SentenceTransformer): the embedding model to be used for searching
    Returns:
        list[dict[str, str]]: a list of dictionaries containing the search results
    """

    # load config json
    with open(os.path.join(str(Path(__file__).parents[1].joinpath("config").absolute()), "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)

    # get the paths from config
    metadata_with_id_path = config["metadata_with_id_path"]
    faiss_index_path = config["faiss_index_path"]

    if not os.path.exists(metadata_with_id_path) or not os.path.exists(faiss_index_path):
        st.error("Database not initialized. Please initialize the database first.")
        return []

    # search files using the query
    query = "query: " + query.strip()
    search_results = search_by_embedding(query, embedding_model=embedding_model, metadata_with_id_path=metadata_with_id_path, faiss_index_path=faiss_index_path,
                                         top_k=top_k)

    return search_results

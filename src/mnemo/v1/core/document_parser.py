import json
import os

from mnemo.v1.core.extract_file_text.parse_pdf import parse_pdf_to_block_info
from mnemo.v1.core.extract_file_text.parse_ppt import parse_ppt_to_get_headers


def load_existing_file_names(metadata_with_id_path: str) -> list | None:
    """
    load existing file names from the metadata file

    Args:
        metadata_with_id_path (str): path to the metadata file with IDs
    Returns:
        list[str] | None: list of existing file names or None if the metadata file does not exist
    """

    if not os.path.exists(metadata_with_id_path):
        return None
    else:
        with open(metadata_with_id_path, "r", encoding="utf-8") as f:
            metadata_with_id = json.load(f)

        existing_files = [info["file_name"] for _, info in metadata_with_id.items()]

        if not existing_files:
            return None
        else:
            return existing_files


def parse_document(file_path: str, metadata_with_id_path: str) -> list[str] | None:
    """
    parse the document file to extract text or headers

    Args:
        file_path (str): path to the document file.
        metadata_with_id_path (str): path to the metadata file with IDs.
    Returns:
        list[str] | None: list of text blocks or headers extracted from the document,
            or None if the file does not exist or has already been processed
    """

    if not os.path.exists(file_path):
        print(f"Warning: no such file: {file_path}")
        return None

    file_name = os.path.basename(file_path)
    existing_file_names = load_existing_file_names(metadata_with_id_path=metadata_with_id_path)

    if existing_file_names is not None and file_name in existing_file_names:
        return None

    if file_name.endswith(".pdf"):
        try:
            return parse_pdf_to_block_info(pdf_path=file_path, only_text=True)
        except Exception as e:
            raise ValueError(f"Error parsing PDF file {file_path}: {e}")
    elif file_name.endswith(".pptx"):
        try:
            return parse_ppt_to_get_headers(ppt_path=file_path)
        except Exception as e:
            raise ValueError(f"Error parsing PPTX file {file_path}: {e}")
    else:
        return None

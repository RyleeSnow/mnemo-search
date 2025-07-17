import fitz

from mnemo.v1.core.extract_file_text.parse_doc_utils import (
    check_line_validity,
    clean_whitespace,
)


def parse_pdf_to_block_info(pdf_path: str, only_text: bool = True, min_block_len: int = 10, header_height: int = 100, footer_height: int = 100):
    """
    parse a PDF file and extract structured text blocks

    Args:
        pdf_path (str): path to the PDF file
        only_text (bool): if True, return only text strings; if False, return detailed block info
        min_block_len (int): minimum length of text blocks to keep
        header_height (int): height of the header area to skip
        footer_height (int): height of the footer area to skip
    Returns:
        list: a list of text blocks or text strings depending on `only_text`
    """

    doc = fitz.open(pdf_path)  # open the PDF file
    all_blocks = []  # list to hold all text blocks

    for page_num, page in enumerate(doc, 1):
        page_height = page.rect.height  # height of the page
        blocks = page.get_text("dict")["blocks"]  # get text blocks from the page

        for b in blocks:
            if b["type"] != 0:
                continue  # only process text blocks

            y0 = b["bbox"][1]  # top y-coordinate of the block
            y1 = b["bbox"][3]  # bottom y-coordinate of the block
            if y0 < header_height or y1 > (page_height - footer_height):
                continue  # skip header and footer areas

            lines = []
            for line in b["lines"]:
                line_text = " ".join(span["text"] for span in line["spans"])  # join spans in the line
                if line_text and check_line_validity(line_text):  # check if the line is valid
                    lines.append(line_text)  # clean and add the line text

            if lines:
                block_text = " ".join(lines)  # join all lines in the block
                block_text = clean_whitespace(block_text)  # clean whitespace in the block text
                block_text = block_text.strip()  # strip leading and trailing whitespace
                if len(block_text) < min_block_len:  # skip blocks that are too short
                    continue

                # Safely extract font and font_size if lines and spans exist
                font_size = None
                font = None

                if b["lines"] and b["lines"][0]["spans"]:
                    font_size = round(b["lines"][0]["spans"][0].get("size", 0), 1)
                    font = b["lines"][0]["spans"][0].get("font", "")

                block_info = {
                    "page": page_num,
                    "text": block_text,
                    "x": round(b["bbox"][0], 2),
                    "y": round(b["bbox"][1], 2),
                    "width": round(b["bbox"][2] - b["bbox"][0], 2),
                    "height": round(b["bbox"][3] - b["bbox"][1], 2),
                    "font_size": font_size,
                    "font": font
                }
                all_blocks.append(block_info)

    if only_text:
        # If only text is required, return a list of text strings
        return [block["text"] for block in all_blocks]
    else:
        # If detailed block info is required, return the full block info
        return all_blocks



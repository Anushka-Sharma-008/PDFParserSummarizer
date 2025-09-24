import json
import pdfplumber
import fitz  # PyMuPDF

def parse_pdf(file_path):
    extracted_data = {"pages": []}
    section_title = None

    try:
        with fitz.open(file_path) as doc:
            for page_number, page in enumerate(doc, 1):
                page_data = {"page_number": page_number, "content": []}

                blocks = page.get_text("blocks")

                font_sizes = [b[4] for b in blocks if len(b) > 4]
                max_font_size = max(font_sizes) if font_sizes else 0

                for block in blocks:
                    if len(block) < 5:
                        continue
                    text_content = block[4].strip().replace("\n", " ")
                    font_size = block[4]

                    if font_size >= max_font_size and len(text_content.split()) < 10:
                        section_title = text_content
                        continue

                    if text_content and text_content not in ["", "\n", " "]:
                        page_data["content"].append({
                            "type": "paragraph",
                            "section": section_title,
                            "text": text_content,
                        })

                with pdfplumber.open(file_path) as pdf_plumber_doc:
                    pdf_plumber_page = pdf_plumber_doc.pages[page_number - 1]
                    tables = pdf_plumber_page.find_tables()

                    for table in tables:
                        table_data = table.extract()
                        if table_data:
                            page_data["content"].append({
                                "type": "table",
                                "section": section_title,
                                "table_data": table_data,
                                "description": None
                            })

                extracted_data["pages"].append(page_data)

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None

    return extracted_data
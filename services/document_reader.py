
import pymupdf
from pptx import Presentation


def extract_pdf_text(file_path):
    """Extract text from a PDF file."""

    extracted_text = []

    try:
        document = pymupdf.open(file_path)

        for page_number, page in enumerate(document, start=1):
            page_text = page.get_text("text")

            if page_text.strip():
                extracted_text.append(
                    f"\n--- Page {page_number} ---\n{page_text}"
                )

        document.close()

        return "\n".join(extracted_text)

    except Exception as error:
        raise ValueError(f"PDF extraction failed: {error}")


def extract_pptx_text(file_path):
    """Extract text from a PowerPoint file."""

    extracted_text = []

    try:
        presentation = Presentation(file_path)

        for slide_number, slide in enumerate(
            presentation.slides, start=1
        ):
            slide_text = []

            for shape in slide.shapes:
                if shape.has_text_frame:
                    text = shape.text.strip()

                    if text:
                        slide_text.append(text)

                if shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                slide_text.append(cell.text.strip())

            if slide_text:
                extracted_text.append(
                    f"\n--- Slide {slide_number} ---\n"
                    + "\n".join(slide_text)
                )

        return "\n".join(extracted_text)

    except Exception as error:
        raise ValueError(f"PPTX extraction failed: {error}")


def extract_document_text(file_path, file_type):
    """Select the correct extraction method."""

    file_type = file_type.lower()

    if file_type == "pdf":
        return extract_pdf_text(file_path)

    elif file_type == "pptx":
        return extract_pptx_text(file_path)

    raise ValueError("Unsupported document format.")

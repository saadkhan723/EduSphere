
from pathlib import Path
from services.document_reader import extract_document_text

UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads" / "documents"

files = list(UPLOAD_FOLDER.glob("*.pdf"))
files += list(UPLOAD_FOLDER.glob("*.pptx"))

if not files:
    print("No PDF or PPTX files found in uploads/documents.")
else:
    file_path = files[0]
    file_type = file_path.suffix.lower().replace(".", "")

    print("Testing file:", file_path.name)

    try:
        extracted_text = extract_document_text(
            str(file_path),
            file_type
        )

        if extracted_text.strip():
            print("\nText extracted successfully!")
            print("\nExtracted text preview:\n")
            print(extracted_text[:3000])
            print("\nTotal characters:", len(extracted_text))
        else:
            print("No text found in this document.")

    except ValueError as error:
        print("Extraction error:", error)

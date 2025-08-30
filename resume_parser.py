import fitz # from PyMuPDF

def extract_resume_text(uploaded_file):
    # 'stream' expects byte stream, and 'filetype' is 'pdf'
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text

from docx import Document

class DocumentReader():
    def __init__(self, document_path):
        self.document = Document(document_path)
        self.sentence_sequence = []
        self.sentences = ""

    def read(self):
        cnt_sources = 0
        for p_cnt, para in enumerate(self.document.paragraphs):
            texts = list(filter(None, para.text.split(".")))
            for text in texts:
                cnt_sources += 1
                self.sentence_sequence.append({"id": f"S{cnt_sources}", "text": text})
                self.sentences += f"{text} (S{cnt_sources})."

            cnt_sources += 1
            self.sentence_sequence.append({"id": f"S{cnt_sources}", "text": "\n"})
            self.sentences += "\n"

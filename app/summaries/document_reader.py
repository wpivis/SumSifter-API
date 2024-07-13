from docx import Document

class DocumentReader():
    def __init__(self, document_path):
        self.document_path = document_path
        self.document = Document(document_path)
        self.sentence_sequence = []
        self.sentences = ""
        self.markdown_content = ""

    def read(self):
        cnt_sources = 0
        for para in self.document.paragraphs:
            texts = list(filter(None, para.text.split(".")))
            for text in texts:
                cnt_sources += 1
                self.sentence_sequence.append({"id": f"S{cnt_sources}", "text": text.strip()})
                self.sentences += f"{text.strip()} (S{cnt_sources})."
            self.sentences += "\n"

    def convert_to_markdown(self):
        doc = Document(self.document_path)
        markdown_lines = []

        for para in doc.paragraphs:
            if para.style.name == 'Title':
                markdown_lines.append(f"# {para.text}")
            elif para.style.name.startswith('Heading'):
                level = para.style.name.split()[-1]  # Assuming styles are like 'Heading 1', 'Heading 2', etc.
                markdown_lines.append(f"{'#' * int(level)} {para.text}")
            else:
                markdown_lines.append(para.text)
            markdown_lines.append('')

        self.markdown_content = "\n".join(markdown_lines)
        return self.markdown_content

    def save_markdown(self, output_path):
        markdown_content = self.convert_to_markdown()
        with open(output_path, 'w') as file:
            file.write(markdown_content)

    def parse_markdown(self):
        lines = self.markdown_content.split('\n')
        sentence_sequence = []
        cnt_sources = 0

        for line in lines:
            line = line.strip()
            if line:
                cnt_sources += 1
                sentence_sequence.append({"id": f"S{cnt_sources}", "text": line})

        return sentence_sequence
from docx import Document


class DocumentReader:
    def __init__(self, document_path):
        self.document_path = document_path
        self.document = Document(document_path)
        self.sentence_sequence = []
        self.sentences = ""
        self.markdown_content = ""

    def convert_to_markdown(self):
        markdown_lines = {}
        sentence_sequence = []

        idx = 0
        prev_element = None
        for para in self.document.paragraphs:
            if para.text.strip() == "":
                continue
            if para.style.name == "Title":
                prev_element = "title"
                idx += 1
                markdown_lines[str(idx)] = f"# {para.text}"
                sentence_sequence.append(
                    {"id": f"{idx}", "text": para.text, "sources": []}
                )
            elif para.style.name.startswith("Heading"):
                prev_element = "heading"
                idx += 1
                level = para.style.name.split()[
                    -1
                ]  # Assuming styles are like 'Heading 1', 'Heading 2', etc.
                markdown_lines[str(idx)] = f"{'#' * int(level)} {para.text}"
                sentence_sequence.append(
                    {"id": f"{idx}", "text": markdown_lines[str(idx)], "sources": []}
                )
            else:
                prev_element = "paragraph"
                for text in para.text.split("."):
                    idx += 1
                    markdown_lines[str(idx)] = text.strip()
                    if len(markdown_lines[str(idx)]) > 0:
                        markdown_lines[str(idx)] = f"{markdown_lines[str(idx)]}."
                    sentence_sequence.append(
                        {
                            "id": f"{idx}",
                            "text": markdown_lines[str(idx)],
                            "sources": [],
                        }
                    )
            if prev_element == "paragraph":
                idx += 1
                markdown_lines[idx] = ""
                sentence_sequence.append({"id": str(idx), "text": "\n", "sources": []})

        self.sentence_sequence = sentence_sequence
        self.markdown_content = markdown_lines
        # return self.markdown_content
        return self.sentence_sequence

from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkingService:
  def __init__(self, text: str):
    self.text = text

  def chunk_text(self):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_text(self.text)
    return chunks, "Text chunked successfully"
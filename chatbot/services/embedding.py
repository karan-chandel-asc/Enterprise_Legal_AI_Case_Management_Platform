import os
from dotenv import load_dotenv

import cohere

load_dotenv()


class EmbeddingService:

    def __init__(self):
        self.co = cohere.ClientV2(
            api_key=os.getenv("COHERE_API_KEY")
        )

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document chunks (used when indexing)."""
        response = self.co.embed(
            model="embed-english-v3.0",
            input_type="search_document",
            texts=texts,
            embedding_types=["float"]
        )

        return response.embeddings.float

    def similarity(self, text1: str, text2: str):
        # Imported lazily: this is the only place scikit-learn is needed,
        # and it shouldn't be a hard dependency for the indexing pipeline.
        from sklearn.metrics.pairwise import cosine_similarity

        embeddings = self.get_embeddings([text1, text2])

        score = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        return score

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query. Cohere uses a different input_type
        for queries vs documents, so this cannot reuse get_embeddings()."""
        response = self.co.embed(
            model="embed-english-v3.0",
            input_type="search_query",
            texts=[text],
            embedding_types=["float"],
        )
        return response.embeddings.float[0]
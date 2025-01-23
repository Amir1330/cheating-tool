import os
import ollama
import chromadb
from sentence_transformers import SentenceTransformer

class RAGSystem:
    def __init__(self, data_dir='data', model='granite3.1-moe:1b'):
        # Initialize embedding model
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize vector database
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="document_collection")

        # Initialize Ollama client
        self.ollama_client = ollama.Client()
        self.model = model

        # Process documents
        self.data_dir = data_dir
        self.load_documents()

    def load_documents(self):
        """Load and embed documents from data directory."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            return

        for filename in os.listdir(self.data_dir):
            filepath = os.path.join(self.data_dir, filename)
            if os.path.isfile(filepath) and filename.endswith(('.txt', '.md', '.py')):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.add_document(filename, content)

    def add_document(self, filename, content, chunk_size=500):
        """Chunk and embed documents."""
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

        for i, chunk in enumerate(chunks):
            embedding = self.embed_model.encode(chunk).tolist()
            doc_id = f"{filename}_chunk_{i}"

            self.collection.add(
                embeddings=embedding,
                documents=[chunk],
                ids=[doc_id]
            )

    def retrieve_context(self, query, top_k=3):
        """Retrieve most relevant document chunks."""
        query_embedding = self.embed_model.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )

        return results['documents'][0]

    def generate_response(self, query):
        """Generate response using retrieved context."""
        context = self.retrieve_context(query)

        prompt = f"Context:\n{' '.join(context)}\n\nQuery: {query}\n\nResponse:"

        response = self.ollama_client.generate(
            model=self.model,
            prompt=prompt,
            stream=False
        )

        return response['response']

    def add_new_document(self, filename, content):
        """Add a new document to the RAG system."""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.add_document(filename, content)

# Example usage
if __name__ == "__main__":
    rag = RAGSystem()

    # Example query
    query = "Explain Python list comprehensions"
    response = rag.generate_response(query)
    print(response)

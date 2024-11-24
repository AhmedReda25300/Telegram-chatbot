
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import re

class UserVectorDB:
    def __init__(self):
        # Use a multilingual model to support both Arabic and English
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.user_indices = {}
        self.user_texts = {}
        self.user_document_types = {}

    def add_texts(self, user_id, texts, document_type):
        if user_id not in self.user_texts:
            self.user_texts[user_id] = []
            self.user_indices[user_id] = None

        self.user_texts[user_id].extend(texts)
        self.user_document_types[user_id] = document_type
        embeddings = self.model.encode(texts)
        
        if self.user_indices[user_id] is None:
            self.user_indices[user_id] = faiss.IndexFlatL2(embeddings.shape[1])
        
        self.user_indices[user_id].add(embeddings.astype('float32'))

    def search(self, user_id, query, k=3):
        if user_id not in self.user_indices:
            return []
        
        query_vector = self.model.encode([query])
        distances, indices = self.user_indices[user_id].search(query_vector.astype('float32'), k)
        return [self.user_texts[user_id][i] for i in indices[0]]

    def clear(self, user_id):
        if user_id in self.user_indices:
            del self.user_indices[user_id]
        if user_id in self.user_texts:
            del self.user_texts[user_id]
        if user_id in self.user_document_types:
            del self.user_document_types[user_id]

    def get_full_text(self, user_id):
        return " ".join(self.user_texts.get(user_id, []))
    
    def get_chunks(self, user_id):
        return self.user_texts.get(user_id, [])

    def get_document_type(self, user_id):
        return self.user_document_types.get(user_id)

vector_db = UserVectorDB()

def preprocess_text(text):
    # Remove problematic characters except Arabic and English letters
    text = re.sub(r'[^\w\s\u0600-\u06FF]+', ' ', text)  # Preserve Arabic characters
    text = text.replace("\n", " ").strip()  # Replace newlines and strip extra spaces
    return text

def chunk_text(text, chunk_size=22000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def add_document_to_db(text, document_type, user_id):
    clean_text = preprocess_text(text)  # Preprocess the text for encoding issues
    chunks = chunk_text(clean_text)
    vector_db.add_texts(user_id, chunks, document_type)

def get_relevant_chunks(query, user_id, k=3):
    query = preprocess_text(query)  # Preprocess the query as well
    return vector_db.search(user_id, query, k)

def clear_vector_db(user_id):
    vector_db.clear(user_id)

def get_full_text(user_id):
    return vector_db.get_full_text(user_id)

def get_chunks(user_id):
    return vector_db.get_chunks(user_id)

def get_document_type(user_id):
    return vector_db.get_document_type(user_id)
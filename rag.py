import json
import chromadb
from sentence_transformers import SentenceTransformer
import ollama
import os

class EnhancedRAG:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("dav_knowledge")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm_model = "llama3.2:1b"  # Free lightweight model
        self.load_knowledge_base()
        self.load_manual_data()
    
    def load_knowledge_base(self):
        try:
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
            
            if knowledge_base and self.collection.count() == 0:
                self._add_documents_to_collection(knowledge_base, "scraped")
                print(f"Loaded {len(knowledge_base)} scraped documents into ChromaDB")
        except FileNotFoundError:
            print("Knowledge base not found. Run scraper first.")
    
    def load_manual_data(self):
        """Load manually added data"""
        try:
            with open('manual_data.json', 'r', encoding='utf-8') as f:
                manual_data = json.load(f)
            
            if manual_data:
                self._add_documents_to_collection(manual_data, "manual")
                print(f"Loaded {len(manual_data)} manual entries into ChromaDB")
        except FileNotFoundError:
            print("No manual data found.")
    
    def _add_documents_to_collection(self, data, source_type):
        """Add documents to ChromaDB collection"""
        documents = []
        metadatas = []
        ids = []
        
        for i, item in enumerate(data):
            documents.append(item['content'])
            metadatas.append({
                'url': item.get('url', 'manual_entry'),
                'title': item.get('title', ''),
                'category': item.get('category', 'general'),
                'source': source_type
            })
            ids.append(f"{source_type}_{i}_{item.get('id', i)}")
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def add_manual_data(self, entry):
        """Add single manual entry to collection"""
        self.collection.add(
            documents=[entry['content']],
            metadatas=[{
                'url': entry['url'],
                'title': entry['title'],
                'category': entry['category'],
                'source': 'manual'
            }],
            ids=[f"manual_{entry['id']}"]
        )
    
    def search(self, query, top_k=5):
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results['documents'][0]:
                return []
            
            search_results = []
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                search_results.append({
                    'content': doc,
                    'url': metadata['url'],
                    'title': metadata['title'],
                    'category': metadata.get('category', 'general'),
                    'source': metadata.get('source', 'scraped')
                })
            
            return search_results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def generate_response(self, query):
        # Search for relevant content
        results = self.search(query)
        
        if not results:
            return "I don't have information about that. Please ask about DAV Koyla Nagar school admissions, timings, fees, events, or contact our staff for more details."
        
        # Prepare context for LLM with source information
        context_parts = []
        for result in results:
            source_info = f"[{result['source'].title()} - {result['category']}]"
            context_parts.append(f"{source_info} {result['content'][:300]}")
        
        context = "\n".join(context_parts)
        
        # Enhanced prompt with source awareness
        prompt = f"""You are DAVGPT, an AI assistant for DAV Koyla Nagar school. Answer the user's question based only on the provided context. Be helpful, concise, and include relevant links when available.

Context from school database:
{context}

Question: {query}

Instructions:
- Provide accurate information based on the context
- Include website links when available
- If asking about notices, events, or recent updates, mention checking the school website
- Be friendly and helpful
- Keep responses concise but informative

Answer:"""
        
        try:
            response = ollama.generate(model=self.llm_model, prompt=prompt)
            
            # Add relevant links to response
            links = [r['url'] for r in results if r['url'] != 'manual_entry']
            if links:
                response_text = response['response']
                unique_links = list(set(links[:2]))  # Max 2 unique links
                link_text = "\n\nFor more details: " + " | ".join(unique_links)
                return response_text + link_text
            
            return response['response']
        except Exception as e:
            # Fallback to simple response if Ollama fails
            fallback = f"Based on our records: {results[0]['content'][:200]}..."
            if results[0]['url'] != 'manual_entry':
                fallback += f" For more details, visit {results[0]['url']}"
            return fallback
    
    def refresh_knowledge_base(self):
        """Clear and reload knowledge base"""
        try:
            self.client.delete_collection("dav_knowledge")
            self.collection = self.client.get_or_create_collection("dav_knowledge")
            self.load_knowledge_base()
            self.load_manual_data()
            return True
        except Exception as e:
            print(f"Error refreshing knowledge base: {e}")
            return False

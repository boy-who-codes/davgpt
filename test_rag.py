from rag import SimpleRAG

# Test the RAG system
rag = SimpleRAG()

# Test queries
test_queries = [
    "What are the school achievements?",
    "Tell me about admissions",
    "What events are happening?",
    "School contact information",
    "What is the fee structure?"
]

print("Testing DAVGPT RAG System")
print("=" * 50)

for query in test_queries:
    print(f"\nQuery: {query}")
    response = rag.generate_response(query)
    print(f"Response: {response[:200]}...")
    print("-" * 50)

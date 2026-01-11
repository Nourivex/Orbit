"""Quick test for Ollama library response structure"""
import ollama

try:
    response = ollama.list()
    print("Ollama response type:", type(response))
    print("Response:", response)
    
    if hasattr(response, '__dict__'):
        print("\nDict:", response.__dict__)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

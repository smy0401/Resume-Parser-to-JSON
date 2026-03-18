#  Llama 3.1:8B Setup & Usage

##  Installation
1. Install **Ollama** from [https://ollama.ai/download](https://ollama.ai/download)  
2. Verify installation:  
   ```bash
   ollama --version
   ```
3. Pull the Llama 3.1 8B model:  
   ```bash
   ollama pull llama3.1:8b
   ```

---

##  Run Commands
Run the model directly in terminal:
```bash
ollama run llama3.1:8b "Hello, summarize this text!"
```

Check installed models:
```bash
ollama list
```

---

##  Python Client
Install the Ollama Python package:
```bash
pip install ollama
```

Example usage:
```python
import ollama

response = ollama.chat(model="llama3.1:8b", messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Summarize this CV: Name: Ali Khan, Email: ali@example.com"}
])

print(response['message']['content'])
```

Run:
```bash
python test_llama.py
```

---

##  Environment Variables
Create a `.env` file at the project root if needed. Example:

```
LLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=127.0.0.1:11434
```

By default, Ollama runs locally on port `11434`.

---

##  Project Integration
- File: `src/models/llama_integration.py` (to be added)  
- This will expose helper functions like `extract_cv_data(text)` that call the Llama model via the Python client.

---



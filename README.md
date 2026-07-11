# 🚀 Advanced PDF AI Chatbot

An intelligent **Retrieval-Augmented Generation (RAG)** chatbot that allows users to upload PDF documents, ask natural language questions, and receive context-aware answers powered by Large Language Models (LLMs).

The application combines **Groq LLMs**, **Sentence Transformers**, **Supabase Cloud**, and **Streamlit** to provide fast, accurate, and scalable document-based question answering.

---

## 📖 Overview

The Advanced PDF AI Chatbot enables users to:

- 📄 Upload one or multiple PDF documents
- 🧠 Automatically extract and process document text
- 🔍 Generate semantic embeddings
- ☁️ Store PDFs and embeddings in Supabase Cloud
- 💬 Ask questions in natural language
- 🤖 Receive AI-generated answers grounded in uploaded documents
- ⚡ Deliver real-time responses using Groq's high-speed inference

Unlike traditional chatbots, this system understands the content of uploaded documents and generates responses based on document context rather than relying solely on the language model's knowledge.

---

# ✨ Features

- 📄 PDF Upload and Management
- 🧠 Automatic Text Extraction
- ✂️ Intelligent Text Chunking
- 🔎 Semantic Search using Sentence Transformers
- 🤖 Context-Aware AI Responses
- ☁️ Cloud Storage with Supabase
- ⚡ Ultra-fast LLM Inference using Groq
- 🎨 Clean Streamlit User Interface
- 🔐 Secure API Key Management using Environment Variables

---

# 🏗️ System Architecture

```
                User
                  │
                  ▼
          Streamlit Interface
                  │
        Upload PDF / Ask Question
                  │
                  ▼
        PDF Text Extraction (PyPDF)
                  │
                  ▼
          Text Chunk Generation
                  │
                  ▼
 Sentence Transformer Embeddings
                  │
                  ▼
        Supabase Vector Storage
                  │
                  ▼
     Retrieve Relevant Chunks (RAG)
                  │
                  ▼
            Groq Large Language Model
                  │
                  ▼
         AI Generated Answer
                  │
                  ▼
                User
```

---

# 🛠️ Technologies Used

## Programming Language

- Python

## Frontend

- Streamlit

## Large Language Model

- Groq
- Llama 3

## NLP

- Sentence Transformers

## PDF Processing

- PyPDF

## Cloud Database

- Supabase

## Environment Management

- python-dotenv

## Vector Embeddings

- SentenceTransformer

---

# 📂 Project Structure

```
Advanced-PDF-AI-Chatbot/
│
├── app.py
├── .env
├── requirements.txt
├── README.md
├── .gitignore
│
├── uploaded_pdfs/
│
├── utils/
│
├── assets/
│
└── screenshots/
```

---

# ⚙️ Installation

## 1 Clone the Repository

```bash
git clone https://github.com/yourusername/Advanced-PDF-AI-Chatbot.git

cd Advanced-PDF-AI-Chatbot
```

---

## 2 Create a Virtual Environment

Windows

```bash
python -m venv venv

venv\Scripts\activate
```

Mac/Linux

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4 Configure Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY

SUPABASE_URL=YOUR_SUPABASE_URL

SUPABASE_KEY=YOUR_SUPABASE_KEY
```

---

## 5 Run the Application

```bash
streamlit run app.py
```

---

# 🔄 Workflow

1. User uploads one or multiple PDF files.
2. PDF text is extracted automatically.
3. Text is split into meaningful chunks.
4. Sentence Transformers generate embeddings.
5. Embeddings and document metadata are stored in Supabase.
6. User asks a question.
7. Relevant document chunks are retrieved.
8. Retrieved context is sent to the Groq LLM.
9. The chatbot generates a context-aware response.

---

# 📊 Core Components

### PDF Processing

- PyPDF
- Text Extraction

### Embedding Model

- Sentence Transformers

### Retrieval

- Semantic Similarity Search

### Large Language Model

- Groq
- Llama 3

### Database

- Supabase

### User Interface

- Streamlit

---

# 🚀 Future Improvements

- ✅ Conversation Memory
- ✅ Multi-document Search
- ✅ Vector Database Optimization
- ✅ User Authentication
- ✅ Chat History
- ✅ Streaming Responses
- ✅ Image Extraction from PDFs
- ✅ OCR Support for Scanned PDFs
- ✅ Multi-language Support
- ✅ Voice-based Interaction

---

# 📈 Skills Demonstrated

This project demonstrates practical experience with:

- Retrieval-Augmented Generation (RAG)
- Large Language Models (LLMs)
- Natural Language Processing (NLP)
- Semantic Search
- Vector Embeddings
- Cloud Database Integration
- Streamlit Application Development
- API Integration
- Prompt Engineering
- Python Development

---

# 🎯 Learning Outcomes

Through this project, I gained hands-on experience in:

- Building production-style AI applications
- Working with Large Language Models
- Implementing Retrieval-Augmented Generation pipelines
- Cloud storage integration with Supabase
- Deploying interactive AI applications with Streamlit
- Managing vector embeddings for semantic search
- Integrating external AI APIs

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

Feel free to fork the repository and submit a pull request.

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Vidu Thilakarathne**

Data Science Undergraduate

- Python
- Machine Learning
- Data Science
- SQL
- Power BI
- Databricks
- PySpark
- FastAPI
- AI Engineering

---

⭐ If you found this project useful, consider giving it a star on GitHub!

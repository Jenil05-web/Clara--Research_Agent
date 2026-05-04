<div align="center">

# 🧠 Clara: Your Personal AI Research Assistant

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*An intelligent, context-aware AI agent that dynamically routes queries across local PDFs, arXiv, and Wikipedia using Advanced RAG.*

[View Live App](https://clara--researchagent-hgcz5arktiapojprrhdme2.streamlit.app/)  

</div>

---

## 🚀 About the Project

Clara is a state-of-the-art AI research assistant built to streamline information gathering. Instead of manually searching the web or reading through massive documents, you can upload your own PDFs or ask open-ended questions. 

Clara automatically evaluates the intent of your query and dynamically routes it to the most relevant knowledge source, ensuring answers are highly accurate, grounded, and free of hallucinations.

---

## ✨ Key Features

- **Intelligent Query Routing:** Uses LangGraph agents to automatically decide if a query should search a local PDF, fetch an academic paper from arXiv, or pull general knowledge from Wikipedia.
- **Local Document Chat:** Upload any PDF to chunk, embed, and index the document using FAISS for highly accurate semantic search.
- **Advanced RAG Pipeline:** Ensures the LLM only answers based on the retrieved context.
- **Interactive UI:** A clean, responsive chat and upload interface built with Streamlit.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Orchestration & Agents:** LangChain, LangGraph
- **Vector Database:** FAISS (Facebook AI Similarity Search)
- **External APIs:** Wikipedia API, arXiv API
- **Models:**  OpenAI gpt-4o-mini / OpenAI Embedding models

---

## 🧠 Architecture

1. **Document Ingestion:** Uploaded PDFs are processed, split into chunks, converted into dense vectors, and stored in a local FAISS index.
2. **Stateful Routing:** The user's prompt enters a directed graph. The router agent analyzes the intent:
   - *Local Context* ➡️ Routes to **FAISS VectorStore**
   - *Scientific/Academic* ➡️ Routes to **arXiv Search**
   - *General Factual* ➡️ Routes to **Wikipedia**
3. **Generation:** The retrieved context and original prompt are synthesized by the LLM to stream a clean, accurate response to the user.

---

## 💻 Getting Started

Follow these steps to set up Clara on your local machine.

### Prerequisites
Make sure you have Python installed (3.9 or higher is recommended) and Git.

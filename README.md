
# LegalIYRI8 – Intelligent Legal Reasoning Interface

LegalIYRI8 is an intelligent legal analysis system designed to process legal cases and documents across different jurisdictions (India, Canada, UK). It uses a **multi-agent AI architecture** built on **CrewAI**, enabling contextual legal understanding, reasoning, and summarization. The system supports YAML-configured legal rules and integrates retrieval-augmented generation (RAG) for legal document research.

## 🌍 Features

- 📜 **Multi-Jurisdictional Support** – Analyze legal scenarios in India, Canada, and the UK with country-specific YAML legal files.
- 🧠 **Multi-Agent Reasoning** – Agent-based system for intake validation, fact extraction, legal research, analysis, and summarization.
- 🔍 **Retrieval-Augmented Generation (RAG)** – Retrieve relevant laws from vectorized legal documents.
- 🤖 **Natural Language Input** – Accepts user-submitted legal descriptions or case details (text or image).
- 📄 **PDF/Image Support** – Extracts facts from scanned legal documents.
- 📊 **Summarized Output** – Generates concise legal summaries with recommendations and legality scores.

## 🗂️ Project Structure
nivedivasu23-legaliri8/
├── main.py                         # Entry point for the app
├── config.py                       # App and API configuration
├── crew\_setup.py                   # CrewAI agent and task setup
├── utils.py                        # Utility functions
├── requirements.txt                # Required Python packages
├── README.md                       # This file

├── legal\_configs/                  # Country-specific legal YAML rules
│   ├── canada/
│   │   └── canada\_rent\_control.yaml
│   ├── india/
│   │   └── civil\_laws.yaml
│   └── united\_kingdom/
│       └── united\_kingdom\_unfair\_dismissal.yaml

├── rag/                            # Retrieval system
│   ├── retriever.py
│   ├── vector\_store.py
│   └── legal\_docs/
│       └── india/

├── tasks/                          # Modular legal task agents
│   ├── analysis\_task.py
│   ├── drafting\_task.py
│   ├── research\_task.py
│   ├── summary\_task.py

├── example/                        # Example documents
│   └── image/

├── India\_validation.md             # Validation output
├── India\_analysis.md              # Analytical output
├── India\_summary.md               # Summary output
├── India\_document.md              # Document text
├── India\_research.md              # Legal research output

````

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/nivedivasu23/nivedivasu23-legaliri8.git
cd nivedivasu23-legaliri8
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python main.py
```

## 🛠️ Configuration

Edit `config.py` to configure:

* Language model (OpenAI, Groq, Gemini)
* File paths and YAML references
* Search & indexing options

## ✅ Supported Countries

* 🇮🇳 India
* 🇨🇦 Canada
* 🇬🇧 United Kingdom

To add support for another country:

* Create a new folder under `legal_configs/`
* Add a new `.yaml` file with relevant legal rules

## 🧠 Tech Stack

* **CrewAI** – Agent-based orchestration
* **OpenAI / Groq / Gemini** – LLM integration
* **LangChain / Chroma** – Vector-based search
* **PyMuPDF / Tesseract** – OCR for scanned documents
* **YAML** – Configurable legal knowledge base


## ✍️ Author

**Niveditha S** – AI and ML Research Engineer | Legal AI | Reasoning Systems





# 💹 MarketMate — Financial Chatbot

**MarketMate** is a FastAPI-based chatbot application focused solely on financial market-related queries. It provides real-time interactions via a web interface and responds to queries using mocked APIs that simulate financial news and quarterly results data.

---

## 🚀 Features

- 🎯 **Domain-Specific Scope**: Only handles financial queries—market news, stock performance, earnings reports.
- 🔁 **Multi-Chat Session Support**: Maintains and switches between multiple conversations using session tracking.
- 📊 **Tiered Rate Limiting**: Enforces rate limits (RPM, RPD, TPM, TPD) based on the user's subscription tier.
- 🔗 **Mock API Integration**: Simulates realistic financial data via mocked `get_financial_news` and `get_quarterly_results` APIs.
- 🎨 **Web UI**: Clean, interactive HTML interface with persistent chat history.

---

## 🧠 Design Approach

- **Framework**: Built using FastAPI for asynchronous performance and simplicity.
- **Templating**: Jinja2 is used to render a dynamic frontend in `site.html`.
- **Sessions**: Managed via `SessionMiddleware`, enabling users to maintain context across messages and chats.
- **Mock API Calls**: Simulated financial data responses help isolate UI/backend logic from external dependencies during early development or offline usage.
- **Token Estimation**: Word count approximates token usage to enforce usage caps.

---

## ⚙️ Key Design Decisions

- **Domain Restriction**: All logic enforces financial-only queries to keep scope narrow and consistent.
- **Session Storage**: Session data is stored server-side using cookies for simplicity—sufficient for single-user/local testing.
- **Rate Limiting Logic**: Built-in checks ensure users don't exceed tier-based limits, protecting backend resource usage.
- **Company Name Extraction**: Basic keyword matching (`extract_company_name`) is used as a placeholder for Named Entity Recognition.

---

## 📦 Folder Structure
```bash
.
├── main.py              # Core FastAPI app with endpoints
├── mock_apis.py         # Mock financial API responses
├── templates/
│   └── site.html        # Web interface for interacting with the chatbot
├── requirements.txt     # Python dependencies (not included but recommended)
└── README.md            # This file
```
## ✅ Assumptions Made

- Only three companies (Tata, Infosys, Reliance) are recognized in the mock extract_company_name function.
- Tier information (like Free, Tier-1, etc.) and user IDs are assumed to be stored in the session.
- Token calculation uses a simple len(text.split()), which may not align exactly with OpenAI tokenizers.


## 🔧 Potential Improvements

- **⚙️ Authentication System:** Add user login, persistent storage, and dynamic tier assignment.


- **📈 Real API Integration:** Replace mocks with live financial APIs (e.g., Yahoo Finance, Alpha Vantage).


- **🧠 NER for Company Extraction:** Integrate spaCy or another NLP tool to accurately extract company names from free-text.


- **📚 Database Integration:** Store conversations in a database (e.g., SQLite, PostgreSQL) instead of session memory.


- **🌐 Model Flexibility:** Add dynamic provider support (e.g., Anthropic, Mistral) with switchable model keys.


## 🏁 Getting Started

Clone the repository:


1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/marketmate.git
   cd marketmate
   pip install -r requirements.txt
   
2. Run the app:
```bash
uvicorn main2:app --reload
Open in browser: http://127.0.0.1:8000

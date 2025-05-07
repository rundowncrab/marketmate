from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from copy import deepcopy
from mock_apis import get_financial_news, get_quarterly_results
from datetime import datetime, timedelta
from collections import defaultdict
import time

# Setup
load_dotenv()
app = FastAPI()

# Added session middleware to the app. This stores user session information (e.g., active chat history)
app.add_middleware(SessionMiddleware, secret_key='super-secret-key')

# Set up Jinja2 templating engine for rendering HTML responses
templates = Jinja2Templates(directory="templates")

# Track usage metrics by user and model (to enforce rate limits)
# Each user's metrics includes:
# - rpm: request timestamps in last minute
# - rpd: request timestamps in last 24 hours
# - tpm: tokens used in last minute
# - tpd: tokens used in last 24 hours
usage_tracker = defaultdict(lambda: defaultdict(lambda: {"rpm": [], "rpd": [], "tpm": 0, "tpd": 0}))

#System_prompt
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "You are a helpful financial assistant. Only respond to questions about financial data, stock performance, market news, or company reports. Do not answer unrelated questions."
}

#Setting up the rate limits as per the example
tier_limits = {
    ("Free", "OpenAI", "gpt-4o"): {"rpm": 3, "rpd": 200, "tpm": 40000, "tpd": 1000000},
    ("Tier-1", "OpenAI", "gpt-4o"): {"rpm": 500, "rpd": 10000, "tpm": 200000, "tpd": 5000000},
    ("Tier-2", "OpenAI", "gpt-4o"): {"rpm": 5000, "rpd": 100000, "tpm": 2000000, "tpd": 50000000},
    ("Tier-3", "OpenAI", "gpt-4o"): {"rpm": 50000, "rpd": 1000000, "tpm": 20000000, "tpd": 500000000}
}


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    #For tracking chat history
    if "chat_history" not in request.session:
        request.session["chat_history"] = [SYSTEM_MESSAGE] #Default system message to start the chat
    if "previous_chats" not in request.session:
        request.session["previous_chats"] = [] # List to store previous chats
    if "active_index" not in request.session:
        request.session["active_index"] = None# Index for the current active chat
    # Render the 'site.html' template with the current session's data
    return templates.TemplateResponse("site.html", {"request": request})

#after clicking the new chat button 
@app.post("/new-chat")
async def new_chat(request: Request):
    previous_chats = request.session.get("previous_chats", [])
    current_chat = request.session.get("chat_history", [])

   # If there is an ongoing chat, save it to previous chats
    if current_chat and current_chat != [SYSTEM_MESSAGE]:
        active_index = request.session.get("active_index")
        if active_index is not None and 0 <= active_index < len(previous_chats):
            previous_chats[active_index] = current_chat  # Replace the active chat
        elif current_chat not in previous_chats:
            previous_chats.append(current_chat)  # Add new chat to history

    # Start a fresh new chat
    new_chat = [SYSTEM_MESSAGE]
    previous_chats.append(new_chat)
    request.session["chat_history"] = new_chat # Set the new chat as the active one
    request.session["previous_chats"] = previous_chats  # Update the previous chats list
    request.session["active_index"] = len(previous_chats) - 1  # Update active chat index

    return JSONResponse({"message": "New chat started."})



@app.post("/send-message")
async def send_message(request: Request, text: str = Form(...), model: str = Form(...)):
    # --- Tiered Rate Limiting Snippet START ---
    user_id = request.session.get("user_id", "default_user")
    tier = request.session.get("tier", "Free")
    provider = "OpenAI"
    key = (tier, provider, model)

    now = time.time()
    usage = usage_tracker[user_id][key]
    limits = tier_limits.get(key)

    if not limits:
        raise HTTPException(
            status_code=400,
            detail=f"Rate limits not defined for: Tier={tier}, Provider={provider}, Model={model}. Please check your configuration."
        )
    required_keys = ["rpm", "rpd", "tpm", "tpd"]
    for k in required_keys:
        if k not in limits:
            raise HTTPException(
                status_code=500,
                detail=f"Missing rate limit key '{k}' in tier_limits for {key}."
            )

    # Clean timestamps older than 1 min (rpm) and 1 day (rpd)
    usage["rpm"] = [t for t in usage["rpm"] if now - t < 60]
    usage["rpd"] = [t for t in usage["rpd"] if now - t < 86400]

    # Token count estimate
    token_count = len(text.split())

     # Enforce rate limits
    if len(usage["rpm"]) >= limits["rpm"]:
        raise HTTPException(status_code=429, detail="Rate limit exceeded: Too many requests per minute. Please wait and try again.")
    if len(usage["rpd"]) >= limits["rpd"]:
        raise HTTPException(status_code=429, detail="Daily request limit reached. Upgrade your plan for more access.")
    if usage["tpm"] + token_count > limits["tpm"]:
        raise HTTPException(status_code=429, detail="Token per minute limit exceeded. Please wait a moment.")
    if usage["tpd"] + token_count > limits["tpd"]:
        raise HTTPException(status_code=429, detail="Daily token limit reached. Upgrade your plan for more usage.")

    # Record usage
    usage["rpm"].append(now)
    usage["rpd"].append(now)
    usage["tpm"] += token_count
    usage["tpd"] += token_count
    # --- Tiered Rate Limiting Snippet END ---

    chat_history = request.session.get("chat_history", [SYSTEM_MESSAGE])
    chat_history.append({"role": "user", "content": text})

    lower_text = text.lower()
    response = "I'm sorry, I can only help with financial market-related questions."
    company_name = extract_company_name(text)
    current_date = datetime.now().strftime("%Y-%m-%d")
    quarter = "Q4 FY24"  # For now, use a static example

     # Branch: Handle financial news request
    if "news" in lower_text or "financial news" in lower_text or "latest update" in lower_text:
        if company_name != "Unknown Company":
            response_data = get_financial_news({
                "company_name": company_name,
                "date": current_date
            })
            if response_data.get("news"):
                response = f"Latest Financial News for {company_name}:\n"
                for article in response_data["news"]:
                    response += f"- {article['headline']} ({article['date']} via {article['source']}): {article['description']}\n"
            else:
                response = f"No recent financial news found for {company_name}."

    # Branch: Handle quarterly result request
    elif any(kw in lower_text for kw in ["quarter", "results", "balance", "profit", "revenue", "transcript"]):
        if company_name != "Unknown Company":
            response_data = get_quarterly_results({
                "company_name": company_name,
                "quarter": quarter,
                "api_key": "demo"  # Placeholder
            })
            response = (
                f"Quarterly Financial Results for {response_data['company_name']} ({response_data['quarter']}):\n"
                f"- P/E Ratio: {response_data['valuation_ratios']['pe_ratio']}\n"
                f"- P/B Ratio: {response_data['valuation_ratios']['pb_ratio']}\n"
                f"- [Balance Sheet]({response_data['files']['balance_sheet_excel']})\n"
                f"- [Analyst Call Transcript]({response_data['files']['analyst_call_transcript_doc']})"
            )

    chat_history.append({"role": "assistant", "content": response})
    request.session["chat_history"] = chat_history

    # Sync current conversation to previous chats
    previous_chats = request.session.get("previous_chats", [])
    active_index = request.session.get("active_index")
    if active_index is not None and 0 <= active_index < len(previous_chats):
        previous_chats[active_index] = chat_history
        request.session["previous_chats"] = previous_chats

    return JSONResponse({"openai_response": chat_history[-1]["content"]})


#For switching up conversations i.e. going back to previous chats
@app.post("/switch-conversation")
async def switch_conversation(request: Request, conversation_index: int = Form(...)):
    previous_chats = request.session.get("previous_chats", [])
    if 0 <= conversation_index < len(previous_chats):
        request.session["chat_history"] = deepcopy(previous_chats[conversation_index])
        request.session["active_index"] = conversation_index
        return JSONResponse({
            "message": "Switched successfully.",
            "chat_history": request.session["chat_history"]
        })

    raise HTTPException(status_code=404, detail="Conversation not found")



@app.get("/get-previous-chats")
async def get_previous_chats(request: Request):
    return JSONResponse({"previous_chats": request.session.get("previous_chats", [])})


def extract_company_name(text: str) -> str:
    # Dummy version — ideally use a proper NER or company list
    for company in ["Tata", "Infosys", "Reliance"]:
        if company.lower() in text.lower():
            return company
    return "Unknown Company"


#in order to delete the chats just go to {localhost}/reset 
@app.get("/reset")
async def reset_session(request: Request):
    request.session.clear()
    return {"message": "Session cleared"}

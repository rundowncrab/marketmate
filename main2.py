from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import openai
from typing import Optional

# Load environment variable
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Constants
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "You are a helpful financial assistant. Only respond to questions about financial data, stock performance, market news, or company reports. Do not answer unrelated questions."
}

TIER_LIMITS = {
    "free": {"RPM": 3, "RPD": 200, "TPM": 40000, "TPD": 1000000},
    "tier1": {"RPM": 500, "RPD": 10000, "TPM": 200000, "TPD": 5000000},
    "tier2": {"RPM": 5000, "RPD": 100000, "TPM": 2000000, "TPD": 50000000},
    "tier3": {"RPM": 50000, "RPD": 1000000, "TPM": 20000000, "TPD": 500000000}
}

# Setup FastAPI
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='super-secret-key')
templates = Jinja2Templates(directory="templates")

# LLM Response
async def get_openai_response(model: str, chat_history: list):
    return {"content": "hey how are you"}
    # try:
    #     response = openai.chat.completions.create(
    #         model=model,
    #         messages=chat_history
    #     )
    #     return {"content": response.choices[0].message.content}
    # except Exception as e:
    #     raise RuntimeError(f"Error with OpenAI API: {str(e)}")

# Serve index
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    if "chat_history" not in request.session:
        request.session["chat_history"] = [SYSTEM_MESSAGE]
    if "previous_chats" not in request.session:
        request.session["previous_chats"] = []
    return templates.TemplateResponse("site.html", {"request": request})

# New chat
@app.post("/new-chat")
async def new_chat(request: Request):
    chat_history = request.session.get("chat_history", [SYSTEM_MESSAGE])
    if "previous_chats" not in request.session:
        request.session["previous_chats"] = []
    request.session["previous_chats"].append(chat_history.copy())
    request.session["chat_history"] = [SYSTEM_MESSAGE]
    return JSONResponse({"message": "New chat started."})

# Send message
@app.post("/send-message")
async def send_message(request: Request, text: str = Form(...), model: str = Form(...)):
    try:
        chat_history = request.session.get("chat_history", [SYSTEM_MESSAGE])
        chat_history.append({"role": "user", "content": text})
        response = await get_openai_response(model, chat_history)
        ai_message = {"role": "assistant", "content": response["content"]}
        chat_history.append(ai_message)
        request.session["chat_history"] = chat_history
        return JSONResponse({"openai_response": response["content"]})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Switch conversation - Change to accept JSON payload
@app.post("/switch-conversation")
async def switch_conversation(request: Request, conversation_index: int = Form(...)):
    previous_chats = request.session.get("previous_chats", [])
    if 0 <= conversation_index < len(previous_chats):
        request.session["chat_history"] = previous_chats[conversation_index]
        return JSONResponse({"message": "Switched successfully.", "chat_history": previous_chats[conversation_index]})
    raise HTTPException(status_code=404, detail="Conversation not found")


# Get previous chats
@app.get("/get-previous-chats")
async def get_previous_chats(request: Request):
    previous_chats = request.session.get("previous_chats", [])
    return JSONResponse({"previous_chats": previous_chats})

import os
import json
import urllib.request
import urllib.error

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
You are the official Senior AI Customer Support Specialist for "Booking Adventures" (Semester 7 PBL Engineering Project).
You assist users like Bittu Jaiswal and travelers with warmth, professional accuracy, and deep platform knowledge.

Platform Knowledge Base:
1. Dynamic Pricing Engine:
   - Powered by a Scikit-Learn Gradient Boosting Regressor (R² ≈ 0.987, MAPE ≈ 5.3%).
   - Fares adjust in real-time based on Urgency (days to departure), Live Seasonality, Competitor Index, Occupancy Rate, Weekend surges, and Aviation Fuel index.
2. Payment Gateway:
   - Real Razorpay Gateway integration supporting UPI (GPay, PhonePe, Paytm, BHIM), Credit/Debit Cards, and NetBanking.
   - Generates authentic Razorpay reference IDs (e.g. pay_...).
3. Cancellation & Refunds:
   - Dynamic 85% instant refund policy for cancellations via Razorpay, tracked via refund IDs (e.g. rfnd_...).
4. Security & Auth:
   - Dual Authentication supporting Resend MFA OTP delivery and One-Click token-saving direct logins.
5. Key Routes:
   - Mumbai (BOM) to Brazil (GIG), Dubai (DXB), Tokyo (HND), London (LHR), Italy (FCO), New York (JFK), Paris (CDG), Switzerland (ZRH), Sydney (SYD), Singapore (SIN).

Tone: Courteous, helpful, intelligent, human-like, and concise (2-4 sentences or clear bullet points). If asked about technical architecture, proudly explain the ML model and FastAPI + SQLite backend.
"""

def get_active_gemini_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
    return api_key or GEMINI_API_KEY

def chat_with_gemini(message: str, history: list = None, user_context: dict = None) -> dict:
    """
    Sends message to Gemini 2.5 Flash API and returns assistant reply.
    """
    api_key = get_active_gemini_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    # Build contents with context
    contents = []

    # Insert system prompt as first turn or context
    system_text = SYSTEM_INSTRUCTION
    if user_context:
        system_text += f"\nCurrently assisting user: {user_context.get('name', 'Valued Customer')} (Email: {user_context.get('email', 'N/A')}, Mobile: {user_context.get('mobile', 'N/A')})."

    contents.append({
        "role": "user",
        "parts": [{"text": f"[SYSTEM INSTRUCTION - ACT AS SUPPORT SPECIALIST]\n{system_text}\n\nUser Question: {message}"}]
    })

    # If conversation history exists, we can pass recent turns
    if history and len(history) > 1:
        # Keep last 6 turns for context
        recent = history[-6:]
        formatted_history = []
        for h in recent:
            role = "user" if h.get("sender") == "user" else "model"
            formatted_history.append({"role": role, "parts": [{"text": h.get("text", "")}]})
        # Add current message at the end
        formatted_history.append({"role": "user", "parts": [{"text": message}]})
        payload = {
            "contents": formatted_history,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 600
            }
        }
    else:
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 600
            }
        }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        res_data = json.loads(resp.read().decode("utf-8"))
        reply_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        return {
            "success": True,
            "reply": reply_text.strip(),
            "model": GEMINI_MODEL
        }
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[GEMINI HTTP ERROR] {e.code}: {err_msg}")
        return {
            "success": False,
            "reply": "I apologize, but I am having a temporary connection issue with the Gemini service. Please ask again in a moment.",
            "error": str(err_msg)
        }
    except Exception as e:
        print(f"[GEMINI EXCEPTION] {e}")
        return {
            "success": False,
            "reply": "Our AI Support system is momentarily reconnecting. You can check flight statuses and booking details from the navigation menu.",
            "error": str(e)
        }

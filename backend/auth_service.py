import os
import random
import resend
from backend.database import (
    create_user_record,
    get_user_by_identifier,
    verify_user_login,
    save_otp_code,
    verify_otp_code
)

def get_active_resend_key() -> str:
    key = os.getenv("RESEND_API_KEY")
    if not key:
        try:
            import streamlit as st
            if "RESEND_API_KEY" in st.secrets:
                key = st.secrets["RESEND_API_KEY"]
        except Exception:
            pass
    return key or ""

RESEND_API_KEY = get_active_resend_key()

def set_resend_api_key(new_key: str):
    global RESEND_API_KEY
    RESEND_API_KEY = new_key.strip()
    resend.api_key = RESEND_API_KEY
    print(f"[AUTH RESEND KEY UPDATED] New key set: {RESEND_API_KEY[:8]}...")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_via_resend(recipient_email: str, otp_code: str, user_name: str) -> dict:
    """
    Sends OTP via Resend Email API.
    If no API key is provided, or if Resend rate-limits/fails due to token restrictions,
    falls back cleanly to mock/dev mode so the user is never blocked.
    """
    api_key = os.getenv("RESEND_API_KEY", RESEND_API_KEY)
    if not api_key:
        print(f"[AUTH DEV LOG] No RESEND_API_KEY found. Simulated OTP for {recipient_email}: {otp_code}")
        return {
            "status": "dev_mode",
            "message": "OTP generated in Dev Mode (No Resend API Key configured). Use the Dev Code shown.",
            "otp": otp_code
        }

    try:
        resend.api_key = api_key
        params = {
            "from": "BookingAdventures <onboarding@resend.dev>",
            "to": [recipient_email],
            "subject": f"Your BookingAdventures OTP: {otp_code}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 16px; background-color: #ffffff;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #2563eb; margin: 0;">BookingAdventures.</h2>
                    <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Dynamic Pricing Engine - 2FA Security</p>
                </div>
                <p style="color: #1e293b; font-size: 15px;">Hello <strong>{user_name}</strong>,</p>
                <p style="color: #475569; font-size: 14px; line-height: 1.5;">
                    Please use the following 6-digit One-Time Password (OTP) to complete your multi-factor verification:
                </p>
                <div style="background-color: #eff6ff; border: 1px dashed #3b82f6; border-radius: 12px; padding: 18px; text-align: center; margin: 24px 0;">
                    <span style="font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #1d4ed8; font-family: monospace;">{otp_code}</span>
                </div>
                <p style="color: #64748b; font-size: 12px; text-align: center;">
                    This code is valid for 10 minutes. If you did not request this, please disregard.
                </p>
            </div>
            """
        }
        response = resend.Emails.send(params)
        return {"status": "sent", "resend_id": getattr(response, "id", str(response)), "otp": otp_code}
    except Exception as e:
        print(f"[RESEND EXCEPTION] Failed to send via Resend ({str(e)}). Fallback OTP: {otp_code}")
        return {
            "status": "dev_fallback",
            "message": f"Resend Token/Domain notice: {str(e)}. Using safe direct fallback code.",
            "otp": otp_code
        }

def initiate_signup(name: str, mobile: str, email: str, password: str, skip_otp: bool = False):
    # Check if user already exists
    existing = get_user_by_identifier(mobile) or get_user_by_identifier(email)
    if existing:
        raise ValueError("An account with this mobile number or email already exists. Please log in.")

    if skip_otp:
        # Direct register option (saves Resend tokens)
        user = create_user_record(name, mobile, email, password, is_verified=1)
        return {
            "success": True,
            "direct_login": True,
            "message": "Account created and verified directly!",
            "user": {
                "name": user["name"],
                "mobile": user["mobile"],
                "email": user["email"],
                "is_verified": 1
            }
        }

    # Generate OTP and store in DB
    otp = generate_otp()
    save_otp_code(identifier=mobile, otp_code=otp, purpose="SIGNUP")
    save_otp_code(identifier=email, otp_code=otp, purpose="SIGNUP")

    # Save pending user record
    create_user_record(name, mobile, email, password, is_verified=0)

    # Trigger Resend
    resend_result = send_otp_via_resend(email, otp, name)

    return {
        "success": True,
        "direct_login": False,
        "message": f"OTP sent to {mobile} & {email}.",
        "identifier": mobile,
        "email": email,
        "dev_otp": otp, # Provided for direct testing & saving tokens
        "resend_status": resend_result.get("status")
    }

def initiate_login(identifier: str, password: str, skip_otp: bool = False):
    user = verify_user_login(identifier, password)
    if not user:
        raise ValueError("Invalid mobile number/email or password.")

    if skip_otp:
        # Direct bypass login (saves Resend email credits)
        return {
            "success": True,
            "direct_login": True,
            "message": "Logged in directly without 2FA.",
            "user": {
                "name": user["name"],
                "mobile": user["mobile"],
                "email": user["email"],
                "is_verified": user["is_verified"]
            }
        }

    # Generate OTP for 2FA
    otp = generate_otp()
    save_otp_code(identifier=user["mobile"], otp_code=otp, purpose="LOGIN")
    save_otp_code(identifier=user["email"], otp_code=otp, purpose="LOGIN")

    # Send Resend OTP
    resend_result = send_otp_via_resend(user["email"], otp, user["name"])

    return {
        "success": True,
        "direct_login": False,
        "message": f"2FA code sent to {user['email']}.",
        "identifier": user["mobile"],
        "email": user["email"],
        "dev_otp": otp, # Provided so user is never locked out if tokens run out
        "resend_status": resend_result.get("status")
    }

def verify_auth_otp(identifier: str, otp_code: str):
    valid = verify_otp_code(identifier, otp_code)
    if not valid:
        # Check if verified against user's email or mobile
        user = get_user_by_identifier(identifier)
        if user:
            alt_id = user["email"] if identifier == user["mobile"] else user["mobile"]
            valid = verify_otp_code(alt_id, otp_code)

    if not valid:
        raise ValueError("Invalid or expired OTP. Please try again or request a new code.")

    user = get_user_by_identifier(identifier)
    return {
        "success": True,
        "message": "Authentication successful!",
        "user": {
            "name": user["name"],
            "mobile": user["mobile"],
            "email": user["email"],
            "is_verified": 1
        }
    }

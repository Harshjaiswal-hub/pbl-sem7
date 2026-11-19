from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import random
import string

from backend.database import (
    init_db,
    get_flights_by_destination,
    get_flight_by_id,
    get_seats_for_flight,
    book_flight_seats,
    save_booking,
    get_user_bookings,
    cancel_booking_pnr,
    get_analytics_summary,
    log_pricing_event,
    get_all_users_list,
    get_user_by_identifier
)
from backend.ml_engine import pricing_engine
from backend.pricing_service import price_flights_dynamically
from backend.schemas import (
    SearchRequest,
    BookingCreateRequest,
    DynamicPricingSimulateRequest,
    SignUpRequest,
    LoginRequest,
    VerifyOtpRequest,
    ResendOtpRequest,
    CreatePaymentOrderRequest,
    VerifyPaymentSignatureRequest,
    SetPaymentCredentialsRequest,
    SetResendKeyRequest,
    ChatMessageRequest,
    ApplyCouponRequest,
    SetTavilyKeyRequest
)
from backend.gemini_service import chat_with_gemini
from backend.live_api_service import (
    fetch_live_currency_rates,
    fetch_live_airport_weather,
    fetch_tavily_live_market_fares,
    set_tavily_api_key,
    get_tavily_api_key,
    fetch_live_aviationstack_flights,
    apply_promo_offer,
    get_live_flight_telemetry,
    ACTIVE_OFFERS
)
from backend.auth_service import (
    initiate_signup,
    initiate_login,
    verify_auth_otp,
    generate_otp,
    save_otp_code,
    send_otp_via_resend,
    set_resend_api_key
)
from backend.razorpay_service import (
    get_razorpay_public_key,
    set_razorpay_credentials,
    create_order,
    verify_payment_signature,
    initiate_refund
)

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Booking Adventures - Dynamic Pricing Engine & Travel Platform",
    description="Full-stack AI/ML-driven airline yield management and multi-factor authentication platform.",
    version="2.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "Booking Adventures Dynamic Pricing Engine",
        "ml_model_loaded": pricing_engine.gbr_model is not None,
        "primary_algorithm": "Gradient Boosting Regressor (Scikit-Learn)",
        "auth_engine": "MFA via Resend + Direct Bypass",
        "version": "2.1.0"
    }

# ================= AUTHENTICATION ENDPOINTS =================
@app.post("/api/auth/signup")
def auth_signup(req: SignUpRequest):
    try:
        result = initiate_signup(
            name=req.name,
            mobile=req.mobile,
            email=req.email,
            password=req.password,
            skip_otp=req.skip_otp
        )
        return result


    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup error: {str(e)}")

@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    try:
        result = initiate_login(
            identifier=req.identifier,
            password=req.password,
            skip_otp=req.skip_otp
        )
        return result


    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/api/auth/verify-otp")
def auth_verify_otp(req: VerifyOtpRequest):
    try:
        result = verify_auth_otp(identifier=req.identifier, otp_code=req.otp_code)
        return result


    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")

@app.post("/api/auth/resend-otp")
def auth_resend_otp(req: ResendOtpRequest):
    user = get_user_by_identifier(req.identifier)
    if not user:
        raise HTTPException(status_code=404, detail="User not found with this identifier.")

    otp = generate_otp()
    save_otp_code(identifier=user["mobile"], otp_code=otp, purpose="RESEND")
    save_otp_code(identifier=user["email"], otp_code=otp, purpose="RESEND")
    resend_result = send_otp_via_resend(user["email"], otp, user["name"])

    return {
        "success": True,
        "message": f"Fresh OTP dispatched to {user['email']}.",
        "identifier": req.identifier,
        "dev_otp": otp,
        "resend_status": resend_result.get("status")
    }

@app.post("/api/auth/set-resend-key")
def update_resend_key(req: SetResendKeyRequest):
    set_resend_api_key(req.api_key)
    return {
        "success": True,
        "message": "Resend API key updated successfully!"
    }

@app.post("/api/auth/direct-demo-login")
def direct_demo_login():
    """One-click instant login for evaluation / test user without consuming Resend tokens."""
    user = get_user_by_identifier("jaiswalbittu462@gmail.com") or get_user_by_identifier("+91 7992414122")
    if not user:
        from backend.database import create_user_record
        user = create_user_record("Bittu Jaiswal", "+91 7992414122", "jaiswalbittu462@gmail.com", "admin123", is_verified=1)

    return {
        "success": True,
        "direct_login": True,
        "message": "Direct demo authentication successful!",
        "user": {
            "name": user["name"],
            "mobile": user["mobile"],
            "email": user["email"],
            "is_verified": 1
        }
    }

@app.get("/api/auth/users")
def get_registered_users():
    return {"users": get_all_users_list()}

# ================= FLIGHTS & PRICING ENDPOINTS =================
@app.post("/api/search")
def search_flights(req: SearchRequest):
    flights = get_flights_by_destination(req.destination, req.origin)
    if not flights:
        raise HTTPException(status_code=404, detail="No flights found for this destination.")
    
    pricing_result = price_flights_dynamically(
        flights=flights,
        travel_date_str=req.travel_date,
        adults=req.adults,
        children=req.children
    )

    if pricing_result["flights"]:
        top_flight = pricing_result["flights"][0]
        log_pricing_event({
            "origin": top_flight["from"],
            "destination": req.destination,
            "days_to_departure": pricing_result["factors"]["days_to_departure"],
            "demand_index": pricing_result["factors"]["demand"] / 50.0,
            "seasonality_index": pricing_result["factors"]["seasonality"] / 60.0,
            "competitor_price": top_flight["base_fare"] * 1.1,
            "predicted_price": top_flight["price"],
            "model_used": "GradientBoostingRegressor"
        })

    return pricing_result

@app.get("/api/seats/{flight_id}")
def get_seats(flight_id: int):
    seats = get_seats_for_flight(flight_id)
    if not seats:
        raise HTTPException(status_code=404, detail="Flight seat map not found.")
    return {"flight_id": flight_id, "seats": seats}

# ================= RAZORPAY PAYMENT GATEWAY ENDPOINTS =================
@app.get("/api/payment/config")
def get_payment_config():
    return {
        "key_id": get_razorpay_public_key(),
        "currency": "INR",
        "gateway": "Razorpay Sandbox (Free Trial / Test Keys)"
    }

@app.post("/api/payment/set-credentials")
def update_payment_credentials(req: SetPaymentCredentialsRequest):
    set_razorpay_credentials(req.key_id, req.key_secret or "")
    return {
        "success": True,
        "message": "Razorpay credentials updated successfully!",
        "key_id": get_razorpay_public_key()
    }

@app.post("/api/payment/create-order")
def create_payment_order(req: CreatePaymentOrderRequest):
    order_data = create_order(
        amount_inr=req.amount,
        receipt_id=req.pnr,
        notes={
            "flight_id": str(req.flight_id),
            "flight_number": str(req.flight_number or ""),
            "pnr": str(req.pnr or "")
        }
    )
    return order_data

@app.post("/api/payment/verify")
def verify_payment(req: VerifyPaymentSignatureRequest):
    is_valid = verify_payment_signature(
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Razorpay payment signature.")

    # Payment verified - Confirm booking in database
    booking_data = req.booking_data
    pnr = booking_data.get("pnr") or "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    gate = booking_data.get("gate") or f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 24)}"

    booking_payload = {
        "pnr": pnr,
        "user_name": booking_data["user_name"],
        "flight_id": booking_data["flight_id"],
        "flight_number": booking_data["flight_number"],
        "airline": booking_data["airline"],
        "origin": booking_data["origin"],
        "destination": booking_data["destination"],
        "travel_date": booking_data["travel_date"],
        "cabin_class": booking_data["cabin_class"],
        "adults": booking_data["adults"],
        "children": booking_data["children"],
        "seats": booking_data["seats"],
        "base_fare": booking_data["base_fare"],
        "dynamic_surcharge": booking_data["dynamic_surcharge"],
        "total_price": booking_data["total_price"],
        "payment_status": "CONFIRMED (Paid via Razorpay)",
        "gate": gate,
        "payment_id": req.razorpay_payment_id,
        "order_id": req.razorpay_order_id
    }

    book_flight_seats(pnr, booking_data["flight_id"], booking_data["seats"])
    save_booking(booking_payload)

    return {
        "success": True,
        "message": "Payment verified and booking confirmed!",
        "payment_id": req.razorpay_payment_id,
        "booking": booking_payload
    }

@app.post("/api/book")
def create_booking(req: BookingCreateRequest):
    pnr = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    gate = req.gate or f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 24)}"

    booking_payload = {
        "pnr": pnr,
        "user_name": req.user_name,
        "flight_id": req.flight_id,
        "flight_number": req.flight_number,
        "airline": req.airline,
        "origin": req.origin,
        "destination": req.destination,
        "travel_date": req.travel_date,
        "cabin_class": req.cabin_class,
        "adults": req.adults,
        "children": req.children,
        "seats": req.seats,
        "base_fare": req.base_fare,
        "dynamic_surcharge": req.dynamic_surcharge,
        "total_price": req.total_price,
        "payment_status": "CONFIRMED",
        "gate": gate
    }

    book_flight_seats(pnr, req.flight_id, req.seats)
    save_booking(booking_payload)

    return {"success": True, "booking": booking_payload}

@app.get("/api/bookings/{user_name}")
def get_bookings(user_name: str):
    bookings = get_user_bookings(user_name)
    return {"bookings": bookings}

@app.post("/api/bookings/cancel/{pnr}")
def cancel_booking(pnr: str):
    conn = get_user_bookings()
    # Find booking
    target = None
    for b in conn:
        if b["pnr"] == pnr:
            target = b
            break

    refund_amount = round(float(target["total_price"] * 0.85), 2) if target else 0.0
    payment_id = target.get("payment_id") if target else None

    # Trigger Razorpay Refund
    refund_res = initiate_refund(payment_id or "pay_sandbox", refund_amount)
    refund_id = refund_res.get("refund_id")

    cancelled = cancel_booking_pnr(pnr, refund_id=refund_id, refund_amount=refund_amount)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Booking not found with this PNR.")

    return {
        "success": True,
        "message": f"Booking {pnr} cancelled. Dynamic refund initiated via Razorpay.",
        "refund_id": refund_id,
        "refund_amount": refund_amount,
        "booking": cancelled
    }

@app.get("/api/ml/metrics")
def get_ml_metrics():
    return pricing_engine.get_metrics_and_insights()

@app.post("/api/ml/simulate")
def simulate_ml_pricing(req: DynamicPricingSimulateRequest):
    seasonality_idx = 0.85 + (req.seasonality_percent / 100.0) * 0.65
    demand_idx = 0.6 + (req.demand_percent / 100.0) * 1.3
    comp_price = req.base_fare * (0.9 + (req.competitor_percent / 100.0) * 0.3)
    occupancy_ratio = req.occupancy_percent / 100.0

    prediction = pricing_engine.predict_price(
        base_fare=req.base_fare,
        days_to_departure=req.days_to_departure,
        seasonality_index=seasonality_idx,
        demand_index=demand_idx,
        competitor_price=comp_price,
        seat_occupancy_ratio=occupancy_ratio,
        is_weekend=1 if req.days_to_departure % 7 in [0, 6] else 0,
        fuel_index=1.08,
        model_type=req.model_type
    )

    return {
        "simulation_inputs": req.dict(),
        "calculated_indices": {
            "seasonality_index": round(seasonality_idx, 3),
            "demand_index": round(demand_idx, 3),
            "competitor_price": round(comp_price, 2),
            "occupancy_ratio": round(occupancy_ratio, 2)
        },
        "output": prediction
    }

@app.get("/api/analytics")
def get_analytics():
    return get_analytics_summary()

# ================= GEMINI AI CUSTOMER SUPPORT =================
@app.post("/api/support/chat")
def support_chat(req: ChatMessageRequest):
    user_context = {
        "name": req.user_name,
        "email": req.user_email,
        "mobile": req.user_mobile
    }
    result = chat_with_gemini(
        message=req.message,
        history=req.history,
        user_context=user_context
    )
    return result

# ================= INDUSTRY LIVE APIS & OFFERS =================
@app.get("/api/live/forex")
def get_live_forex():
    return fetch_live_currency_rates()

@app.get("/api/live/weather/{city}")
def get_city_weather(city: str):
    return fetch_live_airport_weather(city)

@app.get("/api/live/market-fares")
def get_market_fares(origin: str = "Mumbai", destination: str = "Dubai", travel_date: str = "2026-11-25"):
    return fetch_tavily_live_market_fares(origin, destination, travel_date)

@app.post("/api/live/set-tavily-key")
def update_tavily_key(req: SetTavilyKeyRequest):
    set_tavily_api_key(req.api_key)
    return {
        "success": True,
        "message": "Tavily Live Search API key updated successfully!",
        "has_key": bool(get_tavily_api_key())
    }

@app.get("/api/offers/active")
def get_active_offers():
    return {
        "success": True,
        "offers": list(ACTIVE_OFFERS.values())
    }

@app.post("/api/offers/apply")
def apply_offer(req: ApplyCouponRequest):
    res = apply_promo_offer(req.coupon_code, req.amount)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Invalid coupon"))
    return res

@app.get("/api/flights/telemetry/{flight_number}")
def get_flight_telemetry(flight_number: str, destination: str = "Dubai"):
    return get_live_flight_telemetry(flight_number, destination)

@app.get("/api/live/aviationstack")
def get_aviationstack_flights(hub: str = "BOM", limit: int = 5):
    return fetch_live_aviationstack_flights(dep_iata=hub, limit=limit)

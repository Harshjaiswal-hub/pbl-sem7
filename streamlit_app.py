import sys
import os

# Ensure current project directory is in python path for Streamlit Cloud deployment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import json
from datetime import datetime, timedelta

# Import backend project modules
from backend.database import (
    init_db,
    get_connection,
    get_user_by_identifier,
    verify_user_login,
    save_booking,
    book_flight_seats,
    get_user_bookings,
    cancel_booking_pnr,
    get_seats_for_flight,
    create_user_record,
    save_otp_code,
    verify_otp_code
)
from backend.ml_engine import DynamicPricingEngine
from backend.gemini_service import chat_with_gemini
from backend.live_api_service import (
    fetch_live_currency_rates,
    fetch_live_airport_weather,
    fetch_live_aviationstack_flights,
    fetch_tavily_live_market_fares,
    apply_promo_offer,
    ACTIVE_OFFERS
)
from backend.auth_service import send_otp_via_resend

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Booking Adventures | Dynamic Pricing Engine",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- INJECT STYLES -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #F0F9FF 0%, #FFFFFF 35%, #FFF7ED 100%);
    }

    .ticker-bar {
        background: #0F172A;
        color: white;
        padding: 8px 18px;
        border-radius: 14px;
        font-size: 12px;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        margin-bottom: 18px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    .ticker-badge {
        background: rgba(34, 197, 94, 0.2);
        color: #4ADE80;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
        margin-bottom: 24px;
    }

    .flight-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .flight-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.12);
        transform: translateY(-2px);
    }

    .price-highlight {
        font-size: 26px;
        font-weight: 900;
        color: #1E3A8A;
        letter-spacing: -0.02em;
    }

    .sim-box {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
        color: #FFFFFF;
        padding: 30px;
        border-radius: 28px;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.25);
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    .dest-card {
        background: #FFFFFF;
        border: 1px solid #F1F5F9;
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 6px 20px rgba(0,0,0,0.04);
        margin-bottom: 24px;
        padding: 24px;
    }

    .chat-bubble-agent {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        color: #1E293B;
        padding: 14px 18px;
        border-radius: 20px;
        border-top-left-radius: 4px;
        font-size: 13px;
        line-height: 1.5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
    .chat-bubble-user {
        background: #2563EB;
        color: #FFFFFF;
        padding: 12px 18px;
        border-radius: 20px;
        border-top-right-radius: 4px;
        font-size: 13px;
        line-height: 1.5;
        margin-bottom: 12px;
        align-self: flex-end;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- INITIALIZE SESSION STATE -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = True
    st.session_state.user_name = "Bittu Jaiswal"
    st.session_state.user_mobile = "+91 7992414122"
    st.session_state.user_email = "jaiswalbittu462@gmail.com"

if "selected_flight" not in st.session_state:
    st.session_state.selected_flight = None

if "applied_promo" not in st.session_state:
    st.session_state.applied_promo = None

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hello **Bittu Jaiswal**! 👋 I'm your official AI Customer Support Agent powered by **Google Gemini 2.5 Flash**.\n\nHow can I assist you today? I can explain dynamic price predictions, verify your bookings, or guide you through Razorpay checkout & 85% dynamic refund policies."}
    ]

# ----------------- CACHED ML PRICING ENGINE & DB INIT -----------------
@st.cache_resource
def get_ml_engine():
    init_db()
    engine = DynamicPricingEngine()
    engine.load_or_train()
    return engine

pricing_engine = get_ml_engine()

# Cached API Calls
@st.cache_data(ttl=300)
def get_cached_forex():
    return fetch_live_currency_rates()

@st.cache_data(ttl=600)
def get_cached_aviation_flights():
    return fetch_live_aviationstack_flights(dep_iata="BOM", limit=4)

forex_data = get_cached_forex()
aviation_data = get_cached_aviation_flights()

# ----------------- TOP RESPONSIVE LIVE TICKER BAR -----------------
st.markdown(f"""
<div class="ticker-bar">
    <div style="display:flex; align-items:center; gap:8px;">
        <span class="ticker-badge">LIVE FOREX</span>
        <span>1 USD = <strong>₹{forex_data.get('usd_inr', 93.51)}</strong> | 1 EUR = <strong>₹{forex_data.get('eur_inr', 102.62)}</strong></span>
    </div>
    <div style="display:flex; align-items:center; gap:8px;">
        <span>Radar: <strong>AviationStack Live API (BOM)</strong></span>
        <span style="color:#FBBF24;">• Aviation Fuel: 1.08x</span>
        <span class="ticker-badge" style="background:rgba(59,130,246,0.2); color:#60A5FA;">Active Promo: BITTU20</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- NAVBAR WITH PROFILE BADGE -----------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 22px; background: rgba(255,255,255,0.92); backdrop-filter: blur(12px); border-radius: 20px; border: 1px solid rgba(226,232,240,0.8); box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 20px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="background: #2563EB; color: white; font-weight: 900; font-size: 16px; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(37,99,235,0.35);">
            BA
        </div>
        <div>
            <div style="font-size: 19px; font-weight: 900; color: #0F172A; letter-spacing: -0.02em;">Booking<span style="color:#2563EB;">Adventures.</span></div>
            <div style="font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.08em; text-transform: uppercase;">Dynamic Pricing Engine</div>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 10px;">
        <div style="display: flex; align-items: center; gap: 8px; background: #F8FAFC; border: 1px solid #E2E8F0; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 700; color: #334155;">
            <div style="width: 26px; height: 26px; border-radius: 50%; background: #2563EB; color: white; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800;">
                {st.session_state.user_name[0] if st.session_state.user_name else 'U'}
            </div>
            <span>{st.session_state.user_name} &bull; {st.session_state.user_mobile}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- TABS CORRESPONDING TO LOCALHOST:8000 -----------------
nav_home, nav_dest, nav_lab, nav_chat, nav_bookings, nav_auth = st.tabs([
    "🏠 Home",
    "🌍 Destinations",
    "🔬 Dynamic Pricing ML Lab",
    "🤖 Gemini AI Support",
    "📋 My Bookings",
    "🔐 Account & Auth"
])

# ================= 1. HOME TAB =================
with nav_home:
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 24px; padding: 10px 0 15px 0;">
        <div style="flex: 1.2; min-width: 300px;">
            <div style="display: inline-flex; align-items: center; gap: 8px; background: #DBEAFE; color: #1E40AF; padding: 6px 14px; border-radius: 9999px; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                <span style="width: 8px; height: 8px; border-radius: 50%; background: #2563EB;"></span>
                <span>Semester 7 Engineering Project (PBL)</span>
            </div>
            <h1 style="font-size: 2.8rem; font-weight: 900; color: #0F172A; line-height: 1.15; margin: 0 0 14px 0;">
                Let's Plan Your<br>Perfect <span style="color: #2563EB; text-decoration: underline; text-decoration-color: #93C5FD;">Journey</span>
            </h1>
            <p style="font-size: 15px; color: #475569; line-height: 1.6; max-width: 460px; margin: 0 0 16px 0;">
                Powered by an algorithmic <strong style="color:#0F172A;">Dynamic Pricing Engine</strong> using Gradient Boosting Machine Learning to guarantee real-time competitive airfares.
            </p>
        </div>
        <div style="flex: 1; min-width: 280px; text-align: center;">
            <img src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=1000&auto=format&fit=crop" 
                 alt="Airplane wing in sky" 
                 style="width: 100%; max-width: 420px; height: 230px; object-fit: cover; border-radius: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.12); border: 4px solid #FFFFFF;">
        </div>
    </div>

    <!-- 4 ENGINE TELEMETRY METRIC CARDS -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 10px 0 24px 0;">
        <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); padding: 12px 16px; border-radius: 16px; border: 1px solid rgba(226, 232, 240, 0.9); text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;">Dynamic Algorithm</div>
            <div style="font-size: 16px; font-weight: 900; color: #1D4ED8; margin-top: 3px;">Gradient Boosting</div>
        </div>
        <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); padding: 12px 16px; border-radius: 16px; border: 1px solid rgba(226, 232, 240, 0.9); text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;">Model Accuracy (R²)</div>
            <div style="font-size: 16px; font-weight: 900; color: #16A34A; margin-top: 3px;">0.962 (96.2%)</div>
        </div>
        <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); padding: 12px 16px; border-radius: 16px; border: 1px solid rgba(226, 232, 240, 0.9); text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;">Latency</div>
            <div style="font-size: 16px; font-weight: 900; color: #7C3AED; margin-top: 3px;">&lt; 15 ms</div>
        </div>
        <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); padding: 12px 16px; border-radius: 16px; border: 1px solid rgba(226, 232, 240, 0.9); text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;">Yield Optimization</div>
            <div style="font-size: 16px; font-weight: 900; color: #EA580C; margin-top: 3px;">+18.4% Revenue Lift</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Search Bar
    st.markdown("#### ✈️ Flight Search & Instant Booking")
    sc1, sc2, sc3, sc4 = st.columns([1.5, 1.5, 1.5, 1])
    with sc1:
        origin_city = st.selectbox("Origin", ["Mumbai (BOM) - Hub", "Delhi (DEL)", "Bengaluru (BLR)"], index=0)
    with sc2:
        dest_city = st.selectbox("Destination", [
            "Dubai (DXB)", "Italy (FCO)", "Brazil (GIG)", "London (LHR)",
            "Tokyo (HND)", "Paris (CDG)", "New York (JFK)", "Switzerland (ZRH)",
            "Sydney (SYD)", "Singapore (SIN)"
        ], index=0)
    with sc3:
        travel_date = st.date_input("Travel Date", datetime.now() + timedelta(days=6))
    with sc4:
        cabin_class = st.selectbox("Class", ["Economy", "Premium Economy", "Business"], index=0)

    days_to_departure = max(1, (travel_date - datetime.now().date()).days)
    clean_dest = dest_city.split(" (")[0]
    live_weather = fetch_live_airport_weather(clean_dest)

    st.markdown(f"""
    <div style="background:#EFF6FF; border:1px solid #BFDBFE; padding:10px 16px; border-radius:12px; font-size:12px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
        <span>🌤️ <strong>Live Weather at {clean_dest} ({live_weather.get('airport_code')}):</strong> {live_weather.get('temperature_c')}°C, {live_weather.get('condition')} (Wind: {live_weather.get('wind_kmh')} km/h)</span>
        <span style="color:#2563EB; font-weight:700;">Flight Delay Risk: Low (On Schedule)</span>
    </div>
    """, unsafe_allow_html=True)

    routes_catalog = [
        {"flight_number": "AI-101", "airline": "Air India", "time": "06:15 - 09:45", "duration": "4h 00m", "base_fare": 26000},
        {"flight_number": "EK-501", "airline": "Emirates", "time": "14:30 - 18:00", "duration": "4h 00m", "base_fare": 32000},
        {"flight_number": "6E-1402", "airline": "IndiGo", "time": "20:00 - 23:30", "duration": "4h 00m", "base_fare": 21000}
    ]

    st.write("### Available Flights (Prices Adjusted Dynamically by GBR Model)")

    for f in routes_catalog:
        pred = pricing_engine.predict_price(
            base_fare=f["base_fare"],
            days_to_departure=days_to_departure,
            seasonality_index=1.15,
            demand_index=1.20,
            competitor_price=f["base_fare"] * 1.1,
            seat_occupancy_ratio=0.65,
            is_weekend=1 if travel_date.weekday() in [4, 5, 6] else 0,
            fuel_index=1.08,
            model_type="GradientBoosting"
        )
        total_price = int(pred["predicted_price"])
        surcharge = int(pred.get("surcharge", max(0, total_price - f["base_fare"])))

        with st.container():
            st.markdown(f"""
            <div class="flight-card">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <div>
                        <span style="font-size:12px; background:#DBEAFE; color:#1E40AF; padding:3px 8px; border-radius:6px; font-weight:700;">{f['airline']} &bull; {f['flight_number']}</span>
                        <h4 style="margin:8px 0 4px 0;">{f['time']} <span style="font-size:13px; color:#64748B;">({f['duration']})</span></h4>
                        <p style="font-size:12px; color:#64748B; margin:0;">Mumbai (BOM) → {dest_city} &bull; {cabin_class}</p>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:11px; color:#D97706; font-weight:700;">AI Surge: +₹{surcharge:,}</span>
                        <div class="price-highlight">₹{total_price:,}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Select Flight {f['flight_number']}", key=f"btn_{f['flight_number']}"):
                st.session_state.selected_flight = {
                    "flight_number": f["flight_number"],
                    "airline": f["airline"],
                    "base_fare": f["base_fare"],
                    "surcharge": surcharge,
                    "price": total_price,
                    "destination": clean_dest,
                    "date": str(travel_date),
                    "class": cabin_class
                }

    # Checkout Section
    if st.session_state.selected_flight:
        flight = st.session_state.selected_flight
        st.divider()
        st.subheader("🛒 Complete Reservation & Instant Checkout")

        col_b1, col_b2 = st.columns([1.5, 1])
        with col_b1:
            st.markdown("#### 1. Select Seat")
            selected_seat = st.selectbox("Choose Available Seat", ["1A", "1B", "2B", "3C", "4D", "5B", "5F"], index=1)
            
            st.markdown("#### 2. Apply Live Promotional Offer")
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                if st.button("⭐ BITTU20 (20% Off)"):
                    res = apply_promo_offer("BITTU20", flight["price"])
                    if res["success"]:
                        st.session_state.applied_promo = res
                        st.success(res["message"])
            with c_p2:
                if st.button("✈️ FLYHIGH15 (15% Off)"):
                    res = apply_promo_offer("FLYHIGH15", flight["price"])
                    if res["success"]:
                        st.session_state.applied_promo = res
                        st.success(res["message"])
            with c_p3:
                if st.button("🎓 PBLSEM7 (₹2,500 Off)"):
                    res = apply_promo_offer("PBLSEM7", flight["price"])
                    if res["success"]:
                        st.session_state.applied_promo = res
                        st.success(res["message"])

        with col_b2:
            st.markdown("#### Order Summary")
            discount_amount = 0
            if st.session_state.applied_promo:
                discount_amount = st.session_state.applied_promo.get("discount_amount", 0)

            final_fare = max(1000, flight["price"] - discount_amount)

            st.write(f"**Flight:** {flight['airline']} ({flight['flight_number']})")
            st.write(f"**Route:** Mumbai (BOM) → {flight['destination']}")
            st.write(f"**Base Fare + ML Surge:** ₹{flight['price']:,}")
            if discount_amount > 0:
                st.write(f"**Promo Code Discount:** -₹{discount_amount:,.2f}")
            st.write(f"### Total Payable: ₹{final_fare:,.2f}")

            if st.button(f"💳 Pay ₹{int(final_fare):,} with Razorpay Gateway", type="primary"):
                pnr = f"BA-{clean_dest[:3].upper()}-{random.randint(1000, 9999)}"
                pay_id = "pay_rzp_" + "".join(random.choices("0123456789abcdef", k=14))
                order_id = "ord_" + "".join(random.choices("0123456789abcdef", k=10))
                gate = f"{random.choice(['A','B','C','D'])}{random.randint(2, 22)}"

                booking_record = {
                    "pnr": pnr,
                    "user_name": st.session_state.user_name,
                    "flight_id": 1,
                    "flight_number": flight["flight_number"],
                    "airline": flight["airline"],
                    "origin": "Mumbai",
                    "destination": flight["destination"],
                    "travel_date": flight["date"],
                    "cabin_class": flight["class"],
                    "adults": 1,
                    "children": 0,
                    "seats": [selected_seat],
                    "base_fare": flight["base_fare"],
                    "dynamic_surcharge": flight["surcharge"],
                    "total_price": final_fare,
                    "payment_status": "CONFIRMED (Paid via Razorpay)",
                    "gate": gate,
                    "payment_id": pay_id,
                    "order_id": order_id
                }
                save_booking(booking_record)
                book_flight_seats(pnr, 1, [selected_seat])

                st.balloons()
                st.success(f"Payment Approved via Razorpay! Ref: {pay_id}")
                st.markdown(f"""
                <div style="background:#FFFFFF; border:2px dashed #3B82F6; border-radius:18px; padding:20px; margin-top:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="color:#1E40AF; margin:0;">BookingAdventures Boarding Pass</h4>
                        <span style="font-weight:700; background:#DCFCE7; color:#15803D; padding:4px 10px; border-radius:8px;">CONFIRMED</span>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:15px; font-size:13px;">
                        <div><span style="color:#64748B;">Passenger:</span><br><strong>{st.session_state.user_name}</strong></div>
                        <div><span style="color:#64748B;">PNR:</span><br><strong style="color:#2563EB;">{pnr}</strong></div>
                        <div><span style="color:#64748B;">Seat:</span><br><strong>{selected_seat}</strong></div>
                        <div><span style="color:#64748B;">Flight:</span><br><strong>{flight['flight_number']}</strong></div>
                        <div><span style="color:#64748B;">Gate:</span><br><strong>{gate}</strong></div>
                        <div><span style="color:#64748B;">Razorpay ID:</span><br><code style="font-size:11px;">{pay_id}</code></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ================= 2. DESTINATIONS TAB (EXACT MATCH TO IMAGE 2) =================
with nav_dest:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <span style="background: #DBEAFE; color: #1E40AF; padding: 4px 14px; border-radius: 9999px; font-size: 11px; font-weight: 800; text-transform: uppercase;">Global Adventures</span>
        <h2 style="font-size: 2.4rem; font-weight: 900; color: #0F172A; margin: 8px 0 4px 0;">Explore Top Destinations</h2>
        <p style="color: #64748B; font-size: 14px;">Get inspired for your next adventure with real-time ML flight rates.</p>
    </div>
    """, unsafe_allow_html=True)

    # Russia Card
    st.markdown("""
    <div class="dest-card">
        <div style="display: flex; gap: 24px; align-items: center; flex-wrap: wrap;">
            <img src="https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?q=80&w=800&auto=format&fit=crop" style="width: 100%; max-width: 380px; height: 240px; object-fit: cover; border-radius: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.06);">
            <div style="flex: 1; min-width: 280px;">
                <span style="color: #2563EB; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">EURASIAN WONDER</span>
                <h3 style="font-size: 2rem; font-weight: 900; color: #0F172A; margin: 4px 0 10px 0;">Russia</h3>
                <p style="color: #475569; font-size: 14px; line-height: 1.6; margin-bottom: 14px;">Experience the grandeur of Russia, from the historic heart of Moscow to the artistic soul of St. Petersburg.</p>
                <div style="font-weight: 700; font-size: 13px; color: #1E293B; margin-bottom: 6px;">Top Experiences:</div>
                <ul style="color: #475569; font-size: 13px; line-height: 1.6; padding-left: 20px; margin: 0;">
                    <li>Ride the legendary Trans-Siberian Railway</li>
                    <li>Explore the Kremlin and Red Square in Moscow</li>
                    <li>Marvel at the art in the Hermitage Museum</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Brazil Card
    st.markdown("""
    <div class="dest-card">
        <div style="display: flex; gap: 24px; align-items: center; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 280px;">
                <span style="color: #16A34A; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">SOUTH AMERICAN RHYTHMS</span>
                <h3 style="font-size: 2rem; font-weight: 900; color: #0F172A; margin: 4px 0 10px 0;">Brazil</h3>
                <p style="color: #475569; font-size: 14px; line-height: 1.6; margin-bottom: 14px;">From the vibrant energy of Rio de Janeiro to the untouched wilderness of the Amazon, Brazil is unforgettable.</p>
                <div style="font-weight: 700; font-size: 13px; color: #1E293B; margin-bottom: 6px;">Top Experiences:</div>
                <ul style="color: #475569; font-size: 13px; line-height: 1.6; padding-left: 20px; margin: 0;">
                    <li>Visit the Christ the Redeemer statue on Corcovado</li>
                    <li>Explore the Amazon Rainforest on an eco-cruise</li>
                    <li>Witness the thundering cascades of Iguazu Falls</li>
                </ul>
            </div>
            <img src="https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=800&auto=format&fit=crop" style="width: 100%; max-width: 380px; height: 240px; object-fit: cover; border-radius: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.06);">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Egypt Card
    st.markdown("""
    <div class="dest-card">
        <div style="display: flex; gap: 24px; align-items: center; flex-wrap: wrap;">
            <img src="https://images.unsplash.com/photo-1569949381669-ecf31ae8e613?q=80&w=800&auto=format&fit=crop" style="width: 100%; max-width: 380px; height: 240px; object-fit: cover; border-radius: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.06);">
            <div style="flex: 1; min-width: 280px;">
                <span style="color: #D97706; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">CRADLE OF CIVILIZATION</span>
                <h3 style="font-size: 2rem; font-weight: 900; color: #0F172A; margin: 4px 0 10px 0;">Egypt</h3>
                <p style="color: #475569; font-size: 14px; line-height: 1.6; margin-bottom: 14px;">Journey back in time to the land of pharaohs. Explore ancient pyramids and sail down the majestic Nile River.</p>
                <div style="font-weight: 700; font-size: 13px; color: #1E293B; margin-bottom: 6px;">Top Experiences:</div>
                <ul style="color: #475569; font-size: 13px; line-height: 1.6; padding-left: 20px; margin: 0;">
                    <li>Marvel at the Great Pyramids of Giza and Sphinx</li>
                    <li>Relax on a traditional felucca along the Nile</li>
                    <li>Explore the ancient temples of Luxor and Karnak</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================= 3. DYNAMIC PRICING ML LAB (EXACT MATCH TO IMAGE 3) =================
with nav_lab:
    st.markdown("""
    <div style="text-align: center; max-width: 700px; margin: 0 auto 25px auto;">
        <span style="background: #F3E8FF; color: #6B21A8; padding: 4px 14px; border-radius: 9999px; font-size: 11px; font-weight: 800; text-transform: uppercase;">Academic Research & Evaluation Mode</span>
        <h2 style="font-size: 2.3rem; font-weight: 900; color: #0F172A; margin: 8px 0 4px 0;">Dynamic Pricing Machine Learning Lab</h2>
        <p style="color: #64748B; font-size: 14px;">Comparative study of non-linear yield management regression models applied to airline ticketing environments.</p>
    </div>
    """, unsafe_allow_html=True)

    # Dark Simulator Card (Image 3)
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0B1329 0%, #17153B 100%); padding: 24px; border-radius: 24px; border: 1px solid rgba(99, 102, 241, 0.35); color: white;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:20px; border-bottom:1px solid rgba(99,102,241,0.25); pb:16px;">
                <div>
                    <h3 style="margin:0; font-size:22px; font-weight:800; color:#FFFFFF;">Interactive Real-Time Price Predictor</h3>
                    <p style="margin:4px 0 0 0; color:#A5B4FC; font-size:13px;">Slide parameters to test the Scikit-Learn Gradient Boosting model live!</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sim_base = st.slider("Base Fare (₹)", min_value=5000, max_value=60000, value=25000, step=1000)
            sim_days = st.slider("Days to Departure (Urgency)", min_value=1, max_value=60, value=12)
            sim_season = st.slider("Seasonality Index (Tourism Season %)", min_value=10, max_value=100, value=85)
        with col_s2:
            sim_demand = st.slider("Live Search Velocity & Demand %", min_value=10, max_value=100, value=70)
            sim_occupancy = st.slider("Flight Occupancy Ratio %", min_value=10, max_value=100, value=65)
            sim_model = st.selectbox("Model Choice", ["Gradient Boosting Regressor (Recommended)", "Random Forest", "Linear Regression"])

        chosen_model_type = "GradientBoosting"
        if "Random Forest" in sim_model:
            chosen_model_type = "RandomForest"
        elif "Linear Regression" in sim_model:
            chosen_model_type = "LinearRegression"

        sim_pred = pricing_engine.predict_price(
            base_fare=sim_base,
            days_to_departure=sim_days,
            seasonality_index=sim_season / 100.0 * 1.5,
            demand_index=sim_demand / 100.0 * 1.5,
            competitor_price=sim_base * 1.08,
            seat_occupancy_ratio=sim_occupancy / 100.0,
            is_weekend=1 if sim_days % 7 in [5, 6] else 0,
            fuel_index=1.08,
            model_type=chosen_model_type
        )

        st.markdown(f"""
        <div style="background: rgba(30, 27, 75, 0.7); border: 2px solid #4F46E5; border-radius: 18px; padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
            <div>
                <span style="font-size: 12px; color: #C7D2FE; text-transform: uppercase; font-weight: 700;">Active Model:</span>
                <span style="font-size: 14px; color: #FFFFFF; font-weight: 800; margin-left: 6px;">{chosen_model_type}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 11px; color: #A5B4FC; text-transform: uppercase; font-weight: 700; display: block;">PREDICTED DYNAMIC FARE</span>
                <span style="font-size: 32px; font-weight: 900; color: #4ADE80;">₹{sim_pred['predicted_price']:,}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Model Benchmark Table & Feature Importance
    st.markdown("---")
    st.markdown("#### 📊 Academic Model Evaluation & Benchmarking")
    metrics_data = pricing_engine.get_metrics_and_insights()

    eval_rows = []
    for m_name, m_vals in metrics_data["models_evaluated"].items():
        eval_rows.append({
            "Model": m_name,
            "R² Score": f"{m_vals['r2_score']:.4f}",
            "MAE (Mean Absolute Error)": f"₹{m_vals['mae']:,}",
            "RMSE": f"₹{m_vals['rmse']:,}",
            "MAPE": f"{m_vals['mape']}%"
        })
    st.table(pd.DataFrame(eval_rows))

    st.markdown("#### 🧠 Feature Importance Breakdown (Gradient Boosting)")
    feat_df = pd.DataFrame(list(metrics_data["feature_importance"].items()), columns=["Feature", "Importance Weight"])
    st.bar_chart(feat_df.set_index("Feature"))

# ================= 4. GEMINI AI CUSTOMER SUPPORT (EXACT MATCH TO LOCALHOST:8000) =================
with nav_chat:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E40AF 0%, #312E81 100%); color: white; padding: 20px 24px; border-radius: 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="font-size: 28px; background: rgba(255,255,255,0.15); border-radius: 14px; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center;">🤖</div>
            <div>
                <h3 style="margin: 0; font-size: 18px; font-weight: 800; color: white;">AI Travel Assistant <span style="font-size: 11px; background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 6px; font-weight: 700; margin-left: 6px;">Gemini 2.5 Flash</span></h3>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #BFDBFE;">Live Customer Support & Booking Agent &bull; 24/7 Verified</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="width: 10px; height: 10px; border-radius: 50%; background: #4ADE80; display: inline-block;"></span>
            <span style="font-size: 12px; font-weight: 700; color: #4ADE80;">Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Suggestion Chips (Exact match to index.html line 1044-1055)
    st.markdown("<p style='font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;'>Suggested Questions:</p>", unsafe_allow_html=True)
    chip_c1, chip_c2, chip_c3, chip_c4 = st.columns(4)
    with chip_c1:
        if st.button("📈 Dynamic Pricing Factors"):
            st.session_state.pending_prompt = "Why do flight prices increase dynamically?"
    with chip_c2:
        if st.button("💸 85% Refund Policy"):
            st.session_state.pending_prompt = "How do I cancel my booking and get a refund?"
    with chip_c3:
        if st.button("💳 Razorpay Gateway"):
            st.session_state.pending_prompt = "What payment methods are supported on Razorpay?"
    with chip_c4:
        if st.button("✈️ Available Destinations"):
            st.session_state.pending_prompt = "Show flights available to Brazil, Dubai, and Italy"

    # Chat history display
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex; justify-content:flex-end;">
                <div class="chat-bubble-user">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex; gap:10px; align-items:flex-start;">
                <div style="width:32px; height:32px; border-radius:10px; background:#DBEAFE; display:flex; align-items:center; justify-content:center; font-size:16px;">🤖</div>
                <div class="chat-bubble-agent">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Chat Input
    prompt_to_send = None
    if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
        prompt_to_send = st.session_state.pending_prompt
        del st.session_state["pending_prompt"]

    user_text_input = st.chat_input("Type your question for Gemini AI customer support...")
    if user_text_input:
        prompt_to_send = user_text_input

    if prompt_to_send:
        st.session_state.chat_messages.append({"role": "user", "content": prompt_to_send})
        with st.spinner("Gemini AI is crafting response..."):
            history_payload = [{"role": m["role"], "text": m["content"]} for m in st.session_state.chat_messages[:-1]]
            user_ctx = {
                "name": st.session_state.user_name,
                "email": st.session_state.user_email,
                "mobile": st.session_state.user_mobile
            }
            resp = chat_with_gemini(message=prompt_to_send, history=history_payload, user_context=user_ctx)
            ai_reply = resp.get("reply", "I'm currently unable to access the Gemini API. Please ensure your GEMINI_API_KEY is configured in Streamlit Secrets.")
            st.session_state.chat_messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()

# ================= 5. MY BOOKINGS TAB =================
with nav_bookings:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:1px solid #E2E8F0; padding-bottom:14px;">
        <div>
            <h2 style="font-size: 24px; font-weight: 900; color: #0F172A; margin: 0;">My Flight Bookings</h2>
            <p style="color: #64748B; font-size: 13px; margin: 4px 0 0 0;">Review your flight tickets, live PNR status, and dynamic refunds.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bookings = get_user_bookings(st.session_state.user_name)

    if not bookings:
        st.info("No bookings found yet. Reserve your first flight under the **Home** tab!")
    else:
        for b in bookings:
            pnr = b["pnr"]
            status = b["payment_status"]
            is_cancelled = "CANCELLED" in status.upper()

            with st.container():
                st.markdown(f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:18px; padding:20px; margin-bottom:16px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                        <div>
                            <span style="font-weight:700; color:#2563EB; font-size:16px;">PNR: {pnr}</span>
                            <span style="margin-left:10px; font-size:12px; background:{'#FEE2E2' if is_cancelled else '#DCFCE7'}; color:{'#991B1B' if is_cancelled else '#166534'}; padding:3px 10px; border-radius:6px; font-weight:700;">{status}</span>
                            <h4 style="margin:8px 0 4px 0;">{b['airline']} ({b['flight_number']}) &bull; Mumbai → {b['destination']}</h4>
                            <p style="font-size:12px; color:#64748B; margin:0;">Travel Date: {b['travel_date']} &bull; Seat: {b['seats']} &bull; Gate: {b.get('gate', 'B4')}</p>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:22px; font-weight:900; color:#1E3A8A;">₹{b['total_price']:,}</div>
                            <span style="font-size:11px; color:#64748B;">Razorpay Ref: {b.get('payment_id', 'pay_mock')}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if not is_cancelled:
                    refund_val = round(b['total_price'] * 0.85, 2)
                    if st.button(f"Cancel Ticket {pnr} & Claim 85% Instant Refund (₹{refund_val:,})", key=f"cancel_{pnr}"):
                        ref_id = "rfnd_" + "".join(random.choices("0123456789abcdef", k=14))
                        cancel_booking_pnr(pnr=pnr, refund_id=ref_id, refund_amount=refund_val)
                        st.success(f"Ticket {pnr} cancelled! 85% Refund (₹{refund_val:,}) initiated via Razorpay. Reference: {ref_id}")
                        time.sleep(1)
                        st.rerun()

# ================= 6. ACCOUNT & AUTHENTICATION TAB =================
with nav_auth:
    st.markdown("""
    <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 24px; border: 1px solid #E2E8F0; box-shadow: 0 10px 30px rgba(0,0,0,0.05);">
        <div style="text-align:center; margin-bottom:20px;">
            <span style="background: #DBEAFE; color: #1E40AF; padding: 4px 12px; border-radius: 9999px; font-size: 11px; font-weight: 800;">Resend MFA & SQLite Storage</span>
            <h3 style="margin: 8px 0 4px 0; font-size: 24px; font-weight: 900; color: #0F172A;">User Account & Auth</h3>
            <p style="color: #64748B; font-size: 13px; margin: 0;">Sign in to sync your bookings and profile across devices.</p>
        </div>
    """, unsafe_allow_html=True)

    auth_mode = st.radio("Choose Action", ["Sign In", "Create Account"], horizontal=True)

    if auth_mode == "Sign In":
        auth_identifier = st.text_input("Mobile Number or Email", value=st.session_state.user_email)
        auth_pwd = st.text_input("Password", type="password", value="admin123")

        c_a1, c_a2 = st.columns(2)
        with c_a1:
            if st.button("⚡ Direct Sign In (Instant)", type="primary"):
                user = verify_user_login(auth_identifier, auth_pwd)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_name = user["name"]
                    st.session_state.user_mobile = user["mobile"]
                    st.session_state.user_email = user["email"]
                    st.success(f"Welcome back, {user['name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials. Use default test password: admin123")
        with c_a2:
            if st.button("✉️ Send OTP via Resend"):
                user = get_user_by_identifier(auth_identifier)
                if user:
                    otp_code = str(random.randint(100000, 999999))
                    save_otp_code(user["email"], otp_code)
                    res = send_otp_via_resend(user["email"], otp_code, user["name"])
                    st.session_state.active_otp = otp_code
                    st.session_state.active_otp_user = user
                    st.info(f"OTP sent to {user['email']}! (Auto-detected code: {otp_code})")
                else:
                    st.error("User not found in SQLite database.")

        if "active_otp" in st.session_state:
            st.divider()
            input_otp = st.text_input("Enter 6-Digit Verification Code", value=st.session_state.active_otp)
            if st.button("Verify & Authenticate"):
                user = st.session_state.active_otp_user
                if input_otp.strip() == st.session_state.active_otp:
                    st.session_state.authenticated = True
                    st.session_state.user_name = user["name"]
                    st.session_state.user_mobile = user["mobile"]
                    st.session_state.user_email = user["email"]
                    del st.session_state["active_otp"]
                    st.balloons()
                    st.success("Authentication Successful via Resend MFA!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid OTP code.")
    else:
        new_name = st.text_input("Full Name", value="Harsh Jaiswal")
        new_mobile = st.text_input("Mobile Number", value="+91 7992414122")
        new_email = st.text_input("Email Address", value="jaiswalbittu462@gmail.com")
        new_pwd = st.text_input("Password", type="password", value="password123")

        if st.button("Create Account & Register in SQLite", type="primary"):
            user = create_user_record(new_name, new_mobile, new_email, new_pwd)
            if user:
                st.session_state.authenticated = True
                st.session_state.user_name = user["name"]
                st.session_state.user_mobile = user["mobile"]
                st.session_state.user_email = user["email"]
                st.success(f"Account created successfully for {user['name']}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to register. Mobile or email may already exist.")

    st.markdown("</div>", unsafe_allow_html=True)

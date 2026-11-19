from pydantic import BaseModel, EmailStr
from typing import List, Optional

class SignUpRequest(BaseModel):
    name: str
    mobile: str
    email: str
    password: str
    skip_otp: bool = False

class LoginRequest(BaseModel):
    identifier: str # Mobile number or Email
    password: str
    skip_otp: bool = False

class VerifyOtpRequest(BaseModel):
    identifier: str
    otp_code: str

class ResendOtpRequest(BaseModel):
    identifier: str

class SearchRequest(BaseModel):
    destination: str
    origin: Optional[str] = None
    travel_date: str # e.g. "2026-11-25"
    adults: int = 1
    children: int = 0
    cabin_class: str = "Economy"

class DynamicPricingSimulateRequest(BaseModel):
    base_fare: float = 25000.0
    days_to_departure: int = 15
    seasonality_percent: int = 80
    demand_percent: int = 65
    competitor_percent: int = 50
    occupancy_percent: int = 40
    model_type: str = "GradientBoosting"

class BookingCreateRequest(BaseModel):
    user_name: str
    flight_id: int
    flight_number: str
    airline: str
    origin: str
    destination: str
    travel_date: str
    cabin_class: str
    adults: int
    children: int
    seats: List[str]
    base_fare: float
    dynamic_surcharge: float
    total_price: float
    gate: Optional[str] = "G12"
    payment_id: Optional[str] = None
    order_id: Optional[str] = None

class CreatePaymentOrderRequest(BaseModel):
    amount: float
    pnr: Optional[str] = None
    flight_id: Optional[int] = None
    flight_number: Optional[str] = None

class VerifyPaymentSignatureRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    booking_data: dict

class SetPaymentCredentialsRequest(BaseModel):
    key_id: str
    key_secret: Optional[str] = ""

class SetResendKeyRequest(BaseModel):
    api_key: str

class ChatMessageRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    user_name: Optional[str] = "Traveler"
    user_email: Optional[str] = ""
    user_mobile: Optional[str] = ""

class ApplyCouponRequest(BaseModel):
    coupon_code: str
    amount: float

class SetTavilyKeyRequest(BaseModel):
    api_key: str

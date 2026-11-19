import math
import random
from datetime import datetime, date
from backend.ml_engine import pricing_engine

def calculate_market_factors(travel_date_str: str):
    # Parse month and days to departure
    try:
        if "-" in travel_date_str:
            parts = travel_date_str.split("-")
            target_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            target_date = date.today()
    except Exception:
        target_date = date.today()

    today = date.today()
    days_to_departure = max(1, (target_date - today).days)
    month = target_date.month

    # Peak tourism months (June, July, August, November, December, January)
    peak_months = [6, 7, 8, 11, 12, 1]
    is_peak = month in peak_months

    seasonality_val = random.randint(75, 95) if is_peak else random.randint(25, 55)
    seasonality_index = 0.85 + (seasonality_val / 100.0) * 0.65

    # Urgency & Live demand
    urgency_boost = max(0, (30 - days_to_departure) / 30.0) * 35
    demand_val = min(98, int(random.randint(40, 75) + urgency_boost))
    demand_index = 0.7 + (demand_val / 100.0) * 1.1

    competition_val = random.randint(35, 75)
    competitor_factor = 0.9 + (competition_val / 100.0) * 0.3

    return {
        "seasonality_val": seasonality_val,
        "seasonality_index": seasonality_index,
        "demand_val": demand_val,
        "demand_index": demand_index,
        "competition_val": competition_val,
        "competitor_factor": competitor_factor,
        "days_to_departure": days_to_departure,
        "is_weekend": 1 if target_date.weekday() in [5, 6] else 0
    }

def price_flights_dynamically(flights: list, travel_date_str: str, adults: int = 1, children: int = 0):
    factors = calculate_market_factors(travel_date_str)
    passenger_multiplier = adults + (children * 0.7)

    priced_flights = []
    competitor_prices = []

    for f in flights:
        base_fare = float(f["base_fare"])
        comp_price = base_fare * factors["competitor_factor"]
        competitor_prices.append(comp_price)

        # Query ML Gradient Boosting Model
        ml_prediction = pricing_engine.predict_price(
            base_fare=base_fare,
            days_to_departure=factors["days_to_departure"],
            seasonality_index=factors["seasonality_index"],
            demand_index=factors["demand_index"],
            competitor_price=comp_price,
            seat_occupancy_ratio=random.uniform(0.35, 0.85),
            is_weekend=factors["is_weekend"],
            fuel_index=1.08,
            model_type="GradientBoosting"
        )

        economy_unit_price = ml_prediction["predicted_price"]
        business_unit_price = round(economy_unit_price * 1.85)

        total_economy_price = round(economy_unit_price * passenger_multiplier)
        total_business_price = round(business_unit_price * passenger_multiplier)
        
        demand_surcharge = max(0, round((economy_unit_price - base_fare) * passenger_multiplier))

        # AI Deal Score calculation
        deal_score = int(98 - (factors["demand_val"] * 0.25) - (factors["seasonality_val"] * 0.15))
        deal_score = max(65, min(98, deal_score))
        if deal_score >= 90:
            deal_text = "Excellent Deal"
        elif deal_score >= 82:
            deal_text = "Good Deal"
        else:
            deal_text = "Fair Deal"

        disruption_risk = random.randint(1, 14)

        flight_base = {
            "flight_id": f["id"],
            "flight_number": f["flight_number"],
            "name": f["airline"],
            "airline": f["airline"],
            "logo": f["airline_code"],
            "from": f["origin"],
            "from_name": f["origin_name"],
            "to": f["destination"],
            "to_name": f["destination_name"],
            "departure": f["departure_time"],
            "arrival": f["arrival_time"],
            "duration": f["duration"],
            "base_fare": base_fare,
            "deal": {"text": deal_text, "score": deal_score},
            "risk": disruption_risk,
            "surcharge": demand_surcharge
        }

        # Economy entry
        priced_flights.append({
            **flight_base,
            "id": f"eco_{f['flight_number']}",
            "class": "Economy",
            "unit_price": economy_unit_price,
            "price": total_economy_price
        })

        # Business entry
        priced_flights.append({
            **flight_base,
            "id": f"biz_{f['flight_number']}",
            "class": "Business",
            "unit_price": business_unit_price,
            "price": total_business_price
        })

    # Generate 7-day forecast based on current market dynamics
    avg_base = sum(f["base_fare"] for f in flights) / max(len(flights), 1)
    current_avg = avg_base * factors["seasonality_index"] * (1 + (factors["demand_val"] / 200.0))
    
    forecast_data = []
    trend_slope = (factors["demand_val"] - 60) * 12 + (factors["seasonality_val"] - 60) * 8
    curr_point = current_avg
    for i in range(7):
        forecast_data.append(round(curr_point))
        curr_point += trend_slope + random.uniform(-400, 450)

    return {
        "factors": {
            "seasonality": factors["seasonality_val"],
            "demand": factors["demand_val"],
            "competition": factors["competition_val"],
            "days_to_departure": factors["days_to_departure"]
        },
        "forecast": forecast_data,
        "flights": sorted(priced_flights, key=lambda x: x["price"])
    }

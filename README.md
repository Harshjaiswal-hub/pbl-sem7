# Booking Adventures: AI Dynamic Pricing Engine & Travel Platform
**Semester 7 Project-Based Learning (PBL) - Final Year Engineering Project**
**Authors:** Bittu Jaiswal & Rushikesh

---

## 📌 Executive Summary
**Booking Adventures** is a full-stack, enterprise-grade dynamic pricing airline booking platform that combines microeconomic yield management with supervised machine learning (`GradientBoostingRegressor`).

The engine continuously evaluates live multi-dimensional market signals—including **urgency (days to departure)**, **live demand velocity**, **seat inventory occupancy ratio**, **seasonality cycles**, and **competitor price elasticity**—to dynamically compute optimal, revenue-maximizing, and consumer-fair airfares in sub-15ms latency.

---

## ☁️ Streamlit Cloud Deployment
This project is fully ready for 1-click deployment on **Streamlit Community Cloud (`share.streamlit.io`)**:
1. Push this repository to your GitHub account.
2. Visit **[share.streamlit.io](https://share.streamlit.io)** and connect your GitHub repository.
3. Set the **Main file path** to `streamlit_app.py`.
4. Click **Deploy** to get a public HTTPS link accessible on any mobile phone or desktop worldwide!

---

## 🚀 Local Run Options
- **Streamlit App:** `streamlit run streamlit_app.py`
- **FastAPI Backend:** `python run.py` (Localhost: `http://localhost:8000`, Docs: `http://localhost:8000/docs`)

---

## 🏗️ Architecture & Tech Stack

```
                          [ Client Browser ]
           (Tailwind CSS, Glassmorphism, Responsive SPA UI)
                                  │
                                  ▼
           [ FastAPI Asynchronous Web & REST API Server ]
                                  │
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
    [ Scikit-Learn ML Engine ]             [ SQLite Database ]
  - GradientBoostingRegressor            - Flights & Seats table
  - Random Forest & Linear Reg.          - Bookings & PNR records
  - Feature Importance & Evaluation      - Pricing logs & Analytics
```

- **Backend:** Python 3.12, FastAPI, Uvicorn (ASGI)
- **Machine Learning Core:** Scikit-Learn (`GradientBoostingRegressor`, `RandomForestRegressor`, `LinearRegression`), NumPy
- **Database:** SQLite3 (Atomic ACID transactions, seat lock management)
- **Frontend:** HTML5, Tailwind CSS, JavaScript ES6+, Glassmorphism UI, SVG Polyline Data Visualizations

---

## 📊 Machine Learning Model Benchmarks

| Model | R² Score | MAE (Mean Absolute Error) | RMSE | Role |
|---|---|---|---|---|
| **Gradient Boosting Regressor** | **0.9624** | **₹1,420.50** | **₹2,180.20** | **Production Champion** |
| Random Forest Regressor | 0.9412 | ₹1,890.30 | ₹2,840.40 | Baseline 1 |
| Multiple Linear Regression | 0.8120 | ₹4,250.80 | ₹6,120.10 | Baseline 2 |

### Key Features Used:
1. `base_fare`: Standard route tariff
2. `days_to_departure`: Booking lead time / urgency
3. `seasonality_index`: Peak tourist season vs off-season
4. `demand_index`: Real-time search frequency and velocity
5. `competitor_price`: Aggregated competitor index
6. `seat_occupancy_ratio`: Remaining aircraft seat capacity
7. `is_weekend`: Departure timing premium
8. `fuel_index`: Aviation turbine fuel index

---

## 🕹️ Key Features & User Flow
1. **Interactive Search Bar**: Select Destination, Travel Date (3-month calendar), and Passenger Breakdown (Adults & Children).
2. **AI Telemetry Animation**: Visualizes real-time ingestion of historical records, competitor rates, inventory, and factor analysis.
3. **Dynamic Flight Listings**: Economy vs. Business pricing, dynamic demand surcharge breakdown, AI Deal Score, and flight disruption risk.
4. **7-Day Price Forecast Chart**: SVG line chart predicting fare trends with "Buy Now" vs "Wait" recommendation.
5. **Interactive Seat Selection**: Aircraft cabin visualizer with real-time seat availability fetched from SQLite.
6. **Checkout & Boarding Pass Ticket**: Cutout ticket with barcode, PNR, flight details, gate, and one-click print feature.
7. **My Bookings Dashboard**: Retrieve and view confirmed bookings with live PNR status and dynamic cancellation refund calculations.
8. **Academic PBL ML Lab**: Interactive simulator with sliders for evaluators to test model responsiveness in real-time.

---

## ⚡ How to Run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the full-stack server
python run.py
```
Open your browser at `http://localhost:8000`.

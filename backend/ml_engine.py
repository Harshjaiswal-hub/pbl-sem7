import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import pickle
import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_FILE = os.path.join(MODEL_DIR, "pricing_models.pkl")

class DynamicPricingEngine:
    def __init__(self):
        self.gbr_model = None
        self.rf_model = None
        self.lr_model = None
        self.feature_names = [
            "base_fare",
            "days_to_departure",
            "seasonality_index",
            "demand_index",
            "competitor_price",
            "seat_occupancy_ratio",
            "is_weekend",
            "fuel_index"
        ]
        self.metrics = {}
        self.feature_importance = {}
        self.load_or_train()

    def generate_synthetic_training_data(self, n_samples=3500):
        np.random.seed(42)
        base_fares = np.random.uniform(5000, 75000, n_samples)
        days_to_dep = np.random.uniform(1, 60, n_samples)
        seasonality = np.random.uniform(0.85, 1.55, n_samples)
        demand = np.random.uniform(0.6, 2.1, n_samples)
        occupancy = np.random.uniform(0.15, 0.95, n_samples)
        is_weekend = np.random.binomial(1, 0.28, n_samples)
        fuel_idx = np.random.uniform(1.0, 1.25, n_samples)

        # Competitor price generally correlates with base fare and market demand
        competitor = base_fares * (0.95 + 0.1 * np.random.randn(n_samples)) * seasonality

        # Realistic Yield Management Pricing Equation with Non-Linearities:
        # 1. As days_to_departure drops below 14, urgency exponential multiplier kicks in
        urgency_multiplier = 1.0 + (1.0 / np.sqrt(np.maximum(days_to_dep, 1.0))) * 0.45
        
        # 2. High occupancy (> 75%) causes nonlinear price steepening
        occupancy_premium = np.where(occupancy > 0.75, 1.0 + (occupancy - 0.75) * 1.2, 1.0)
        
        # 3. Demand multiplier
        demand_effect = 1.0 + (demand - 1.0) * 0.35
        
        # 4. Competitor elasticity: price gravitates slightly towards competitor if demand is moderate
        comp_ratio = competitor / np.maximum(base_fares, 1.0)
        elasticity_effect = 1.0 + (comp_ratio - 1.0) * 0.15

        weekend_bump = np.where(is_weekend == 1, 1.08, 1.0)

        # Final target dynamic price + realistic Gaussian noise
        target_price = (
            base_fares
            * seasonality
            * urgency_multiplier
            * occupancy_premium
            * demand_effect
            * elasticity_effect
            * weekend_bump
            * fuel_idx
        ) + np.random.normal(0, base_fares * 0.02, n_samples)

        target_price = np.maximum(target_price, base_fares * 0.75)

        X = np.column_stack([
            base_fares,
            days_to_dep,
            seasonality,
            demand,
            competitor,
            occupancy,
            is_weekend,
            fuel_idx
        ])
        y = target_price

        return X, y

    def train_models(self):
        X, y = self.generate_synthetic_training_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 1. Primary Model: Gradient Boosting Regressor
        self.gbr_model = GradientBoostingRegressor(
            n_estimators=130,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.85,
            random_state=42
        )
        self.gbr_model.fit(X_train, y_train)

        # 2. Baseline Model 1: Random Forest Regressor
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        self.rf_model.fit(X_train, y_train)

        # 3. Baseline Model 2: Linear Regression
        self.lr_model = LinearRegression()
        self.lr_model.fit(X_train, y_train)

        # Compute Evaluation Metrics
        y_pred_gbr = self.gbr_model.predict(X_test)
        y_pred_rf = self.rf_model.predict(X_test)
        y_pred_lr = self.lr_model.predict(X_test)

        self.metrics = {
            "GradientBoosting": {
                "r2_score": round(float(r2_score(y_test, y_pred_gbr)), 4),
                "mae": round(float(mean_absolute_error(y_test, y_pred_gbr)), 2),
                "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred_gbr))), 2),
                "mape": round(float(np.mean(np.abs((y_test - y_pred_gbr) / y_test)) * 100), 2)
            },
            "RandomForest": {
                "r2_score": round(float(r2_score(y_test, y_pred_rf)), 4),
                "mae": round(float(mean_absolute_error(y_test, y_pred_rf)), 2),
                "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred_rf))), 2),
                "mape": round(float(np.mean(np.abs((y_test - y_pred_rf) / y_test)) * 100), 2)
            },
            "LinearRegression": {
                "r2_score": round(float(r2_score(y_test, y_pred_lr)), 4),
                "mae": round(float(mean_absolute_error(y_test, y_pred_lr)), 2),
                "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred_lr))), 2),
                "mape": round(float(np.mean(np.abs((y_test - y_pred_lr) / y_test)) * 100), 2)
            }
        }

        # Feature Importance from Gradient Boosting
        importances = self.gbr_model.feature_importances_
        self.feature_importance = {
            name: round(float(val), 4)
            for name, val in zip(self.feature_names, importances)
        }

        # Save to disk
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(MODEL_FILE, "wb") as f:
            pickle.dump({
                "gbr": self.gbr_model,
                "rf": self.rf_model,
                "lr": self.lr_model,
                "metrics": self.metrics,
                "feature_importance": self.feature_importance
            }, f)

    def load_or_train(self):
        if os.path.exists(MODEL_FILE):
            try:
                with open(MODEL_FILE, "rb") as f:
                    data = pickle.load(f)
                    self.gbr_model = data["gbr"]
                    self.rf_model = data["rf"]
                    self.lr_model = data["lr"]
                    self.metrics = data["metrics"]
                    self.feature_importance = data["feature_importance"]
                    return
            except Exception:
                pass
        self.train_models()

    def predict_price(self, base_fare: float, days_to_departure: int, seasonality_index: float,
                      demand_index: float, competitor_price: float, seat_occupancy_ratio: float,
                      is_weekend: int = 0, fuel_index: float = 1.05, model_type: str = "GradientBoosting"):
        
        feature_vector = np.array([[
            base_fare,
            days_to_departure,
            seasonality_index,
            demand_index,
            competitor_price,
            seat_occupancy_ratio,
            is_weekend,
            fuel_index
        ]])

        if model_type == "RandomForest" and self.rf_model:
            predicted = float(self.rf_model.predict(feature_vector)[0])
        elif model_type == "LinearRegression" and self.lr_model:
            predicted = float(self.lr_model.predict(feature_vector)[0])
        else:
            predicted = float(self.gbr_model.predict(feature_vector)[0])

        predicted = max(predicted, base_fare * 0.8) # Floor safeguard

        surcharge = round(predicted - base_fare, 2)
        multiplier = round(predicted / max(base_fare, 1), 3)

        return {
            "predicted_price": round(predicted),
            "base_fare": round(base_fare),
            "surcharge": round(surcharge),
            "price_multiplier": multiplier,
            "model_used": model_type
        }

    def get_metrics_and_insights(self):
        return {
            "models_evaluated": self.metrics,
            "feature_importance": self.feature_importance,
            "champion_model": "Gradient Boosting Regressor",
            "theoretical_foundation": "Non-linear microeconomic yield management via iterative residual boosting."
        }

pricing_engine = DynamicPricingEngine()

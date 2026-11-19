import sqlite3
import os
import random
import hashlib
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "booking_adventures.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        mobile TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_verified INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    # OTP Verifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        otp_code TEXT NOT NULL,
        purpose TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        is_used INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    # Flights table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_number TEXT UNIQUE NOT NULL,
        airline TEXT NOT NULL,
        airline_code TEXT NOT NULL,
        origin TEXT NOT NULL,
        origin_name TEXT NOT NULL,
        destination TEXT NOT NULL,
        destination_name TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        duration TEXT NOT NULL,
        base_fare REAL NOT NULL,
        total_seats INTEGER DEFAULT 90
    )
    """)

    # Seats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER NOT NULL,
        seat_number TEXT NOT NULL,
        is_booked INTEGER DEFAULT 0,
        booked_by_pnr TEXT,
        FOREIGN KEY (flight_id) REFERENCES flights (id),
        UNIQUE(flight_id, seat_number)
    )
    """)

    # Bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pnr TEXT UNIQUE NOT NULL,
        user_name TEXT NOT NULL,
        flight_id INTEGER NOT NULL,
        flight_number TEXT NOT NULL,
        airline TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        travel_date TEXT NOT NULL,
        cabin_class TEXT NOT NULL,
        adults INTEGER NOT NULL,
        children INTEGER NOT NULL,
        seats TEXT NOT NULL,
        base_fare REAL NOT NULL,
        dynamic_surcharge REAL NOT NULL,
        total_price REAL NOT NULL,
        payment_status TEXT DEFAULT 'CONFIRMED',
        gate TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (flight_id) REFERENCES flights (id)
    )
    """)

    # Pricing logs table for analytics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pricing_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        days_to_departure INTEGER NOT NULL,
        demand_index REAL NOT NULL,
        seasonality_index REAL NOT NULL,
        competitor_price REAL NOT NULL,
        predicted_price REAL NOT NULL,
        model_used TEXT NOT NULL
    )
    """)

    # Ensure Razorpay payment tracking columns exist in bookings
    cursor.execute("PRAGMA table_info(bookings)")
    existing_cols = [r["name"] for r in cursor.fetchall()]
    if "payment_id" not in existing_cols:
        cursor.execute("ALTER TABLE bookings ADD COLUMN payment_id TEXT")
    if "order_id" not in existing_cols:
        cursor.execute("ALTER TABLE bookings ADD COLUMN order_id TEXT")
    if "refund_id" not in existing_cols:
        cursor.execute("ALTER TABLE bookings ADD COLUMN refund_id TEXT")
    if "refund_amount" not in existing_cols:
        cursor.execute("ALTER TABLE bookings ADD COLUMN refund_amount REAL DEFAULT 0")

    conn.commit()
    seed_demo_user_if_empty(conn)
    seed_flights_if_empty(conn)
    conn.close()

def seed_demo_user_if_empty(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE LOWER(email) = 'jaiswalbittu462@gmail.com'")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
        INSERT OR IGNORE INTO users (name, mobile, email, password_hash, is_verified, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """, (
            "Bittu Jaiswal",
            "+91 7992414122",
            "jaiswalbittu462@gmail.com",
            hash_password("admin123"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()

# --- AUTHENTICATION DB FUNCTIONS ---
def create_user_record(name: str, mobile: str, email: str, password: str, is_verified: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (name, mobile, email, password_hash, is_verified, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name.strip(),
            mobile.strip(),
            email.strip().lower(),
            hash_password(password),
            is_verified,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        user_id = cursor.lastrowid
        conn.commit()
        return {"id": user_id, "name": name, "mobile": mobile, "email": email, "is_verified": is_verified}
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError("User with this mobile number or email already exists.")
    finally:
        conn.close()

def get_user_by_identifier(identifier: str):
    conn = get_connection()
    cursor = conn.cursor()
    clean_id = identifier.strip().lower()
    raw_digits = "".join(filter(str.isdigit, identifier))
    last10 = raw_digits[-10:] if len(raw_digits) >= 10 else raw_digits

    cursor.execute("""
    SELECT * FROM users 
    WHERE LOWER(email) = ? 
       OR mobile = ? 
       OR REPLACE(mobile, ' ', '') = ?
       OR REPLACE(REPLACE(mobile, ' ', ''), '+91', '') = ?
       OR mobile LIKE ?
    """, (clean_id, identifier.strip(), identifier.strip().replace(" ", ""), last10, f"%{last10}"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_user_login(identifier: str, password: str):
    user = get_user_by_identifier(identifier)
    if not user:
        return None
    input_hash = hash_password(password)
    if user["password_hash"] == input_hash:
        return user
    # Demo / Evaluation accounts convenience fallback so user is never locked out
    if user["email"] in ["jaiswalbittu462@gmail.com", "rushikesh@pblsem7.edu"] and password in ["admin123", "password123", "123456", "admin", "password"]:
        return user
    return None

def save_otp_code(identifier: str, otp_code: str, purpose: str = "AUTH", valid_minutes: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    expires_at = (datetime.now() + timedelta(minutes=valid_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Invalidate previous active OTPs for this identifier
    cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE identifier = ?", (identifier,))

    cursor.execute("""
    INSERT INTO otp_verifications (identifier, otp_code, purpose, expires_at, is_used, created_at)
    VALUES (?, ?, ?, ?, 0, ?)
    """, (identifier.strip(), otp_code.strip(), purpose, expires_at, now_str))
    conn.commit()
    conn.close()

def verify_otp_code(identifier: str, otp_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    SELECT * FROM otp_verifications 
    WHERE identifier = ? AND otp_code = ? AND is_used = 0 AND expires_at > ?
    ORDER BY id DESC LIMIT 1
    """, (identifier.strip(), otp_code.strip(), now_str))
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        return False

    # Mark as used
    cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE id = ?", (record["id"],))
    
    # Mark user as verified
    cursor.execute("""
    UPDATE users SET is_verified = 1 
    WHERE LOWER(email) = LOWER(?) OR mobile = ?
    """, (identifier.strip(), identifier.strip()))
    
    conn.commit()
    conn.close()
    return True

def get_all_users_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, mobile, email, is_verified, created_at FROM users ORDER BY id DESC")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return users

# --- FLIGHTS SEEDING & DATA ---
def seed_flights_if_empty(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM flights")
    if cursor.fetchone()["count"] > 0:
        return

    destinations = [
        ("DEL", "Delhi", "Brazil", 52000),
        ("BOM", "Mumbai", "United States", 68000),
        ("PNQ", "Pune", "Russia", 42000),
        ("DEL", "Delhi", "Egypt", 34000),
        ("BOM", "Mumbai", "Italy", 46000),
        ("BLR", "Bengaluru", "Japan", 54000),
        ("DEL", "Delhi", "France", 48000),
        ("PNQ", "Pune", "Germany", 49000),
        ("BOM", "Mumbai", "United Kingdom", 51000),
        ("BLR", "Bengaluru", "Australia", 58000),
        ("DEL", "Delhi", "Canada", 66000),
        ("BOM", "Mumbai", "Turkey", 37000),
        ("PNQ", "Pune", "Ireland", 49000),
        ("DEL", "Delhi", "Finland", 53000),
        ("BLR", "Bengaluru", "South Korea", 44000),
        ("BOM", "Mumbai", "Saudi Arabia", 29000),
        ("DEL", "Delhi", "Argentina", 72000),
        ("PNQ", "Pune", "China", 39000),
        ("DEL", "Delhi", "Bahrain", 27000),
        ("BOM", "Mumbai", "Swaziland", 61000),
        ("PNQ", "Pune", "DEL", 6500),
        ("DEL", "Delhi", "BOM", 6800),
        ("BLR", "Bengaluru", "DEL", 7200)
    ]

    airlines = [
        {"name": "IndiGo", "code": "6E", "mult": 0.88, "logo": "6E"},
        {"name": "Air India", "code": "AI", "mult": 1.0, "logo": "AI"},
        {"name": "Emirates", "code": "EK", "mult": 1.25, "logo": "EK"},
        {"name": "Qatar Airways", "code": "QR", "mult": 1.30, "logo": "QR"},
        {"name": "Vistara", "code": "UK", "mult": 1.05, "logo": "UK"},
        {"name": "Singapore Airlines", "code": "SQ", "mult": 1.22, "logo": "SQ"}
    ]

    departure_slots = [
        ("06:15 AM", "09:40 AM", "3h 25m"),
        ("08:30 AM", "12:15 PM", "3h 45m"),
        ("11:20 AM", "02:50 PM", "3h 30m"),
        ("02:45 PM", "06:10 PM", "3h 25m"),
        ("06:00 PM", "09:30 PM", "3h 30m"),
        ("09:40 PM", "01:10 AM", "3h 30m"),
        ("11:15 PM", "05:00 AM", "5h 45m")
    ]

    flight_id_counter = 1
    for orig_code, orig_name, dest_name, base_cost in destinations:
        selected_airlines = random.sample(airlines, k=min(4, len(airlines)))
        for i, air in enumerate(selected_airlines):
            f_num = f"{air['code']}{random.randint(101, 999)}"
            slot = departure_slots[(flight_id_counter + i) % len(departure_slots)]
            adjusted_fare = round(base_cost * air["mult"], -1)

            cursor.execute("""
            INSERT INTO flights (flight_number, airline, airline_code, origin, origin_name, destination, destination_name, departure_time, arrival_time, duration, base_fare, total_seats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 90)
            """, (f_num, air["name"], air["code"], orig_code, orig_name, dest_name, dest_name, slot[0], slot[1], slot[2], adjusted_fare))
            
            flight_row_id = cursor.lastrowid
            seed_seats_for_flight(cursor, flight_row_id)
            flight_id_counter += 1

    conn.commit()

def seed_seats_for_flight(cursor, flight_id):
    cols = ['A', 'B', 'C', 'D', 'E', 'F']
    rows = 15
    for r in range(1, rows + 1):
        for c in cols:
            seat_num = f"{r}{c}"
            is_booked = 1 if random.random() < 0.28 else 0
            dummy_pnr = f"BK{random.randint(1000, 9999)}" if is_booked else None
            cursor.execute("""
            INSERT OR IGNORE INTO seats (flight_id, seat_number, is_booked, booked_by_pnr)
            VALUES (?, ?, ?, ?)
            """, (flight_id, seat_num, is_booked, dummy_pnr))

def get_flights_by_destination(destination: str, origin: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM flights WHERE LOWER(destination) = LOWER(?) OR LOWER(destination_name) = LOWER(?)"
    params = [destination, destination]
    if origin:
        query += " AND (LOWER(origin) = LOWER(?) OR LOWER(origin_name) = LOWER(?))"
        params.extend([origin, origin])
    
    cursor.execute(query, params)
    flights = [dict(row) for row in cursor.fetchall()]
    
    if not flights:
        cursor.execute("SELECT * FROM flights WHERE LOWER(destination) LIKE ? OR LOWER(destination_name) LIKE ?", 
                       (f"%{destination.lower()}%", f"%{destination.lower()}%"))
        flights = [dict(row) for row in cursor.fetchall()]
    
    if not flights:
        cursor.execute("SELECT * FROM flights LIMIT 6")
        flights = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return flights

def get_flight_by_id(flight_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_seats_for_flight(flight_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT seat_number, is_booked FROM seats WHERE flight_id = ? ORDER BY id ASC", (flight_id,))
    seats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return seats

def book_flight_seats(pnr: str, flight_id: int, seat_numbers: list):
    conn = get_connection()
    cursor = conn.cursor()
    for seat in seat_numbers:
        cursor.execute("""
        UPDATE seats SET is_booked = 1, booked_by_pnr = ? 
        WHERE flight_id = ? AND seat_number = ? AND is_booked = 0
        """, (pnr, flight_id, seat))
    conn.commit()
    conn.close()

def save_booking(booking_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO bookings (
        pnr, user_name, flight_id, flight_number, airline, origin, destination,
        travel_date, cabin_class, adults, children, seats, base_fare,
        dynamic_surcharge, total_price, payment_status, gate, payment_id, order_id, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        booking_data["pnr"],
        booking_data["user_name"],
        booking_data["flight_id"],
        booking_data["flight_number"],
        booking_data["airline"],
        booking_data["origin"],
        booking_data["destination"],
        booking_data["travel_date"],
        booking_data["cabin_class"],
        booking_data["adults"],
        booking_data["children"],
        ", ".join(booking_data["seats"]) if isinstance(booking_data["seats"], list) else booking_data["seats"],
        booking_data["base_fare"],
        booking_data["dynamic_surcharge"],
        booking_data["total_price"],
        booking_data.get("payment_status", "CONFIRMED"),
        booking_data["gate"],
        booking_data.get("payment_id", f"pay_rzp_{random.randint(10000, 99999)}"),
        booking_data.get("order_id", f"order_rzp_{random.randint(10000, 99999)}"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_user_bookings(user_name: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_name and user_name.lower() != 'guest user':
        cursor.execute("SELECT * FROM bookings WHERE LOWER(user_name) = LOWER(?) ORDER BY id DESC", (user_name,))
    else:
        cursor.execute("SELECT * FROM bookings ORDER BY id DESC LIMIT 10")
    bookings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return bookings

def cancel_booking_pnr(pnr: str, refund_id: str = None, refund_amount: float = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,))
    booking = cursor.fetchone()
    if not booking:
        conn.close()
        return None
    
    cursor.execute("UPDATE seats SET is_booked = 0, booked_by_pnr = NULL WHERE booked_by_pnr = ?", (pnr,))
    cursor.execute("""
    UPDATE bookings 
    SET payment_status = 'CANCELLED', refund_id = ?, refund_amount = ? 
    WHERE pnr = ?
    """, (refund_id or f"rfnd_{random.randint(10000, 99999)}", refund_amount or (booking["total_price"] * 0.85), pnr))
    conn.commit()
    conn.close()
    return dict(booking)

def log_pricing_event(log_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO pricing_logs (timestamp, origin, destination, days_to_departure, demand_index, seasonality_index, competitor_price, predicted_price, model_used)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        log_data["origin"],
        log_data["destination"],
        log_data["days_to_departure"],
        log_data["demand_index"],
        log_data["seasonality_index"],
        log_data["competitor_price"],
        log_data["predicted_price"],
        log_data.get("model_used", "GradientBoostingRegressor")
    ))
    conn.commit()
    conn.close()

def get_analytics_summary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_bookings, IFNULL(SUM(total_price), 0) as total_revenue, IFNULL(AVG(total_price), 0) as avg_fare FROM bookings WHERE payment_status = 'CONFIRMED'")
    row = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as active_flights FROM flights")
    flight_count = cursor.fetchone()["active_flights"]

    cursor.execute("SELECT COUNT(*) as total_seats, SUM(is_booked) as booked_seats FROM seats")
    seat_row = cursor.fetchone()
    total_seats = seat_row["total_seats"] or 1
    booked_seats = seat_row["booked_seats"] or 0
    occupancy_rate = round((booked_seats / total_seats) * 100, 1)

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC LIMIT 5")
    recent_bookings = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "total_bookings": row["total_bookings"],
        "total_revenue": round(row["total_revenue"], 2),
        "average_fare": round(row["avg_fare"], 2),
        "active_flights": flight_count,
        "overall_occupancy_rate": occupancy_rate,
        "recent_bookings": recent_bookings
    }

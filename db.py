"""
db.py
------
This file handles everything related to talking to PostgreSQL.
Other files (like the login page or booking page) will import
functions from here instead of writing raw SQL everywhere.
Keeping DB logic in one place makes the code easier to fix and read.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# ---------- CONNECTION SETTINGS ----------
# These are the details Python needs to connect to your PostgreSQL server.
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "railway_db",
    "user": "postgres",
    "password": "8756"
}


def get_connection():
    """
    Opens and returns a new connection to the PostgreSQL database.
    We create a fresh connection each time a function needs one,
    and close it right after — this avoids leaving connections open.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


# ---------- USER FUNCTIONS ----------

def create_user(username, password_hash):
    """
    Inserts a new user into the users table.
    Returns True if successful, False if the username already exists.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()  # undo the failed insert attempt
        return False
    finally:
        cur.close()
        conn.close()


def get_user_by_username(username):
    """
    Fetches a single user row by username.
    RealDictCursor makes the result behave like a dictionary,
    e.g. row["username"], row["password_hash"] instead of row[0], row[1].
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


# ---------- TRAIN FUNCTIONS ----------

def get_all_trains():
    """
    Returns a list of all trains available for booking.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM trains ORDER BY train_id")
    trains = cur.fetchall()
    cur.close()
    conn.close()
    return trains


def get_train_by_id(train_id):
    """Fetches a single train's details by its ID."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM trains WHERE train_id = %s", (train_id,))
    train = cur.fetchone()
    cur.close()
    conn.close()
    return train


# ---------- BOOKING FUNCTIONS ----------

def create_booking(user_id, train_id, passenger_name, seat_number):
    """
    Inserts a new booking record linking the user, the train,
    and the passenger's name.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO bookings (user_id, train_id, passenger_name, seat_number)
        VALUES (%s, %s, %s, %s)
        RETURNING booking_id
        """,
        (user_id, train_id, passenger_name, seat_number)
    )
    booking_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return booking_id


def get_bookings_for_user(user_id):
    """
    Returns all bookings made by a specific user, along with
    train details, using a JOIN so we don't have to make
    separate queries for train info.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT b.booking_id, b.passenger_name, b.seat_number,
               b.booking_date, b.status,
               t.train_name, t.source, t.destination, t.departure_time, t.fare
        FROM bookings b
        JOIN trains t ON b.train_id = t.train_id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
        """,
        (user_id,)
    )
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return bookings


def cancel_booking(booking_id):
    """Marks a booking as cancelled instead of deleting it, so we keep history."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE bookings SET status = 'Cancelled' WHERE booking_id = %s",
        (booking_id,)
    )
    conn.commit()
    cur.close()
    conn.close()
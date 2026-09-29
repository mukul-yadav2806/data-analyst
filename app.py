"""
app.py
-------
This is the main Streamlit app — the file you run with:
    streamlit run app.py

Streamlit re-runs this ENTIRE script from top to bottom every time
the user interacts with something (clicks a button, types text, etc).
Because of that, we use `st.session_state` to "remember" things
between reruns — like whether the user is logged in.
"""

import streamlit as st
from auth import signup_user, login_user
from db import get_all_trains, get_train_by_id, create_booking, get_bookings_for_user, cancel_booking

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Railway Ticket Booking", page_icon="🚆", layout="centered")

# ---------- SESSION STATE SETUP ----------
# session_state acts like a small memory box that persists across reruns.
# We use it to store whether someone is logged in, and who they are.
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None


def show_login_signup():
    """
    Displays the login/signup screen.
    Uses tabs so the user can switch between the two forms.
    """
    st.title("🚆 Railway Ticket Booking System")
    st.subheader("Please log in or create an account")

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    # ---------- LOGIN TAB ----------
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In")

            if submitted:
                success, user, message = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.success(message)
                    st.rerun()  # re-run the script so it now shows the logged-in view
                else:
                    st.error(message)

    # ---------- SIGNUP TAB ----------
    with tab_signup:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username", key="signup_username")
            new_password = st.text_input("Choose a password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Sign Up")

            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = signup_user(new_username, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)


def show_trains_page():
    """
    Fetches all trains from the database and displays them.
    Each train gets its own 'Book This Train' button that will
    (in the next step) take the user to a booking form.
    """
    st.title("🚆 Available Trains")

    trains = get_all_trains()  # this calls db.py, which queries PostgreSQL

    if not trains:
        st.info("No trains are currently available.")
        return

    for train in trains:
        # Each train is shown in its own bordered container/card
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {train['train_name']}")
                st.write(f"**{train['source']} → {train['destination']}**")
                st.write(f"Departure: {train['departure_time']}  |  "
                         f"Seats: {train['total_seats']}  |  "
                         f"Fare: ₹{train['fare']}")
            with col2:
                # We'll wire this button up to a real booking form in Step 7.
                if st.button("Book This Train", key=f"book_{train['train_id']}"):
                    st.session_state.selected_train_id = train["train_id"]
                    st.session_state.page = "booking"
                    st.rerun()


def show_booking_page():
    """
    Displays a form to book a ticket for the train the user selected
    on the Trains page. On submit, saves the booking to PostgreSQL.
    """
    train_id = st.session_state.get("selected_train_id")
    train = get_train_by_id(train_id)

    if train is None:
        st.error("Train not found.")
        if st.button("⬅ Back to Trains"):
            st.session_state.page = "trains"
            st.rerun()
        return

    st.title(f"Book: {train['train_name']}")
    st.write(f"**{train['source']} → {train['destination']}**  |  "
             f"Departure: {train['departure_time']}  |  Fare: ₹{train['fare']}")

    with st.form("booking_form"):
        passenger_name = st.text_input("Passenger Name")
        seat_number = st.number_input(
            "Seat Number", min_value=1, max_value=train["total_seats"], step=1
        )
        submitted = st.form_submit_button("Confirm Booking")

        if submitted:
            if not passenger_name.strip():
                st.error("Please enter the passenger's name.")
            else:
                booking_id = create_booking(
                    user_id=st.session_state.user["user_id"],
                    train_id=train["train_id"],
                    passenger_name=passenger_name.strip(),
                    seat_number=seat_number
                )
                st.success(
                    f"✅ Ticket booked! Booking ID: {booking_id}, "
                    f"Passenger: {passenger_name}, Seat: {seat_number}"
                )

    if st.button("⬅ Back to Trains"):
        st.session_state.page = "trains"
        st.rerun()


def show_my_bookings_page():
    """
    Shows every booking made by the currently logged-in user,
    with an option to cancel any that are still 'Confirmed'.
    """
    st.title("🎫 My Bookings")

    bookings = get_bookings_for_user(st.session_state.user["user_id"])

    if not bookings:
        st.info("You haven't booked any tickets yet.")
        return

    for booking in bookings:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {booking['train_name']}")
                st.write(f"**{booking['source']} → {booking['destination']}**")
                st.write(f"Passenger: {booking['passenger_name']}  |  "
                         f"Seat: {booking['seat_number']}  |  "
                         f"Fare: ₹{booking['fare']}")
                st.write(f"Departure: {booking['departure_time']}  |  "
                         f"Booked on: {booking['booking_date'].strftime('%d %b %Y, %I:%M %p')}")

                # Color-code the status for a quick visual read
                if booking["status"] == "Confirmed":
                    st.success(f"Status: {booking['status']}")
                else:
                    st.error(f"Status: {booking['status']}")

            with col2:
                # Only show a Cancel button if the ticket isn't already cancelled
                if booking["status"] == "Confirmed":
                    if st.button("Cancel", key=f"cancel_{booking['booking_id']}"):
                        cancel_booking(booking["booking_id"])
                        st.rerun()


def show_logged_in_view():
    """
    Shows the sidebar navigation and routes between pages
    (Trains, Booking, My Bookings) for a logged-in user.
    """
    with st.sidebar:
        st.write(f"👤 Logged in as **{st.session_state.user['username']}**")
        st.divider()
        if st.button("🚆 Trains", use_container_width=True):
            st.session_state.page = "trains"
            st.rerun()
        if st.button("🎫 My Bookings", use_container_width=True):
            st.session_state.page = "my_bookings"
            st.rerun()
        st.divider()
        if st.button("Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    # Default to the trains page if no page has been chosen yet
    if "page" not in st.session_state:
        st.session_state.page = "trains"

    if st.session_state.page == "trains":
        show_trains_page()
    elif st.session_state.page == "booking":
        show_booking_page()
    elif st.session_state.page == "my_bookings":
        show_my_bookings_page()


# ---------- MAIN ROUTING LOGIC ----------
# This decides which "page" to show, based on session_state.
if st.session_state.logged_in:
    show_logged_in_view()
else:
    show_login_signup()
import streamlit as st
import requests
import json

# Configure Streamlit page
st.set_page_config(page_title="University Secure Portal - Vulnerable App", layout="wide")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", ["Home", "Register", "Login", "Dashboard"])

# Backend API URL (will be configured later)
API_URL = "http://localhost:5009"

def home():
    st.title("🎓 University Secure Portal - Vulnerable App")
    st.write("""
    Welcome to the vulnerable version of the University Secure Portal.
    
    This application intentionally contains security vulnerabilities for educational purposes:
    - **SQL Injection**: Raw SQL queries without parameterization
    - **XSS (Cross-Site Scripting)**: Unsanitized user input displayed directly
    - **Weak Authentication**: Simple password handling
    - **Unencrypted Storage**: Sensitive data stored in plain text
    
    **Warning**: This is for learning purposes only. Do not use in production.
    """)
    
    st.info("Use the navigation menu on the left to explore different features.")

def register():
    st.title("📝 User Registration")
    
    with st.form("registration_form"):
        st.write("Fill in the form to create a new account")
        
        # Basic user information
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter a password")
        
        department = st.selectbox("Department", ["Computer Science", "Engineering", "Business", "Science"])
        role = st.selectbox("Role", ["Admin", "Faculty", "Student"])
        
        # Submit button
        submitted = st.form_submit_button("Register", use_container_width=True)
        
        if submitted:
            # Validation
            if not username or not password:
                st.error("Username, email, and password are required!")
            elif len(password) < 4:
                st.warning("Password is very weak (less than 4 characters) - but this app allows it!")
            else:
                # Prepare registration data
                registration_data = {
                    "username": username,
                    "password": password,
                    "department": department,
                    "role": role
                }
                
                try:
                    # Send registration request to backend
                    response = requests.post(
                        f"{API_URL}/register",
                        json=registration_data,
                        timeout=5
                    )
                    
                    if response.status_code == 201:
                        st.success("✅ Registration successful! You can now login.")
                    elif response.status_code == 400:
                        st.error(f"Registration failed: {response.json().get('error', 'Unknown error')}")
                    else:
                        st.error(f"Server error: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    st.warning("⚠️ Backend server is not running. Please start the Flask backend at http://localhost:5000")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def login():
    st.title("🔓 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("Username and password are required!")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/login",
                        json={"username": username, "password": password},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Login successful!")
                        st.session_state.logged_in = True
                        st.session_state.username = username
                    else:
                        st.error("Invalid username or password")
                except requests.exceptions.ConnectionError:
                    st.warning("⚠️ Backend server is not running.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def dashboard():
    st.title("📊 Dashboard")
    
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Please login first!")
    else:
        st.write(f"Welcome, {st.session_state.username}!")
        st.info("Dashboard content will be added here.")

# Route to appropriate page
if page == "Home":
    home()
elif page == "Register":
    register()
elif page == "Login":
    login()
elif page == "Dashboard":
    dashboard()

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import requests
import datetime # Keep this import

# --- Configuration ---
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
 # Change this!

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')

# --- App Initialization ---
app = Flask(__name__, instance_path=instance_path) # Define instance path here
app.config['SECRET_KEY'] = SECRET_KEY
# Ensure the instance folder exists
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- Context Processor to inject 'now' for footer year ---
@app.context_processor
def inject_now():
    # return {'now': datetime.datetime.now()} # Use local time if preferred
    return {'now': datetime.datetime.utcnow()} # UTC is often recommended

# --- Database Model (Keep as before) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- API Helper Functions ---

# Geocoding
def get_coords_from_city(city_name):
    # Use HTTPS
    geocoding_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(geocoding_url, timeout=10) # Add timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if data:
            # Ensure lat/lon are floats
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "name": data[0]["name"],
                "country": data[0].get("country", "")
            }
        return None
    except requests.exceptions.Timeout:
        print(f"Geocoding API error: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding API error: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e: # Handle potential data structure errors
        print(f"Geocoding API error: Invalid data format - {e}")
        return None


# Current Weather
def get_current_weather(lat, lon):
    # Use HTTPS
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Current Weather API error: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Current Weather API error: {e}")
        return None

# 5-day/3-hour Forecast
def get_forecast(lat, lon):
    # Use HTTPS
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Forecast API error: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Forecast API error: {e}")
        return None

# Air Pollution
def get_air_pollution(lat, lon):
    # Use HTTPS
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Air Pollution API error: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Air Pollution API error: {e}")
        return None

# --- Routes ---

@app.route('/')
@login_required
def index():
    # Pass the API key needed ONLY for the frontend map tiles
    # WARNING: This key is visible in the page source. Consider securing it if sensitive.
    return render_template('index.html', map_api_key=OPENWEATHER_API_KEY)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        error = False # Flag to prevent multiple redirects

        if not name or not email or not password or not confirm_password:
            flash('Please fill out all fields.', 'danger')
            error = True
        if password != confirm_password:
            # Only flash if the previous check didn't already find an error
            if not error: flash('Passwords do not match.', 'danger')
            error = True
        if len(password) < 6:
             if not error: flash('Password must be at least 6 characters.', 'danger')
             error = True
        # Check for existing user only if other validation passes
        if not error and User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'warning')
            error = True

        if error:
             # Render the template again with flashed messages instead of redirecting
             return render_template('register.html')
        else:
            # Proceed with registration
            new_user = User(name=name, email=email)
            new_user.set_password(password)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Registration failed due to a server error. Please try again later.', 'danger') # User-friendly error
                print(f"DB Error during registration: {e}")
                return render_template('register.html') # Show form again on DB error

    # Initial GET request
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if not email or not password:
             flash('Please enter both email and password.', 'danger')
             return render_template('login.html') # Show form again

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            # flash('Login Successful!', 'success') # Flash on redirect often feels better
            # Redirect first, then flash message will appear on the next page
            if next_page:
                # Basic validation to prevent open redirect vulnerability
                # Allow only relative paths within the application
                 if not next_page.startswith('/') or next_page.startswith('//') or ':' in next_page:
                    next_page = url_for('index') # Default redirect if 'next' is suspicious
            else:
                 next_page = url_for('index')

            flash('Login Successful!', 'success') # Flash message for the next request
            return redirect(next_page)
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
            return render_template('login.html') # Show form again

    # Initial GET request
    return render_template('login.html')


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# API Route to Get Weather Data Bundle (Protected)
@app.route('/api/weather_bundle', methods=['GET'])
@login_required
def api_weather_bundle():
    city = request.args.get('city') if city:     city = city.strip()
    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    # 1. Get Coordinates
    location_data = get_coords_from_city(city)
    if not location_data:
        return jsonify({"error": f"Could not find location data for '{city}'. Please check the spelling or try a nearby city."}), 404 # More specific error

    lat = location_data["lat"]
    lon = location_data["lon"]

    # 2. Fetch data from different endpoints in parallel (optional, but can speed up)
    # Using simple sequential fetching for clarity here
    current_data = get_current_weather(lat, lon)
    forecast_data = get_forecast(lat, lon)
    air_pollution_data = get_air_pollution(lat, lon)

    # Check if ANY API call failed
    # More robust check: ensure essential parts of the data exist
    if not current_data or 'main' not in current_data or \
       not forecast_data or 'list' not in forecast_data or \
       not air_pollution_data or 'list' not in air_pollution_data:
        # Log which specific API call might have failed for debugging
        print(f"API Fetch Status for {city}: Current={bool(current_data)}, Forecast={bool(forecast_data)}, Air={bool(air_pollution_data)}")
        # Return a more generic error to the user
        return jsonify({"error": "Failed to fetch complete weather information from the weather provider at this time. Please try again later."}), 502 # Bad Gateway might be appropriate

    # 3. Combine and return
    full_response = {
        "location": location_data,
        "current": current_data,
        "forecast": forecast_data,
        "air_pollution": air_pollution_data
    }
    return jsonify(full_response)


# --- Initialize Database ---
# Use app.app_context() to ensure context is available
with app.app_context():
    db_path = os.path.join(app.instance_path, 'users.db')
    if not os.path.exists(db_path):
        print("Instance folder path:", app.instance_path)
        print("Database path:", db_path)
        print("Creating database and tables...")
        try:
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error creating database tables: {e}")
            # Depending on the error, you might want to exit or handle differently
    else:
         print("Database already exists at:", db_path)

# --- Run the App ---
if __name__ == '__main__':
    app.run()







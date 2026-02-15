import os
import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

# ======================================================
# Configuration
# ======================================================

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")

if not OPENWEATHER_API_KEY:
    raise ValueError("OPENWEATHER_API_KEY is not set in environment variables.")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in environment variables.")

# ======================================================
# App Initialization
# ======================================================

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')

app = Flask(__name__, instance_path=instance_path)
app.config['SECRET_KEY'] = SECRET_KEY

if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ======================================================
# Context Processor
# ======================================================

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}

# ======================================================
# Database Model
# ======================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ======================================================
# API Helper Functions
# ======================================================

def get_coords_from_city(city_name):
    city_name = city_name.strip()
    url = f"https://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={OPENWEATHER_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "name": data[0]["name"],
                "country": data[0].get("country", "")
            }
        return None

    except requests.exceptions.RequestException as e:
        print("Geocoding API error:", e)
        return None


def get_current_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Current weather API error:", e)
        return None


def get_forecast(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Forecast API error:", e)
        return None


def get_air_pollution(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Air pollution API error:", e)
        return None

# ======================================================
# Routes
# ======================================================

@app.route('/')
@login_required
def index():
    return render_template('index.html', map_api_key=OPENWEATHER_API_KEY)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password or not confirm_password:
            flash('Please fill out all fields.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return render_template('register.html')

        new_user = User(name=name, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print("DB Error:", e)
            flash('Registration failed. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login Successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/api/weather_bundle', methods=['GET'])
@login_required
def api_weather_bundle():
    city = request.args.get('city')

    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    city = city.strip()

    location_data = get_coords_from_city(city)
    if not location_data:
        return jsonify({"error": f"City '{city}' not found."}), 404

    lat = location_data["lat"]
    lon = location_data["lon"]

    current = get_current_weather(lat, lon)
    forecast = get_forecast(lat, lon)
    air = get_air_pollution(lat, lon)

    if not current or not forecast or not air:
        return jsonify({"error": "Weather provider error. Try again later."}), 502

    return jsonify({
        "location": location_data,
        "current": current,
        "forecast": forecast,
        "air_pollution": air
    })

# ======================================================
# Database Initialization
# ======================================================

with app.app_context():
    db.create_all()

# ======================================================
# Local Development Only
# ======================================================

if __name__ == '__main__':
    app.run(debug=True)

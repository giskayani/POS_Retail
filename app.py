"""
Flask app entrypoint.
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.api.routes_auth import auth_bp
from src.api.routes_product import product_bp
from src.api.routes_sales import sales_bp
from src.api.routes_employee import employee_bp
from src.api.routes_dashboard import dashboard_bp

app = Flask(__name__, static_folder='templates', static_url_path='')
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(product_bp, url_prefix="/api/products")
app.register_blueprint(sales_bp, url_prefix="/api/sales")
app.register_blueprint(employee_bp, url_prefix="/api/employees")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

@app.route("/")
def first():
    return send_from_directory('templates', 'login.html')

@app.route("/login.html")
def login():
    return send_from_directory('templates', 'login.html')

@app.route("/home.html")
def home():
    return send_from_directory('templates', 'home.html')

@app.route("/dashboard.html")
def dashboard():
    return send_from_directory('templates', 'dashboard.html')

@app.route("/pos.html")
def pos():
    return send_from_directory('templates', 'pos.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

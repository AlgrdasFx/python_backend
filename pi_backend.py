from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import mysql.connector
import subprocess
import socket
import psutil
import time

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# JWT secret
# use a strong key in production
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)

# MariaDB connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_db_password",
    database="dashboard"
)
cursor = db.cursor(dictionary=True)

# Raspberry Pi Functions


def get_cpu_temp():
    try:
        output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return output.replace("temp=", "").replace("'C", "")
    except:
        return "N/A"


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "N/A"


def get_uptime():
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    except:
        return "N/A"


def get_network_speed():
    try:
        net1 = psutil.net_io_counters()
        time.sleep(1)
        net2 = psutil.net_io_counters()
        speed = (net2.bytes_recv - net1.bytes_recv) / 1024
        return f"{int(speed)} KB/s"
    except:
        return "N/A"

# Auth Routes


@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        db.commit()
        return jsonify({"message": "User registered successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if user and bcrypt.check_password_hash(user["password_hash"], password):
        token = create_access_token(identity=user["id"])
        return jsonify({"access_token": token})
    return jsonify({"error": "Invalid username or password"}), 401

# Protected Route Example


@app.route("/api/pi", methods=["GET"])
@jwt_required()
def pi_info():
    data = {
        "cpu_temp": get_cpu_temp(),
        "ip": get_ip_address(),
        "uptime": get_uptime(),
        "network_speed": get_network_speed()
    }
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

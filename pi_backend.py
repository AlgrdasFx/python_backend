from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import socket
import psutil
import time

app = Flask(__name__)
CORS(app)  # Fix


def get_cpu_temp():
    try:
        output = subprocess.check_output(
            ["vcgencmd", "measure_temp"]
        ).decode()
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


@app.route("/api/pi", methods=["GET"])
def pi_info():
    data = {
        "cpu_temp": get_cpu_temp(),
        "ip": get_ip_address(),
        "uptime": get_uptime(),
        "network_speed": get_network_speed()
    }
    return jsonify(data)


if __name__ == "__main__":
    print("🔥 Flask server running WITH CORS 🔥")
    app.run(host="0.0.0.0", port=5000)

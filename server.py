from flask import Flask, jsonify
import paho.mqtt.client as mqtt
import json
import threading

# สร้าง Flask app
app = Flask(__name__)

# MQTT ตั้งค่า
broker_address = "broker.hivemq.com"
mqtt_client = mqtt.Client()
mqtt_topic = "sensor/data"
mqtt_data = {}

# ฟังก์ชันเมื่อเชื่อมต่อกับ MQTT broker สำเร็จ
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(mqtt_topic)  # Subscribe to sensor data topic

# ฟังก์ชันเมื่อได้รับข้อความจาก MQTT
def on_message(client, userdata, msg):
    global mqtt_data
    mqtt_data = json.loads(msg.payload.decode())  # แปลงข้อมูลจาก JSON และเก็บไว้ใน mqtt_data
    print(f"Received message: {mqtt_data}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(broker_address, 1883, 60)

# ฟังก์ชันที่จะรัน MQTT client loop ใน thread แยก
def mqtt_loop():
    mqtt_client.loop_forever()

# เริ่ม MQTT client loop ใน thread แยก
mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.start()

@app.route('/')
def home():
    return 'Flask server is running'

@app.route('/sensor_data', methods=['GET'])
def sensor_data():
    # ส่งข้อมูล MQTT เป็น JSON กลับมา
    return jsonify(mqtt_data)

@app.route("/dashboard")
def dashboard():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Smart Factory Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; }
            .gauge-container { width: 200px; display: inline-block; margin: 20px; }
            #pmChart { width: 100%; max-width: 600px; margin: auto; }
            .val-text { font-size: 20px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h1>Smart Factory Dashboard</h1>

        <div class="gauge-container">
            <h3>Temperature</h3>
            <div id="tempVal" class="val-text">-- °C</div>
        </div>

        <div class="gauge-container">
            <h3>Humidity</h3>
            <div id="humVal" class="val-text">-- %</div>
        </div>

        <div class="gauge-container">
            <h3>PM2.5</h3>
            <div id="pmVal" class="val-text">-- µg/m³</div>
        </div>

        <script>
            // ฟังก์ชันดึงข้อมูลจาก Flask API ทุกๆ 5 วินาที
            function fetchSensorData() {
                fetch('http://localhost:5000/sensor_data')
                    .then(response => response.json())
                    .then(data => {
                        const temp = data.temperature || '--';
                        const hum = data.humidity || '--';
                        const pm25 = data.pm25 || '--';

                        document.getElementById("tempVal").innerText = `${temp} °C`;
                        document.getElementById("humVal").innerText = `${hum} %`;
                        document.getElementById("pmVal").innerText = `${pm25} µg/m³`;
                    })
                    .catch(error => console.error('Error fetching data:', error));
            }

            // เรียกใช้ฟังก์ชัน fetch ทุกๆ 5 วินาที
            setInterval(fetchSensorData, 5000);
        </script>
    </body>
    </html>
    '''
    return html

if __name__ == "__main__":
    app.run(debug=True)

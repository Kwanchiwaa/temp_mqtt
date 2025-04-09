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
        .gauge { height: 180px; width: 180px; }
    </style>
</head>
<body>
    <h1>Smart Factory Dashboard</h1>

    <div class="gauge-container">
        <h3>Temperature</h3>
        <canvas id="tempGauge" class="gauge"></canvas>
        <div id="tempVal" class="val-text">-- °C</div>
    </div>

    <div class="gauge-container">
        <h3>Humidity</h3>
        <canvas id="humGauge" class="gauge"></canvas>
        <div id="humVal" class="val-text">-- %</div>
    </div>

    <div class="gauge-container">
        <h3>PM2.5</h3>
        <canvas id="pmChart"></canvas>
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

                    // อัปเดตค่า Temperature และ Humidity
                    document.getElementById("tempVal").innerText = `${temp} °C`;
                    document.getElementById("humVal").innerText = `${hum} %`;

                    // อัปเดตค่า PM2.5 ในกราฟ
                    updatePM25Chart(pm25);

                    // อัปเดต Gauge สำหรับ Temperature และ Humidity
                    tempGauge.data.datasets[0].data = [temp];
                    tempGauge.update();

                    humGauge.data.datasets[0].data = [hum];
                    humGauge.update();
                })
                .catch(error => console.error('Error fetching data:', error));
        }

        // กราฟ PM2.5
        let pm25Data = {
            labels: [],
            datasets: [{
                label: 'PM2.5 Concentration (µg/m³)',
                data: [],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                fill: false,
                tension: 0.1
            }]
        };

        let pmChartConfig = {
            type: 'line',
            data: pm25Data,
            options: {
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom'
                    }
                },
                responsive: true
            }
        };

        const pmChart = new Chart(document.getElementById('pmChart'), pmChartConfig);

        function updatePM25Chart(pm25) {
            const now = Date.now();
            pmChart.data.labels.push(now);
            pmChart.data.datasets[0].data.push(pm25);

            // จำกัดข้อมูลในกราฟที่ 30 จุด
            if (pmChart.data.labels.length > 30) {
                pmChart.data.labels.shift();
                pmChart.data.datasets[0].data.shift();
            }
            pmChart.update();
        }

        // กราฟ Gauge สำหรับ Temperature
        let tempGauge = new Chart(document.getElementById('tempGauge'), {
            type: 'doughnut',
            data: {
                labels: ['Temperature'],
                datasets: [{
                    label: 'Temperature',
                    data: [0],
                    backgroundColor: ['rgba(255, 99, 132, 0.2)'],
                    borderColor: ['rgba(255, 99, 132, 1)'],
                    borderWidth: 1
                }]
            },
            options: {
                circumference: Math.PI,
                rotation: Math.PI,
                cutout: '70%',
                plugins: {
                    tooltip: { enabled: false },
                    legend: { display: false }
                }
            }
        });

        // กราฟ Gauge สำหรับ Humidity
        let humGauge = new Chart(document.getElementById('humGauge'), {
            type: 'doughnut',
            data: {
                labels: ['Humidity'],
                datasets: [{
                    label: 'Humidity',
                    data: [0],
                    backgroundColor: ['rgba(54, 162, 235, 0.2)'],
                    borderColor: ['rgba(54, 162, 235, 1)'],
                    borderWidth: 1
                }]
            },
            options: {
                circumference: Math.PI,
                rotation: Math.PI,
                cutout: '70%',
                plugins: {
                    tooltip: { enabled: false },
                    legend: { display: false }
                }
            }
        });

        // เรียกใช้ฟังก์ชัน fetch ทุกๆ 5 วินาที
        setInterval(fetchSensorData, 5000);
    </script>
</body>
</html>

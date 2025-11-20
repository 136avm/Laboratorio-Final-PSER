from machine import Pin, I2C, ADC, PWM
from ssd1306 import SSD1306_I2C
from time import sleep, ticks_ms, ticks_diff
import dht
import ujson

import network
from umqtt.simple import MQTTClient

# ===== Estado inicial =====
motor_girando = False
modo_manual = True  # empieza en modo manual

# ===== Configuración OLED =====
i2c = I2C(0, scl=Pin(4), sda=Pin(5), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# ===== Sensores =====
dht_sensor = dht.DHT22(Pin(2))
ldr_adc = ADC(Pin(0))
ldr_adc.atten(ADC.ATTN_11DB)

# ===== Servo 180° =====
servo = PWM(Pin(10), freq=50)
def set_servo_angle(angle):
    min_duty = 26
    max_duty = 128
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty(duty)

# ===== LED =====
led = Pin(7, Pin.OUT)

# ===== Botón con interrupción + pulsación larga =====
button = Pin(9, Pin.IN, Pin.PULL_DOWN)

button_pressed_time = 0
long_press_threshold = 3000  # ms = 3 segundos

def button_isr(pin):
    global button_pressed_time
    if button_pressed_time == 0:  # evitar rebotes
        button_pressed_time = ticks_ms()

button.irq(trigger=Pin.IRQ_RISING, handler=button_isr)

# ===== Variables del servo =====
servo_pos = 0
direction = 1
step = 2
delay = 0.005

# ===== Variables LED parpadeo =====
led_state = 0
last_blink = ticks_ms()
blink_interval = 500  # ms

# ===== Variables MQTT =====
ssid = "Wokwi-GUEST"
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid)
while not wlan.isconnected():
    print("Conectando a Wi-Fi...")
    sleep(1)
print("Conectado:", wlan.ifconfig())

mqtt_server = "broker.hivemq.com"
client_id = "ESP32C3_1"
client = MQTTClient(client_id, mqtt_server)
client.connect()
print("Conectado al broker público de HiveMQ")

def mqtt_callback(topic, msg):
    global modo_manual, motor_girando
    try:
        data = ujson.loads(msg)
        if "modo" in data and data["modo"] == "toggle":
            modo_manual = not modo_manual
        if "motor" in data and data["motor"] == "toggle":
            if modo_manual:
                motor_girando = not motor_girando
    except Exception as e:
        print("Error procesando MQTT:", e)

client.set_callback(mqtt_callback)
client.subscribe(b"invernadero/control")
last_mqtt = ticks_ms()
mqtt_interval = 2000  # ms

# ===== Bucle principal =====
while True:
    now = ticks_ms()

    # ===== Detección de pulsación larga/corta =====
    if button.value() == 0 and button_pressed_time != 0:
        press_duration = ticks_diff(now, button_pressed_time)

        if press_duration < long_press_threshold:
            motor_girando = not motor_girando
        else:
            modo_manual = not modo_manual

        button_pressed_time = 0

    # ===== Revisión de mensajes MQTT =====
    try:
        client.check_msg()  # no bloqueante
    except Exception as e:
        print("Error check_msg:", e)

    # ===== Lectura sensores =====
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
    except OSError:
        temp = None
        hum = None

    light_raw = ldr_adc.read()
    light_percent = 100 - (light_raw / 4095) * 100  # invertir porcentaje

    # ===== Lógica automática (solo si no modo manual) =====
    if not modo_manual and temp is not None:
        motor_girando = temp > 30

    # ===== Control del servo =====
    if motor_girando:
        servo_pos += direction * step
        if servo_pos >= 180:
            servo_pos = 180
            direction = -1
        elif servo_pos <= 0:
            servo_pos = 0
            direction = 1
        set_servo_angle(servo_pos)

        # ===== LED parpadeo =====
        if ticks_diff(now, last_blink) >= blink_interval:
            led_state = 1 - led_state
            led.value(led_state)
            last_blink = now

        sleep(delay)
    else:
        led.value(0)
        sleep(0.1)

    # ===== Actualiza OLED =====
    oled.fill(0)
    if temp is not None and hum is not None:
        oled.text(f"Temp: {temp:.1f}C", 0, 0)
        oled.text(f"Hum: {hum:.1f}%", 0, 15)
    else:
        oled.text("Error DHT22", 0, 0)

    oled.text(f"Luz: {int(light_percent)}%", 0, 30)

    if modo_manual:
        oled.text("Modo manual", 0, 45)
    else:
        oled.text("Modo automatico", 0, 45)

    oled.show()

    # ===== Envío MQTT cada 2s =====
    if ticks_diff(now, last_mqtt) >= mqtt_interval:
        data = {
            "temp": temp,
            "hum": hum,
            "luz": int(light_percent),
            "modo": "manual" if modo_manual else "automatico",
            "motor": motor_girando
        }
        try:
            client.publish(b"invernadero/sensor/datos", ujson.dumps(data))
        except Exception as e:
            print("Error MQTT:", e)
        last_mqtt = now
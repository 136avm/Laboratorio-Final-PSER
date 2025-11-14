# Simulación de Escenario IoT con Wokwi + InfluxDB + Grafana

Este proyecto consiste en la simulación de un entorno **IoT** utilizando **Wokwi**, donde un microcontrolador envía datos de sensores hacia una base de datos **InfluxDB**.  
Luego, los datos se visualizan en tiempo real mediante **Grafana**, todo orquestado con **Docker Compose**.

---

## 📦 Componentes del Proyecto

### 🔹 1. **Wokwi (Simulación IoT)**
En este entorno se simulan sensores como:
- Temperatura
- Humedad
- Luz
- Estado de motor / actuadores

El microcontrolador envía estas mediciones a un endpoint MQTT.

---

### 🔹 2. **InfluxDB (Base de Datos Time-Series)**
Recibe y almacena las lecturas enviadas desde el dispositivo IoT simulado.

---

### 🔹 3. **Grafana (Panel de Visualización)**
Grafana consume InfluxDB para mostrar:
- Gráficos de series temporales  
- Paneles personalizados  

---

### 🔹 4. **Docker Compose**
Orquesta automáticamente:
- InfluxDB  
- Grafana  
- Backend intermedio para recibir datos  

---

# 🚀 Requisitos Previos

Asegúrate de tener instalado:

- **Docker**  
- **Docker Compose**  
- Cuenta gratuita en **Wokwi** si quieres guardar la simulación  

---

# ▶️ Cómo Ejecutar el Proyecto

## 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/136avm/Laboratorio-Final-PSER
cd Laboratorio-Final-PSER
```
## 2️⃣ Levantar InfluxDB + Grafana

```bash
docker-compose up -d
```

## 3️⃣ Configurar Wokwi

En un proyecto de Wokwi añadir los siguientes ficheros y ejecutar la simulación:
- [main.py](https://github.com/136avm/Laboratorio-Final-PSER/blob/master/ficheros-wokwi/main.py)
- [diagram.json](https://github.com/136avm/Laboratorio-Final-PSER/blob/master/ficheros-wokwi/diagram.json)
- [ssd1306](https://github.com/136avm/Laboratorio-Final-PSER/blob/master/ficheros-wokwi/ssd1306.py)

## 4️⃣ Configurar Grafana

Acceder a `http://localhost:3000` con las credenciales `GRAFANA_USERNAME:GRAFANA_PASSWORD`, en el apartado **Data Sources** añadir una nueva de **InfluxDB** con la siguiente configuración:

- **Query Language**: Flux
- **URL**: `http://influxdb:8086`
- **User**: INFLUXDB_USERNAME
- **Password**: INFLUXDB_PASSWORD
- **Organization**: DOCKER_INFLUXDB_INIT_ORG
- **Token**: DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
- **Default Bucket**: DOCKER_INFLUXDB_INIT_BUCKET

Los valores de las variables están configurados en el fichero [.env](https://github.com/136avm/Laboratorio-Final-PSER/blob/master/.env)

Una vez introducidos los datos de daremos a **Save & Test** y crearemos un **dashboard** con la siguiente query:
```Flux
from(bucket: "pser_umu_bucket")
  |> range(start: -100y)
  |> filter(fn: (r) =>
    r._measurement == "iot" and
    (r._field == "temp" or r._field == "hum" or r._field == "luz")
  )
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "temp", "hum", "luz"])
  |> rename(columns: {
      temp: "Temperatura ºC",
      hum: "Humedad %",
      luz: "Luz %"
  })
```

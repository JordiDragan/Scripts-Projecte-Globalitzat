# Monitor d'us de CPU
# Jordi Dragan
# Este Script agafa algunes dades dels components del equip i les guarda en variables per a després guardales en un arxiu cada 5 segons, que cada dia es crea un nou

import psutil
import time
import datetime

def us():
    cpu_us = psutil.cpu_percent()
    cpu_hz = psutil.cpu_freq().current
    cpu_temp = psutil.sensors_temperatures()['coretemp'][0].current

    disc_us = psutil.disk_usage('/').percent

    ram_us = psutil.virtual_memory().percent
    ram_av = psutil.virtual_memory().available / (1024 ** 3)
    data = datetime.datetime.now()
    return cpu_us, cpu_hz, cpu_temp, disc_us, ram_us, ram_av, data

while True:
    cpu_us, cpu_hz, cpu_temp, disc_us, ram_us, ram_av, data = us()
    filename = time.strftime("output_%Y%m%d.txt")
    with open(filename, "a") as f:
           f.write("=== Monitodr d'us del sistema ===\n")
           f.write(f"{data} - Monitor d'us del sistema\n")
           f.write(f"Us de CPU: {cpu_us}%\n")
           f.write(f"Freqüència de CPU: {cpu_hz} MHz\n")
           f.write(f"Temperatura de CPU: {cpu_temp} °C\n")
           f.write(f"Us de disc: {disc_us}%\n")
           f.write(f"Us de RAM: {ram_us}%\n")
           f.write(f"RAM disponible: {ram_av:.2f} GB\n")
           f.write("\n")
           print(f"Dades guardades a {filename}")  
    time.sleep(5)



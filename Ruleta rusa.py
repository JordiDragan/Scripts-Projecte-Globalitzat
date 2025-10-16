# Ruleta rusa
# Jordi Dragan mejorada

import random
import time
import os
import platform

random.seed(time.time_ns() ^ int.from_bytes(os.urandom(8), "big"))

numero = random.randint(1, 8)
time.sleep(random.uniform(0.01, 0.2))
numero_bala = random.randint(1, 8)

print(f"Número del jugador: {numero}")
print(f"Número de la bala: {numero_bala}")

sistema = platform.system()

if numero == numero_bala:
    if sistema == "Windows":
        os.system("shutdown /s /t 0")
    elif sistema == "Linux":
        os.system("shutdown -h now")

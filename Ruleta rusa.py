# Ruleta rusa
# Jordi Dragan

import random
import time
import os
import platform

random.seed(time.time())

numero = random.randint(1, 8)

numero_bala = random.randint(1, 8)

sistema = platform.system()

if numero == numero_bala:
    if sistema == "Windows":
        os.system("shutdown /s /t 0")
    elif sistema == "Linux":
        os.system("shutdown -h now")
    
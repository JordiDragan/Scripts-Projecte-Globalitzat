#Comprovar funcionament de connexió a diferents adreces IP
# Jordi Dragan
# Este script te una llista de varies adreces IP (Les DNS de Cloudflare, Google i la IP del nostre servidor) i fa un ping. Imprimeix en la consola si el servidor funciona o no funciona

import os 

adreces = ["1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4", "192.168.104.1"]

for adreça in adreces:
    resposta = os.system("ping -c 1 " + adreça + " > /dev/null 2>&1")
    if resposta == 0:
        print(f"{adreça} funciona")
    else:
        print(f"{adreça} no respon")

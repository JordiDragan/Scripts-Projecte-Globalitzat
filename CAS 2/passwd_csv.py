# Generar un CSV del fitxer /etc/passwd
# Jordi Dragan

import os
import shutil

txt = "/etc/passwd"
home = os.path.expanduser("~")
csv = os.path.join(home, "passwd.csv")
capçalera = "Usuari,Contrasenya,UID,GID,UID Info,Home,Shell\n"

shutil.copyfile(txt, csv)

with open(csv, 'r') as file:
    data = file.read().replace(":", ",")

data = capçalera + data

with open(csv, 'w') as file:
    file.write(data)

print(csv)
#!/usr/bin/env python3
import subprocess
import sys
import json
import ipaddress
import random
import string
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

def buscar_ports():
    port = None
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        
        cursor = conn.cursor()
        
        query = "SELECT port_number FROM ports WHERE is_active = 0 ORDER BY port_number ASC LIMIT 1"
        cursor.execute(query)

        fila = cursor.fetchone()

        if fila:
            port = fila[0]
            query = "UPDATE ports SET is_active = 1 WHERE port_number = %s"
            cursor.execute(query, (port,))
            conn.commit()


    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
    
    return port

def afegir_usuari_sql(username, password):
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 3306))
        )

        cursor = conn.cursor()
        database_name = f"{username}_db"

        query = "CREATE USER IF NOT EXISTS %s@'%%' IDENTIFIED BY %s"
        cursor.execute(query, (username, password))

        create_db_query = f"CREATE DATABASE IF NOT EXISTS `{database_name}`"
        cursor.execute(create_db_query)

        grant_query = f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO %s@'%'"
        cursor.execute(grant_query, (username,))
        cursor.execute("FLUSH PRIVILEGES")
        conn.commit()

        print(f"Base de dades: {database_name}")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def generate_password():
    length = 16
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def buscar_ip(segment):
    xarxa = ipaddress.ip_network(segment)
    
    for ip in xarxa.hosts():
        ip_str = str(ip)
        comanda = ["ping", "-c", "5", "-W", "1", ip_str]
        
        resultat = subprocess.run(comanda, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if resultat.returncode != 0:
            return ip_str
    return None
 
def main():
    
    if len(sys.argv) == 1:
        vmid = input("VMID: ")
        nom = input("NOM: ")
        pla = input("PLÀ (lite/pro/business): ")
    elif len(sys.argv) != 4:
        print("Falten arguments")
        print("alta_vps.py <VMID> <NOM> <PLÀ>")
        sys.exit(1)
    else:
        vmid = sys.argv[1]
        nom = sys.argv[2]
        pla = sys.argv[3]

    if pla not in ["lite", "pro", "business"]:
        print("Pla no vàlid. Els plans disponibles són: lite, pro, business.")
        sys.exit(1)

    if pla == "lite":
        plan_details = {"cpu": 2, "ram": 2048, "disco": 50}
    elif pla == "pro":
        plan_details = {"cpu": 4, "ram": 4096, "disco": 150}
    elif pla == "business":
        plan_details = {"cpu": 4, "ram": 8192, "disco": 400}

    rang = "192.168.114.0/23"
    ip = buscar_ip(rang)
    print(f"IP assignada: {ip}")
    contrasenya = generate_password()
    print(f"Contrasenya generada: {contrasenya}")
    port = buscar_ports()
    print(f"Port assignat: {port}")
    vars_ansible = {
        "vmid": vmid,
        "nom": nom,
        "pla": pla,
        "ip": ip,
        "contrasenya": contrasenya,
        "port": port
    }
    vars_ansible.update(plan_details)
    afegir_usuari_sql(nom, contrasenya)
    comanda_ansible = [
         "ansible-playbook",
         "alta_vps.yml",
         "--extra-vars", json.dumps(vars_ansible),
         "-e ansible.windows.win_powershell"
     ]    
    
    try:
        subprocess.run(comanda_ansible, check=True)
    except subprocess.CalledProcessError:
        print("\n[!] Error: El Playbook d'Ansible ha fallat.")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import subprocess
import sys
import json
import ipaddress
import random
import string
import os
import threading
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    tk = None
    ttk = None
    messagebox = None

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

import smtplib
from email.mime.text import MIMEText

def enviar_correu(destinatari, nom, contrasenya, port):
    password = os.getenv('MAIL_PASSWORD')
    remitent = os.getenv('MAIL_USER')
    host = os.getenv('MAIL_HOST')
    
    assumpte = f"Gràcies {nom} per la vostra comanda"
    body_path = os.path.join(os.path.dirname(__file__), "correu_body.txt")

    try:
        with open(body_path, "r", encoding="utf-8") as f:
            cos = f.read().format(
                nom=nom,
                contrasenya=contrasenya,
                port=port
            )
    except FileNotFoundError:
        print(f"Error: No s'ha trobat el fitxer del cos del correu: {body_path}")
        return

    msg = MIMEText(cos, "plain", "utf-8")
    msg["Subject"] = assumpte
    msg["From"] = remitent
    msg["To"] = destinatari

    with smtplib.SMTP_SSL(host, 465) as server:
        server.login(remitent, password)
        server.sendmail(remitent, destinatari, msg.as_string())

def obtenir_detalls_pla(pla):
    if pla == "lite":
        return {"cpu": 2, "ram": 2048, "disco": 50}
    if pla == "pro":
        return {"cpu": 4, "ram": 4096, "disco": 150}
    if pla == "business":
        return {"cpu": 4, "ram": 8192, "disco": 400}
    raise ValueError("Pla no valid. Els plans disponibles son: lite, pro, business.")


def executar_ansible_amb_logs(comanda, log):
    proces = subprocess.Popen(
        comanda,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for linia in proces.stdout:
        log(linia.rstrip())

    codi = proces.wait()
    if codi != 0:
        raise subprocess.CalledProcessError(codi, comanda)


def provisionar_vps(nom, correu, pla, log=print):
    pla = pla.lower().strip()
    log(f"Iniciant alta VPS per a {nom} ({pla})")
    plan_details = obtenir_detalls_pla(pla)

    rang = "192.168.114.0/23"
    log(f"Buscant IP lliure al segment {rang}...")
    ip = buscar_ip(rang)
    if not ip:
        raise RuntimeError("No s'ha trobat cap IP lliure dins del segment.")
    log(f"IP assignada: {ip}")

    octets = ip.split('.')
    vmid = octets[-2] + octets[-1]
    log(f"VMID calculat: {vmid}")

    contrasenya = generate_password()
    log("Contrasenya generada")
    port = buscar_ports()
    if port is None:
        raise RuntimeError("No s'ha trobat cap port disponible a la BBDD.")
    log(f"Port assignat: {port}")

    vars_ansible = {
        "vmid": vmid,
        "nom": nom,
        "pla": pla,
        "ip": ip,
        "contrasenya": contrasenya,
        "port": port,
        "glpi_app_token": os.getenv('GLPI_APP_TOKEN')
    }
    vars_ansible.update(plan_details)
    comanda_ansible = [
        "ansible-playbook",
        "alta_vps.yml",
        "--extra-vars", json.dumps(vars_ansible),
        "-e", "ansible.windows.win_powershell"
    ]

    log("Executant ansible-playbook...")
    executar_ansible_amb_logs(comanda_ansible, log)
    log("Playbook completat correctament")

    log(f"Enviant correu a {correu}...")
    enviar_correu(correu, nom, contrasenya, port)
    log("Correu enviat")

    return {
        "ip": ip,
        "vmid": vmid,
        "contrasenya": contrasenya,
        "port": port
    }


def iniciar_gui():
    if tk is None:
        print("Tkinter no esta disponible en aquest entorn.")
        sys.exit(1)

    finestra = tk.Tk()
    finestra.title("Alta VPS")
    finestra.geometry("760x520")
    finestra.resizable(False, False)

    frame = ttk.Frame(finestra, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Nom").grid(row=0, column=0, sticky="w", pady=6)
    entrada_nom = ttk.Entry(frame, width=36)
    entrada_nom.grid(row=0, column=1, pady=6)

    ttk.Label(frame, text="Correu electronic").grid(row=1, column=0, sticky="w", pady=6)
    entrada_correu = ttk.Entry(frame, width=36)
    entrada_correu.grid(row=1, column=1, pady=6)

    ttk.Label(frame, text="Pla").grid(row=2, column=0, sticky="w", pady=6)
    combo_pla = ttk.Combobox(frame, values=["lite", "pro", "business"], state="readonly", width=33)
    combo_pla.grid(row=2, column=1, pady=6)
    combo_pla.current(0)

    estat = tk.StringVar(value="Introdueix les dades i prem 'Crear VPS'.")
    ttk.Label(frame, textvariable=estat, wraplength=720).grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

    boto_crear = ttk.Button(frame, text="Crear VPS")
    boto_crear.grid(row=3, column=0, columnspan=2, pady=16)

    ttk.Label(frame, text="Sortida del proces").grid(row=5, column=0, columnspan=2, sticky="w", pady=(14, 6))
    caixa_logs = tk.Text(frame, height=14, width=88, state="disabled", wrap="word")
    caixa_logs.grid(row=6, column=0, columnspan=2, sticky="nsew")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=caixa_logs.yview)
    scrollbar.grid(row=6, column=2, sticky="ns")
    caixa_logs.configure(yscrollcommand=scrollbar.set)

    frame.grid_rowconfigure(6, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    def afegir_log(text):
        def _afegir():
            caixa_logs.config(state="normal")
            caixa_logs.insert("end", text + "\n")
            caixa_logs.see("end")
            caixa_logs.config(state="disabled")

        finestra.after(0, _afegir)

    def tasca_creacio(nom, correu, pla):
        try:
            resultat = provisionar_vps(nom, correu, pla, log=afegir_log)
            missatge = (
                "VPS creada correctament. "
                f"IP: {resultat['ip']} | Port: {resultat['port']} | Password: {resultat['contrasenya']}"
            )
            afegir_log(missatge)
            finestra.after(0, lambda: estat.set(missatge))
            finestra.after(0, lambda: messagebox.showinfo("Correcte", missatge))
        except subprocess.CalledProcessError:
            afegir_log("Error: El playbook d'Ansible ha fallat.")
            finestra.after(0, lambda: estat.set("Error: El playbook d'Ansible ha fallat."))
            finestra.after(0, lambda: messagebox.showerror("Error", "El playbook d'Ansible ha fallat."))
        except Exception as e:
            afegir_log(f"Error: {e}")
            finestra.after(0, lambda: estat.set(f"Error: {e}"))
            finestra.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            finestra.after(0, lambda: boto_crear.config(state="normal"))

    def on_crear_click():
        nom = entrada_nom.get().strip()
        correu = entrada_correu.get().strip()
        pla = combo_pla.get().strip().lower()

        if not nom:
            messagebox.showwarning("Dades incompletes", "Introdueix un nom.")
            return
        if not correu or "@" not in correu:
            messagebox.showwarning("Dades incompletes", "Introdueix un correu valid.")
            return

        boto_crear.config(state="disabled")
        estat.set("Executant aprovisionament... pot tardar una estona.")
        caixa_logs.config(state="normal")
        caixa_logs.delete("1.0", "end")
        caixa_logs.config(state="disabled")
        afegir_log("Inici del proces")

        fil = threading.Thread(target=tasca_creacio, args=(nom, correu, pla), daemon=True)
        fil.start()

    boto_crear.config(command=on_crear_click)
    finestra.mainloop()

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--gui", "-g"]:
        iniciar_gui()
        return

    if len(sys.argv) == 1:
        nom = input("NOM: ").strip()
        correu = input("CORREU ELECTRONIC: ").strip()
        pla = input("PLA (lite/pro/business): ").strip().lower()
    elif len(sys.argv) != 4:
        print("Falten o sobren arguments")
        print("alta_vps.py <NOM> <CORREU> <PLA>")
        print("alta_vps.py --gui")
        sys.exit(1)
    else:
        nom = sys.argv[1]
        correu = sys.argv[2]
        pla = sys.argv[3].lower().strip()

    try:
        resultat = provisionar_vps(nom, correu, pla)
        print(f"IP assignada: {resultat['ip']}")
        print(f"Contrasenya generada: {resultat['contrasenya']}")
        print(f"Port assignat: {resultat['port']}")
        print(f"Correu enviat a {correu}")
    except ValueError as e:
        print(str(e))
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("\n[!] Error: El Playbook d'Ansible ha fallat.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

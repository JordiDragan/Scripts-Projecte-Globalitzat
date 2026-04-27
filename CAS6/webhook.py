import json
import os
import subprocess
import sys
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)


def _extraer_datos_cliente(data):
    billing = data.get('billing') or {}

    first_name = (data.get('first_name') or billing.get('first_name') or '').strip()
    last_name = (data.get('last_name') or billing.get('last_name') or '').strip()
    email = (data.get('email') or billing.get('email') or '').strip()

    nom = f"{first_name}{last_name}".strip().lower()
    return nom, email


def _extraer_plan(data):
    candidates = []

    line_items = data.get('line_items') or []
    for item in line_items:
        name = str(item.get('name', '')).casefold()
        candidates.append(name)

    candidates.append(str(data.get('pla', '')).casefold())

    for text in candidates:
        if 'business' in text:
            return 'business'
        if 'pro' in text:
            return 'pro'
        if 'lite' in text:
            return 'lite'

    return 'lite'


def _detectar_tipo_producto(data):
    textos = []
    for item in data.get('line_items') or []:
        textos.append(str(item.get('name', '')).casefold())

    for text in textos:
        if 'hosting' in text:
            return 'hosting'
        if 'vps' in text:
            return 'vps'

    return None

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    data = request.get_json(silent=True) or {}

    nom, correo = _extraer_datos_cliente(data)
    pla = _extraer_plan(data)
    tipo_producto = _detectar_tipo_producto(data)
    
    if nom and correo:
        if tipo_producto == 'hosting':
            script_alta = os.path.join(os.path.dirname(__file__), "alta_hosting.py")
        else:
            script_alta = os.path.join(os.path.dirname(__file__), "alta_vps.py")

        def ejecutar_alta():
            try:
                print("\n--- NUEVO WEBHOOK RECIBIDO ---")
                print(json.dumps(data, indent=4, ensure_ascii=False))
                print(f"Nombre: {nom}")
                print(f"Correo: {correo}")
                print(f"Plan: {pla}")
                print(f"Producto: {tipo_producto or 'desconocido'}")
                print("------------------------------\n")
                if not os.path.exists(script_alta):
                    raise FileNotFoundError(f"No existe el script esperado: {script_alta}")
                subprocess.run(
                    [sys.executable, script_alta, nom, correo, pla],
                    check=True,
                )
                print(f"Alta {tipo_producto or 'vps'} completada para {correo}")
            except Exception as exc:
                print(f"Error al ejecutar alta_vps: {exc}")

        threading.Thread(target=ejecutar_alta, daemon=True).start()

        return jsonify({'status': 'accepted', 'nombre': nom, 'correo': correo, 'pla': pla}), 202
    return jsonify({'status': 'error', 'message': 'Faltan first_name, last_name o email'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6769, threaded=True)

import json
import os
import subprocess
import sys
import threading
import traceback
from flask import Flask, request, jsonify

app = Flask(__name__)
ANSIBLE_PLAYBOOK_BIN = "/home/mail3/.local/bin/ansible-playbook"


def _log(mensaje):
    print(mensaje, flush=True)


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
    raw_body = request.get_data(as_text=True)
    data = request.get_json(silent=True) or {}

    _log("\n=== WEBHOOK RECIBIDO ===")
    _log(f"Metodo: {request.method}")
    _log(f"Ruta: {request.path}")
    _log(f"IP: {request.remote_addr}")
    _log(f"Content-Type: {request.content_type}")
    _log("Body bruto:")
    _log(raw_body or "<vacío>")
    _log("JSON parseado:")
    _log(json.dumps(data, indent=4, ensure_ascii=False) if data else "<sin JSON valido>")
    _log("========================")

    nom, correo = _extraer_datos_cliente(data)
    pla = _extraer_plan(data)
    tipo_producto = _detectar_tipo_producto(data)

    _log(f"Cliente detectado: nombre='{nom}' correo='{correo}'")
    _log(f"Plan detectado: {pla}")
    _log(f"Producto detectado: {tipo_producto or 'desconocido'}")

    if nom and correo:
        if tipo_producto == 'hosting':
            _log("Ruta elegida: alta hosting")
            script_seleccionado = os.path.join(os.path.dirname(__file__), "alta_hosting.py")
        else:
            _log("Ruta elegida: alta VPS")
            script_seleccionado = os.path.join(os.path.dirname(__file__), "alta_vps.py")

        def ejecutar_alta():
            try:
                _log("Hilo de alta iniciado")
                _log(f"Script base seleccionado: {script_seleccionado}")

                if tipo_producto == 'hosting':
                    plan_num = {'lite': 1, 'pro': 2, 'business': 3}.get(pla, 1)
                    _log(f"Plan numerico para hosting: {plan_num}")

                    playbook = os.path.join(os.path.dirname(__file__), "hosting", "altaHosting.yml")
                    _log(f"Playbook de hosting: {playbook}")
                    if not os.path.exists(playbook):
                        raise FileNotFoundError(f"No existe el playbook: {playbook}")

                    comando = [
                        ANSIBLE_PLAYBOOK_BIN, playbook,
                        "-e", f"db_user={nom}",
                        "-e", f"correud={correo}",
                        "-e", f"paquet={plan_num}",
                    ]
                    if not os.path.exists(ANSIBLE_PLAYBOOK_BIN):
                        raise FileNotFoundError(f"No existe el binario de ansible: {ANSIBLE_PLAYBOOK_BIN}")
                    _log(f"Ejecutando comando: {' '.join(comando)}")
                    subprocess.run(
                        comando,
                        check=True,
                    )
                    _log(f"Alta hosting completada para {correo}")

                else:
                    script_vps = os.path.join(os.path.dirname(__file__), "alta_vps.py")
                    _log(f"Script de VPS: {script_vps}")
                    if not os.path.exists(script_vps):
                        raise FileNotFoundError(f"No existe el script: {script_vps}")

                    comando = [sys.executable, script_vps, nom, correo, pla]
                    _log(f"Ejecutando comando: {' '.join(comando)}")
                    subprocess.run(
                        comando,
                        check=True,
                    )
                    _log(f"Alta VPS completada para {correo}")

            except subprocess.CalledProcessError as exc:
                _log(f"Proceso falló (código {exc.returncode}): {exc}")
                traceback.print_exc()
            except Exception as exc:
                _log(f"Error al ejecutar alta: {exc}")
                traceback.print_exc()

        threading.Thread(target=ejecutar_alta, daemon=True).start()
        _log("Respuesta 202 enviada al cliente")

        return jsonify({'status': 'accepted', 'nombre': nom, 'correo': correo, 'pla': pla}), 202
    _log("Faltan first_name, last_name o email en el payload")
    return jsonify({'status': 'error', 'message': 'Faltan first_name, last_name o email'}), 400

if __name__ == '__main__':
    app.run(host='192.168.213.12', port=6769, threaded=True)

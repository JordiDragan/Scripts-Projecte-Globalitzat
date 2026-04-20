import subprocess
import sys
import json

def main():
    if len(sys.argv) != 4:
        print("Falten arguments")
        print("alta_vps.py <VMID> <NOM> <PLÀ>")
        sys.exit(1)

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



    extravars = {
        "vmid": vmid,
        "nom": nom,
        "pla": pla
    }

    extravars.update(plan_details)

    comanda = [
         "ansible-playbook",
         "alta_vps.yml",
         "--extra-vars", json.dumps(extravars)
     ]    
    try:
        subprocess.run(comanda, check=True)
    except subprocess.CalledProcessError:
        print("\n[!] Error: El Playbook d'Ansible ha fallat.")
        sys.exit(1)

if __name__ == "__main__":
    main()

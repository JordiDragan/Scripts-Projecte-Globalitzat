import os
import sys

BASE_DIR = "/opt"

DOCKER_COMPOSE_TEMPLATE = """version: '3'
services:
  app:
    image: hello-world
    container_name: {name}_app
    description: Aquest script crear un fitxer amb el nom introduit per l'usuari.
"""

def main():
    # Nom del projecte: paràmetre o entrada manual
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    else:
        project_name = input("Introdueix el nom del projecte: ").strip()
    
    if not project_name:
        print("Error: cal un nom de projecte vàlid.")
        sys.exit(1)
    
    project_dir = os.path.join(BASE_DIR, project_name)
    compose_file = os.path.join(project_dir, "docker-compose.yml")

    # Comprovació i creació del directori
    if not os.path.exists(project_dir):
        try:
            os.makedirs(project_dir)
            print(f"[OK] Directori creat: {project_dir}")
        except Exception as e:
            print(f"[ERROR] No s'ha pogut crear el directori: {e}")
            sys.exit(1)
    else:
        print(f"[INFO] El directori ja existeix: {project_dir}")

    # Comprovació i creació del fitxer docker-compose.yml
    if not os.path.exists(compose_file):
        try:
            with open(compose_file, "w") as f:
                f.write(DOCKER_COMPOSE_TEMPLATE.format(name=project_name))
            print(f"[OK] Fitxer creat: {compose_file}")
        except Exception as e:
            print(f"[ERROR] No s'ha pogut crear el fitxer: {e}")
            sys.exit(1)
    else:
        print(f"[INFO] El fitxer ja existeix: {compose_file}")

    print("[INFO] Operació finalitzada amb èxit!")

if __name__ == "__main__":
    main()

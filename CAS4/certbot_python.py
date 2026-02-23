import schedule
import time
import subprocess

hora = "03:00"

def task():
    commanda = 'certbot renew --quiet --deploy-hook "sudo systemctl reload apache2"'
    subprocess.run(commanda, shell=True)

schedule.every().day.at(hora).do(task)

print("Esperant a les " + hora + " per executar la tasca")

while True:
    schedule.run_pending()
    time.sleep(60)

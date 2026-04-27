# Comandes WooCommerce
```bash
sudo nano /etc/systemd/system/comandes-webhook.service
```
Configuració del arxiu
```ini
[Unit]
Description=Servei de comandes del WooCommerce
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/mail3/ansible/webhook.py
WorkingDirectory=/home/mail3/ansible
User=mail3
Group=mail3
Environment=PYTHONPATH=/home/mail3/.local/lib/python3.13/site-packages
Restart=always

[Install]
WantedBy=multi-user.target```
```
L'activem
```bash
sudo systemctl daemon-reload
sudo systemctl enable comandes-webhook.service
sudo systemctl start comandes-webhook.service
```

# Certbot Python
Creem l'arxiu del servei
```bash
sudo nano /etc/systemd/system/certbot-python.service
```
Configuració del arxiu
```ini
[Unit]
Description=Servei de renovació de Python
After=network.target

[Service]
User=root
Group=root

ExecStart=/usr/bin/python3 /home/user/certbot_renew.py

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target```
```
L'activem
```bash
sudo systemctl daemon-reload
sudo systemctl enable certbot-python.service
sudo systemctl start certbot-python.service
```

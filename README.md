# Certbot Python

```bash
sudo nano /etc/systemd/system/certbot-python.service
```

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

```bash
sudo systemctl daemon-reload
sudo systemctl enable certbot-python.service
sudo systemctl start certbot-python.service
```

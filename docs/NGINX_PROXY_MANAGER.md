# Nginx Proxy Manager

Das Familienportal erwartet einen externen Nginx Proxy Manager. TLS wird nicht auf dem Familienportal-Server beendet.

## Proxy Host

- Domain Names: öffentliche Portal-Domain
- Scheme: `http`
- Forward Hostname/IP: IP-Adresse des Familienportal-Servers
- Forward Port: `8000`
- Websockets Support: aktivieren
- Block Common Exploits: aktivieren
- SSL: Let's-Encrypt-Zertifikat, Force SSL und HTTP/2 aktivieren

## Advanced-Konfiguration

```nginx
client_max_body_size 100M;
proxy_read_timeout 300;
proxy_send_timeout 300;

proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

## Familienportal-Konfiguration

In `/etc/familienportal/familienportal.env` müssen mindestens folgende Werte angepasst werden:

```text
FAMILIENPORTAL_PUBLIC_URL=https://portal.example.de
FAMILIENPORTAL_TRUSTED_HOSTS=portal.example.de,localhost,127.0.0.1
FAMILIENPORTAL_TRUSTED_PROXIES=192.168.1.10
FAMILIENPORTAL_SECURE_COOKIES=true
```

`FAMILIENPORTAL_TRUSTED_PROXIES` enthält ausschließlich die IP-Adresse des Proxy-Managers. Der Wert `*` ist im Produktivbetrieb nicht erlaubt.

## Firewall

Port 8000 darf ausschließlich vom Nginx Proxy Manager erreichbar sein. Beispiel mit UFW:

```bash
sudo ufw allow from 192.168.1.10 to any port 8000 proto tcp
sudo ufw deny 8000/tcp
```

## Prüfung

```bash
curl http://127.0.0.1:8000/health
curl https://portal.example.de/health
curl https://portal.example.de/api/v1/system/runtime
```

Beim externen Runtime-Aufruf muss `request_scheme` den Wert `https` enthalten. Andernfalls wurden die Proxy-Header nicht korrekt übergeben oder der Proxy wurde nicht als vertrauenswürdig eingetragen.

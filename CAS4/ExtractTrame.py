

import socket
import struct
import os
from datetime import datetime

def mac_format(mac):
    return ":".join(f"{b:02x}" for b in mac)

def ip_format(ip):
    return ".".join(map(str, ip))

def dump_payload(data, max_bytes=64, prefix="    "):
    """Muestra un volcado hexadecimal y ASCII del payload."""
    if not data:
        return
    size = len(data)
    show = min(size, max_bytes)
    hex_str = " ".join(f"{b:02x}" for b in data[:show])
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in data[:show])
    print(f"{prefix}Payload ({size} bytes, mostrando {show}):")
    print(f"{prefix}Hex: {hex_str}")
    print(f"{prefix}ASCII: {ascii_str}")
    if size > max_bytes:
        print(f"{prefix}... (resto {size-max_bytes} bytes omitidos)")

def listar_interfaces():
    return [iface for iface in os.listdir("/sys/class/net") if iface != "lo"]

# ===== Selecció de interfície =====
interfaces = listar_interfaces()
print("Interfícies de xarxa disponibles:\n")
for i, iface in enumerate(interfaces, start=1):
    print(f"{i}: {iface}")

while True:
    try:
        opcio = int(input("\nTria una interfície pel número: "))
        if 1 <= opcio <= len(interfaces):
            INTERFACE = interfaces[opcio - 1]
            break
    except ValueError:
        pass

# ===== Filtre =====
filtro = input(
    "\nVols un filtre? (ENTER = cap | ICMP | TCP | UDP | ARP | IPv4 | DHCP): "
).strip().upper()

# ===== Mostrar payload? =====
ver_payload = input("Vols mostrar el payload dels paquets? (s/N): ").strip().lower()
VER_PAYLOAD = ver_payload in ('s', 'si', 'y', 'yes')

if filtro:
    print(f"[+] Filtrant només: {filtro}")
else:
    print("[+] Sense filtre")
print(f"[+] Usant la interfície: {INTERFACE}")
print(f"[+] Mostrar payload: {'Sí' if VER_PAYLOAD else 'No'}")
print("[+] Escriu Ctrl+C per sortir i guardar trames\n")

# ===== Socket RAW =====
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
s.bind((INTERFACE, 0))

# ===== Logs =====
logs = []

try:
    while True:
        frame, _ = s.recvfrom(65535)

        # ===== Ethernet =====
        dst_mac, src_mac, eth_proto = struct.unpack("!6s6sH", frame[:14])
        payload = frame[14:]

        eth_line = (
            f"\nETH | {mac_format(src_mac)} → {mac_format(dst_mac)} "
            f"| 0x{eth_proto:04x}"
        )
        logs.append(eth_line)
        print(eth_line)

        # ===== ARP =====
        if eth_proto == 0x0806:
            if filtro and filtro != "ARP":
                continue

            arp = struct.unpack("!HHBBH6s4s6s4s", payload[:28])
            src_ip = ip_format(arp[6])
            dst_ip = ip_format(arp[8])

            arp_line = f"ARP | {src_ip} → {dst_ip}"
            logs.append(arp_line)
            print(arp_line)
            # ARP no tiene payload adicional, pero podemos mostrar el resto si queremos
            if VER_PAYLOAD and len(payload) > 28:
                dump_payload(payload[28:], prefix="    ")
            continue

        # ===== IPv4 =====
        if eth_proto != 0x0800:
            continue

        # --- IP header real ---
        version_ihl = payload[0]
        ihl = version_ihl & 0x0F
        ip_header_len = ihl * 4

        if len(payload) < ip_header_len:
            continue  # paquet incomplet

        iph = struct.unpack("!BBHHHBBH4s4s", payload[:20])
        proto = iph[6]
        src_ip = ip_format(iph[8])
        dst_ip = ip_format(iph[9])

        proto_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        proto_name = proto_map.get(proto, str(proto))

        if filtro and filtro not in ("IPV4", proto_name, "DHCP"):
            continue

        ip_line = f"IP  | {src_ip} → {dst_ip} | {proto_name}"
        logs.append(ip_line)
        print(ip_line)

        l4_payload = payload[ip_header_len:]

        # ===== TCP =====
        if proto == 6 and len(l4_payload) >= 4:
            src_port, dst_port = struct.unpack("!HH", l4_payload[:4])
            if filtro and filtro != "TCP":
                continue
            tcp_line = f"TCP | {src_port} → {dst_port}"
            logs.append(tcp_line)
            print(tcp_line)
            # Mostrar payload TCP (después de la cabecera TCP)
            # La cabecera TCP tiene longitud variable, necesitamos calcular su tamaño
            # Para simplificar, mostramos todo el l4_payload, que incluye cabecera TCP y datos
            # Pero mejor extraer el payload real: el offset de datos TCP está en el byte 12 (4 bits)
            if len(l4_payload) >= 20:  # mínimo cabecera TCP
                tcp_header_len = ((l4_payload[12] >> 4) & 0x0F) * 4
                tcp_data = l4_payload[tcp_header_len:] if tcp_header_len <= len(l4_payload) else b''
                if VER_PAYLOAD:
                    dump_payload(tcp_data, prefix="    TCP payload: ")
            elif VER_PAYLOAD:
                dump_payload(l4_payload, prefix="    TCP data: ")

        # ===== UDP =====
        elif proto == 17 and len(l4_payload) >= 8:
            src_port, dst_port, length, checksum = struct.unpack("!HHHH", l4_payload[:8])
            if filtro and filtro not in ("UDP", "DHCP"):
                continue

            # Detectar DHCP (UDP 67/68)
            dhcp_flag = False
            if (src_port == 68 and dst_port == 67) or (src_port == 67 and dst_port == 68):
                dhcp_flag = True

            if dhcp_flag:
                dhcp_line = f"DHCP | {src_ip} → {dst_ip} | UDP {src_port}→{dst_port}"
                logs.append(dhcp_line)
                print(dhcp_line)
            else:
                udp_line = f"UDP | {src_port} → {dst_port}"
                logs.append(udp_line)
                print(udp_line)
            
            # Mostrar payload UDP (después de la cabecera UDP de 8 bytes)
            udp_data = l4_payload[8:]
            if VER_PAYLOAD:
                dump_payload(udp_data, prefix="    UDP payload: ")

        # ===== ICMP =====
        elif proto == 1 and len(l4_payload) >= 8:
            icmp_type, code, checksum = struct.unpack("!BBH", l4_payload[:4])
            # Nota: en ICMP, el tipo y código son los primeros 2 bytes, luego checksum 2 bytes
            # Luego viene el payload (que puede incluir parte del datagrama original)
            if filtro and filtro != "ICMP":
                continue
            icmp_line = f"ICMP | Type {icmp_type} Code {code}"
            logs.append(icmp_line)
            print(icmp_line)
            icmp_data = l4_payload[4:]  # después de tipo, código y checksum
            if VER_PAYLOAD:
                dump_payload(icmp_data, prefix="    ICMP payload: ")

except KeyboardInterrupt:
    # ===== Guardar trames =====
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"tramas-{INTERFACE}-{now}.txt"
    with open(filename, "w") as f:
        for line in logs:
            f.write(line + "\n")
    print(f"\n[+] Trames guardades a {filename}")
    print("[+] Programa finalitzat.")


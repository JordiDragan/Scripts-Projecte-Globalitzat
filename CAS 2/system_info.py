import os
import platform
import socket
import psutil

def get_network_info():
    interfaces = psutil.net_if_addrs()
    info = []
    for iface_name, addrs in interfaces.items():
        iface_info = {"name": iface_name}
        for addr in addrs:
            if addr.family.name == 'AF_INET':
                iface_info["ip"] = addr.address
                iface_info["netmask"] = addr.netmask
            elif addr.family.name == 'AF_LINK':
                iface_info["mac"] = addr.address
        info.append(iface_info)
    return info

def main():
    hostname = socket.gethostname()
    os_info = f"{platform.system()} {platform.release()}"
    
    filename = "system_info.txt"
    
    with open(filename, "w") as f:
        f.write(f"Hostname: {hostname}\n")
        f.write(f"Operating System: {os_info}\n\n")
        f.write("Network Interfaces:\n")
        
        for iface in get_network_info():
            f.write(f"Interface: {iface.get('name', 'N/A')}\n")
            f.write(f"  IP Address: {iface.get('ip', 'N/A')}\n")
            f.write(f"  Netmask: {iface.get('netmask', 'N/A')}\n")
            f.write(f"  MAC Address: {iface.get('mac', 'N/A')}\n\n")
    
    print(f"[INFO] Fitxer creat amb èxit: {os.path.abspath(filename)}")

if __name__ == "__main__":
    main()
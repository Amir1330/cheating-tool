import os
import subprocess
import time
import tkinter as tk
import threading
from PIL import Image
import io
import google.generativeai as genai
from dotenv import load_dotenv
import pyperclip

load_dotenv()

class ClipboardMonitor:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        self.is_running = True
        self.previous_content = None
        self.previous_is_image = False
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        # Hyprland/Wayland window settings
        self.root.attributes('-alpha', 0.1)
        self.root.wm_attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry("303x100+40+900")
        self.root.configure(bg='black')

        self.response_label = tk.Label(
            self.root,
            text="📋 Copy question/text or image",
            wraplength=280,
            justify='left',
            fg='#2E8B57',  # Sea green
            bg='#F0F0F0',
            font=('Consolas', 12, 'bold')
        )
        self.response_label.pack(fill='both', expand=True)

        # Drag handling
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)

    def get_clipboard_content(self):
        """Get clipboard content with image priority"""
        try:
            # Check for image first (Wayland/Hyprland)
            types = subprocess.check_output(
                ['wl-paste', '--list-types'],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip().split()
            
            if 'image/png' in types:
                image_data = subprocess.check_output(
                    ['wl-paste', '--type', 'image/png'],
                    stderr=subprocess.DEVNULL
                )
                return (image_data, True)
            
            # Fallback to text
            text = pyperclip.paste().strip()
            return (text, False) if text else (None, False)
        except Exception as e:
            return (None, False)

    def process_content(self, content, is_image):
        """Handle both text and image processing"""
        try:
            self.update_response("🔍 Analyzing...")
            
            if is_image:
                img = Image.open(io.BytesIO(content))
                prompt = """You are an exam assistant. Analyze this image:
1. For multiple choice: ONLY the correct letter(s)
2. Direct answer otherwise
3. No explanations
4. Max 5 words"""
                response = self.vision_model.generate_content([prompt, img])
            else:
                prompt = f"""You are an exam assistant. Given:
{content}
Respond with:
1. ONLY correct letter(s) for MCQs
2. Direct short answer otherwise
3. No explanations"""
                response = self.text_model.generate_content(prompt)

            self.update_response(f"✅ {response.text.strip()}")
        except Exception as e:
            self.update_response(f"❌ Error: {str(e)}")

    def monitor_clipboard(self):
        """Clipboard monitoring loop"""
        while self.is_running:
            try:
                content, is_image = self.get_clipboard_content()
                if content and content != self.previous_content:
                    self.previous_content = content
                    self.previous_is_image = is_image
                    self.process_content(content, is_image)
                time.sleep(0.3)
            except Exception as e:
                self.update_response(f"⚠️ Clipboard Error: {str(e)}")

    def update_response(self, text):
        if hasattr(self, 'response_label'):
            self.response_label.config(text=text)
            self.root.update()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        dx, dy = event.x - self.x, event.y - self.y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        monitor_thread = threading.Thread(target=self.monitor_clipboard)
        monitor_thread.daemon = True
        monitor_thread.start()
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = ClipboardMonitor()
        app.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}") 
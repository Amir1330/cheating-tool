import os
import subprocess
import time
import tkinter as tk
import threading
from PIL import Image
import io
import pytesseract
import google.generativeai as genai
from dotenv import load_dotenv
import pyperclip

load_dotenv()

class ClipboardMonitor:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        self.is_running = True
        self.previous_text = ""
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        # Hyprland/Wayland transparency settings
        self.root.attributes('-alpha', 0.1)
        self.root.wm_attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry("303x100+40+900")
        self.root.configure(bg='black')

        self.response_label = tk.Label(
            self.root,
            text="...",
            wraplength=280,
            justify='left',
            fg='gray',  # Bright green
            bg='#FFFFFF',
            font=('Consolas', 12, 'bold')
        )
        self.response_label.pack(fill='both', expand=True)

        # Make window draggable
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
                # Use pytesseract to extract text from the image
                extracted_text = pytesseract.image_to_string(img)
                self.process_text(extracted_text.strip())
            else:
                self.process_text(content)
        except Exception as e:
            self.update_response(f"❌ Error: {str(e)}")

    def process_text(self, text):
        """Process the extracted or copied text"""
        try:
            self.update_response("...")
            prompt = f"""
You are an exam assistant. Given the question below:
1. If it's a multiple choice question, respond only with the letter(s) of correct answer(s)
2. For other questions, provide only the direct answer without explanation
3. Keep the response as short as possible
4. Never explain your reasoning
5. Never add any additional text
Question: {text}
Answer:"""
            response = self.model.generate_content(prompt)
            self.update_response(response.text.strip())
        except Exception as e:
            self.update_response(f"Error: {str(e)}")

    def update_response(self, text):
        if hasattr(self, 'response_label'):
            self.response_label.config(text=text)
            self.root.update()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def monitor_clipboard(self):
        """Clipboard monitoring loop"""
        while self.is_running:
            try:
                content, is_image = self.get_clipboard_content()
                if content and content != self.previous_text:
                    self.previous_text = content
                    self.process_content(content, is_image)
                time.sleep(0.3)
            except Exception as e:
                self.update_response(f"⚠️ Clipboard Error: {str(e)}")

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
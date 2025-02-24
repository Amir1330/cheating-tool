import os
import pyperclip
import time
import tkinter as tk
import threading
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ClipboardMonitor:
    def __init__(self):
        # Use environment variable for API key
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

    def process_text(self, text):
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
        while self.is_running:
            try:
                current_text = pyperclip.paste()
                if current_text != self.previous_text and current_text.strip():
                    self.previous_text = current_text
                    self.process_text(current_text)
            except Exception as e:
                self.update_response(f"Clipboard Error: {str(e)}")
            time.sleep(0.1)

    def run(self):
        try:
            monitor_thread = threading.Thread(target=self.monitor_clipboard)
            monitor_thread.daemon = True
            monitor_thread.start()
            self.root.mainloop()
        except Exception as e:
            print(f"Error running application: {str(e)}")

if __name__ == "__main__":
    try:
        # Set API key inside .env file in this way
        # GEMINI_API_KEY=your_api_key_here
        app = ClipboardMonitor()
        app.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}")

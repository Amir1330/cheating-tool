import pyperclip
import time
from tkinter import Tk, Label, Frame, Button
from ollama import Client
import threading

class ClipboardMonitor:
    def __init__(self, model_name="qwen:0.5b"):
        self.model_name = model_name
        self.client = Client()
        self.is_running = True
        self.previous_text = ""
        self.setup_gui()

    def setup_gui(self):
        self.root = Tk()

        # Make window frameless and transparent
        self.root.overrideredirect(True)
        self.root.attributes(
            '-alpha', 0.8,  # 80% transparency
            '-topmost', True
        )

        # Configure main window
        self.root.geometry("300x150+10+10")
        self.root.configure(bg='black')

        # Create main frame
        main_frame = Frame(self.root, bg='black')
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Minimal close button in top-right corner
        close_btn = Label(
            main_frame,
            text="×",
            fg='gray70',
            bg='black',
            cursor='hand2'
        )
        close_btn.pack(side='top', anchor='ne')
        close_btn.bind('<Button-1>', lambda e: self.stop_application())

        # Response label with minimal design
        self.response_label = Label(
            main_frame,
            text="waiting for text to convert to haiku...",
            wraplength=280,
            justify='left',
            fg='gray70',
            bg='black',
            font=('Consolas', 9)
        )
        self.response_label.pack(fill='both', expand=True)

        # Make window draggable
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)

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
                self.update_response(f"error: {str(e)}")
            time.sleep(0.5)

    def process_text(self, text):
        try:
            self.update_response("answering...")
            # Format prompt to request a haiku based on the clipboard text
            formatted_prompt = f"Answer the given question with accuracy. For multiple-choice questions, provide only the correct option in the format (e.g., 'C. Answer text'). Avoid any explanations or additional information: {text}"

            response = self.client.generate(
                model=self.model_name,
                prompt=formatted_prompt,
                stream=False
            )
            ai_response = response.response if hasattr(response, 'response') else response.text
            # Format the haiku response with line breaks
            formatted_haiku = ai_response.replace('\n', '\n').strip()
            self.update_response(formatted_haiku)
        except Exception as e:
            self.update_response(f"error: {str(e)}")

    def update_response(self, text):
        if hasattr(self, 'response_label'):
            self.response_label.config(text=text)
            self.root.update()

    def stop_application(self):
        self.is_running = False
        self.root.quit()

    def run(self):
        monitor_thread = threading.Thread(target=self.monitor_clipboard)
        monitor_thread.daemon = True
        monitor_thread.start()
        self.root.mainloop()

if __name__ == "__main__":
    app = ClipboardMonitor()
    app.run()

import os
import time
import tkinter as tk
import threading
from PIL import ImageGrab
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
        print("Setting up GUI...")  # Debugging statement
        self.root = tk.Tk()
        # Windows transparency settings
        self.root.attributes('-alpha', 0.9)  # Make it more visible
        self.root.wm_attributes("-topmost", True)
        self.root.overrideredirect(True)

        # Set window size and position it in the center of the screen
        window_width = 400  # Increased width
        window_height = 200  # Increased height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
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

        # Close button
        close_button = tk.Button(self.root, text="Close", command=self.close_window)
        close_button.pack(pady=10)

        # Make window draggable
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)

        print("GUI setup complete.")  # Debugging statement

    def get_clipboard_content(self):
        """Get clipboard content with image priority"""
        try:
            # Check for image first
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                img.save("temp_image.png")  # Save the image temporarily
                with open("temp_image.png", "rb") as image_file:
                    return (image_file.read(), True)

            # Fallback to text
            text = pyperclip.paste().strip()
            return (text, False) if text else (None, False)
        except Exception as e:
            return (None, False)

    def process_content(self, content, is_image):
        """Handle both text and image processing"""
        try:
            self.update_response("🔍 Analyzing...")
            print(f"Processing content: {content}")  # Debugging statement
            
            if is_image:
                img = Image.open(io.BytesIO(content))
                # Use pytesseract to extract text from the image
                extracted_text = pytesseract.image_to_string(img)
                print(f"Extracted text from image: {extracted_text}")  # Debugging statement
                self.process_text(extracted_text.strip())
            else:
                self.process_text(content)
        except Exception as e:
            self.update_response(f"❌ Error: {str(e)}")

    def process_text(self, text):
        """Process the extracted or copied text"""
        try:
            self.update_response("...")
            print(f"Sending to AI: {text}")  # Debugging statement
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
            print(f"AI Response: {response.text.strip()}")  # Debugging statement
            if response.text.strip():  # Check if response is not empty
                self.update_response(response.text.strip())
            else:
                self.update_response("No response from AI.")
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

    def close_window(self):
        """Close the application"""
        self.is_running = False
        self.root.destroy()

    def run(self):
        print("Starting clipboard monitoring...")  # Debugging statement
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
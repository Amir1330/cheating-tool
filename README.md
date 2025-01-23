## ultimate cheating tool
### usage
- clone this repo `git clone https://github.com/Amir1330/cheating-tool/`
- go to the directory `cd cheating-tool`
- install dependencies `pip install python-dotenv pyperclip google-generativeai`
- create a ***.env*** file `touch .env`
- add your **gemini** API key to .env file `GEMINI_API_KEY=your_api_key_here` you can find it [here](https://aistudio.google.com/apikey)
- if you are using windows u can make it completle transparent by
  ```
  self.root.attributes('-transparentcolor', 'black')  # Make black background transparent
  self.root.configure(bg='black')
  ```
- run `python3 google-selector.py` and just copy MCQ, it will automaticaly ask gemini and give only letter as a response 

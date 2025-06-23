Hi there! 👋
This guide will help you set up TaskNav, a cool Python web app.


🖥️ Step 1: Install Visual Studio Code (VS Code)
Visual Studio Code is like a special notebook where you write code.

👉 To install it:
Go to this website: https://code.visualstudio.com/

Click the Download button for your computer (Windows, Mac, or Linux).

Open the downloaded file and follow the instructions to install it.

Once it's done, open VS Code!


🐍 Step 2: Install Python
Python is the language this app uses!

Go to https://www.python.org/downloads/

Click Download Python (choose the latest version).

Open the file and install it. Make sure to check the box that says ✅ "Add Python to PATH" before clicking "Install."

📂 Step 3: Get the Project
Open VS Code

Press Ctrl ~ to open the Terminal (a black box at the bottom)

Copy and paste this one at a time:

git clone https://github.com/margvelinho/TaskNav.git

cd TaskNav

This gets the project onto your computer.

📦 Step 4: Install the Tools (Packages)
if you dont have flask installed:
in the terminal enter: pip install flask
Still in the terminal, type this:
  pip install python-dotenv
  
This installs something that helps hide secret codes (called environment variables).


🔐 Step 5: Add Your API Key and Secret Key
In the TaskNav folder, create a new file named .env

Inside that file, add this line (replace with your real key):

env file:
API_KEY=your_openrouter_api_key_here

👉 You can get a free API key here: https://openrouter.ai
Create an account then on the right top of the screen click on the accound, you will se "key", click it and create new API Key.

You also need a FLASK_SECRET_KEY. This is like a secret password that helps keep your website safe.

To make one, just run the .py file,

You’ll see a long string of letters and numbers, like:
e2f4a8c5f1d2b3c9e7a1f3e9b0c7d1a2

Copy that string and add it to your .env file like this:

FLASK_SECRET_KEY=e2f4a8c5f1d2b3c9e7a1f3e9b0c7d1a2
🧠 What does this do?
This line gives Flask (the tool that runs the website) a secret code to keep your sessions safe and secure.

🚀 Step 6: Run the App!
Now run app.py

Running on http://localhost:5000/

🎉 Go to your web browser and visit: http://localhost:5000

Your TaskNav app is live!

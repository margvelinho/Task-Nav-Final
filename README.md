TASKNAV
🔧How to Set Up This Project:


### 📥 1. Download the Project

Open your terminal and run the following commands to clone the project and enter the project folder:

```bash
git clone https://github.com/margvelinho/TaskNav.git
cd TaskNav

Enter this in the Terminal: pip install python-dotenv


Make sure you have Python installed

3. Set Up Environment Variables
Create a .env file in the root directory and add your OpenRouter API key like this:

API_KEY=your_openrouter_api_key_here
👉 You can get a free API key from: https://openrouter.ai

🔐 Generate a Secret Key

You need a `FLASK_SECRET_KEY` for Flask session security.  
You can generate one by running this in Python:

```python
import secrets
print(secrets.token_hex(16))
Then, copy the result into your .env file like this:
FLASK_SECRET_KEY=your_generated_key_here

4.Run the App

python app.py

The Flask app should now be running at http://localhost:5000/.

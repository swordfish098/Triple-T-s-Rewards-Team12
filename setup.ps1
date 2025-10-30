
# Create and activate virtual environment
# The activation command is different for Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies from requirements.txt
pip install -r requirements.txt
# Install Waitress instead of Gunicorn
pip install waitress

# Run the app using Waitress
# This will run in the current window. You must keep the window open.
python .\app.py
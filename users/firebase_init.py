import firebase_admin
from firebase_admin import credentials
import os

username = os.getlogin()  
FIREBASE_CREDENTIALS_PATH = f"C:\\Users\\{username}\\Downloads\\findthem.json"

def initialize_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            print(f"Looking for Firebase credentials at: {FIREBASE_CREDENTIALS_PATH}")
            if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
                print(f"ERROR: Firebase credentials file not found at {FIREBASE_CREDENTIALS_PATH}")
                return
                
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
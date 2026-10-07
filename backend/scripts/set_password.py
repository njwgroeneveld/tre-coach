"""Set a new password for a tre-coach account.

The app has no password-reset page, so a forgotten password is set here with the service role key.
The password is typed hidden and never printed.

Run from tre-coach/backend:  venv\\Scripts\\python.exe scripts\\set_password.py
"""
import getpass
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

email = input("Email: ").strip().lower()
user = next((u for u in client.auth.admin.list_users() if (u.email or "").lower() == email), None)
if not user:
    raise SystemExit(f"No account with email {email}")

password = getpass.getpass("New password (hidden): ")
if len(password) < 8:
    raise SystemExit("Use at least 8 characters.")
if getpass.getpass("Repeat it: ") != password:
    raise SystemExit("The passwords do not match; nothing changed.")

client.auth.admin.update_user_by_id(user.id, {"password": password})
print(f"Password updated for {email}. Log in with it at http://localhost:5173")

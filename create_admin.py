import sys
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import create_admin

username = input("Enter admin username: ")
email = input("Enter admin email: ")
password = input("Enter admin password: ")

password_hash = generate_password_hash(password)

create_admin(
    username,
    email,
    password_hash,
    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
)

print(f"Admin '{username}' created successfully!")
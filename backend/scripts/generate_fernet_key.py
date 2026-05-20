#!/usr/bin/env python3
"""Print a Fernet key for FERNET_KEY in .env (requires cryptography from requirements.txt)."""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    print(Fernet.generate_key().decode())

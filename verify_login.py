from rag_api_service import hash_password, verify_password, fake_users_db

def verify_login_logic():
    print("Verifying password hashing...")
    pwd = "secret"
    hashed = hash_password(pwd)
    print(f"Hash generated: {hashed}")
    
    if verify_password(pwd, hashed):
        print("SUCCESS: Password verified correctly.")
    else:
        print("FAILURE: Password verification failed.")

    print("\nVerifying mock DB...")
    admin_user = fake_users_db.get("admin")
    if admin_user:
        stored_hash = admin_user["hashed_password"]
        if verify_password("secret", stored_hash):
             print("SUCCESS: Admin password verified.")
        else:
             print("FAILURE: Admin password verification failed.")
    else:
        print("FAILURE: Admin user not found in mock DB.")

if __name__ == "__main__":
    verify_login_logic()

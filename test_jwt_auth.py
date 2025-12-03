import requests
import sys

BASE_URL = "http://localhost:8001"

def test_jwt_auth():
    print("Testing JWT Authentication...")

    # 1. Login to get token
    print("\n1. Testing Login (/token)...")
    login_data = {
        "username": "admin",
        "password": "secret"
    }
    try:
        response = requests.post(f"{BASE_URL}/token", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("✅ Login successful. Token received.")
            else:
                print("❌ Login failed. No access token in response.")
                sys.exit(1)
        else:
            print(f"❌ Login failed. Status code: {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error during login: {e}")
        sys.exit(1)

    # 2. Access protected resource with token
    print("\n2. Testing Protected Resource (/admin/leads) with valid token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{BASE_URL}/admin/leads", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "leads" in data and "user" in data:
                print("✅ Access granted. Data received.")
                print(f"   User: {data['user']}")
                print(f"   Leads count: {len(data['leads'])}")
            else:
                print("❌ Unexpected response format.")
                print(data)
        else:
            print(f"❌ Access denied. Status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error accessing protected resource: {e}")

    # 3. Access protected resource without token
    print("\n3. Testing Protected Resource (/admin/leads) without token...")
    try:
        response = requests.get(f"{BASE_URL}/admin/leads")
        if response.status_code == 401:
            print("✅ Access denied as expected (401 Unauthorized).")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing protected resource: {e}")

    # 4. Access protected resource with invalid token
    print("\n4. Testing Protected Resource (/admin/leads) with invalid token...")
    headers = {"Authorization": "Bearer invalid_token"}
    try:
        response = requests.get(f"{BASE_URL}/admin/leads", headers=headers)
        if response.status_code == 401:
            print("✅ Access denied as expected (401 Unauthorized).")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing protected resource: {e}")

if __name__ == "__main__":
    test_jwt_auth()

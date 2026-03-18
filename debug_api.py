import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_check_identifier():
    print("Testing check-identifier...")
    r = requests.get(f"{BASE_URL}/auth/check-identifier?q=kmaisan@dspng.tech")
    print(f"Admin check: {r.status_code} {r.json()}")

    r = requests.get(f"{BASE_URL}/auth/check-identifier?q=nonexistent@test.com")
    print(f"New user check: {r.status_code} {r.json()}")

def test_signup_email():
    print("\nTesting signup (email)...")
    payload = {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    r = requests.post(f"{BASE_URL}/auth/signup", json=payload)
    print(f"Signup response: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
    else:
        print(r.json())

def test_login_email():
    print("\nTesting login (email)...")
    payload = {
        "username": "testuser@example.com",
        "password": "testpassword123"
    }
    r = requests.post(f"{BASE_URL}/auth/token", data=payload)
    print(f"Login response: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
    else:
        print(r.json())

if __name__ == "__main__":
    try:
        test_check_identifier()
        test_signup_email()
        test_login_email()
    except Exception as e:
        print(f"Error: {e}")

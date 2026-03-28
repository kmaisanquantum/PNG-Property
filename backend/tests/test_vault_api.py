import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock FastAPI dependencies and models
from main import User, FollowSearchRequest, UPLOAD_DIR

def test_vault_config():
    print("Testing Vault Configuration...")
    assert UPLOAD_DIR.exists()
    print(f"  Upload Dir: {UPLOAD_DIR}")

def test_user_model_update():
    print("Testing User Model Update...")
    u = User(email="test@example.com", full_name="Test User", documents=[{"type": "ID", "filename": "id.pdf"}])
    assert hasattr(u, "documents")
    assert len(u.documents) == 1
    print(f"  User documents field verified.")

if __name__ == "__main__":
    try:
        test_vault_config()
        test_user_model_update()
        print("\n✅ Vault Infrastructure Verified!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

"""
Check which server is currently running
"""
import requests

SERVER_URL = "http://localhost:8001"

def check_server():
    """Check which server type is running"""
    try:
        response = requests.get(f"{SERVER_URL}/")
        if response.status_code == 200:
            info = response.json()
            print(f"Server Name: {info.get('name', 'Unknown')}")
            print(f"Version: {info.get('version', 'Unknown')}")
            print(f"Description: {info.get('description', 'None')}")
            
            if "security_features" in info:
                print("\n🔐 Security Features:")
                if isinstance(info["security_features"], dict):
                    for feature, description in info["security_features"].items():
                        print(f"   - {feature}: {description}")
                elif isinstance(info["security_features"], list):
                    for feature in info["security_features"]:
                        print(f"   - {feature}")
                return "secure"
            else:
                print("\n⚠️  Basic server - no advanced security features detected")
                return "basic"
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return "error"
    except Exception as e:
        print(f"❌ Could not connect to server: {e}")
        return "offline"

if __name__ == "__main__":
    print("🔍 Checking server type...")
    server_type = check_server()
    
    if server_type == "secure":
        print("\n✅ Secure server is running - ready for Phase 6B tests")
    elif server_type == "basic":
        print("\n⚠️  Basic server running - start secure server for Phase 6B tests:")
        print("   python run_secure_server.py")
    elif server_type == "offline":
        print("\n❌ No server running - start secure server:")
        print("   python run_secure_server.py")
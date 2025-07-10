#!/usr/bin/env python3
"""
Test script for Phase 8A Web Interface
Validates core functionality without requiring full Streamlit execution
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing Phase 8A Web Interface Imports...")
    
    try:
        # Test Streamlit import
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        # Test web interface imports
        from web_ui.streamlit_app import StreamlitWebInterface
        print("✅ StreamlitWebInterface imported successfully")
    except ImportError as e:
        print(f"❌ StreamlitWebInterface import failed: {e}")
        return False
    
    try:
        # Test security imports (optional)
        from cli_agent.auth.auth_manager import AuthManager
        print("✅ AuthManager imported successfully")
    except ImportError as e:
        print(f"⚠️  AuthManager import failed (optional): {e}")
    
    try:
        # Test CLI agent import
        from cli_agent.cli_agent import CLIAgent
        print("✅ CLIAgent imported successfully")
    except ImportError as e:
        print(f"❌ CLIAgent import failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test that required files exist"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        "web_ui/streamlit_app.py",
        "run_web_ui.py",
        "requirements.txt",
        "README_WEB_UI.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_web_interface_class():
    """Test StreamlitWebInterface class instantiation"""
    print("\n🏗️ Testing StreamlitWebInterface Class...")
    
    try:
        from web_ui.streamlit_app import StreamlitWebInterface
        
        # Test class instantiation
        interface = StreamlitWebInterface()
        print("✅ StreamlitWebInterface instantiated successfully")
        
        # Test method existence
        required_methods = [
            'authenticate_user',
            'render_header',
            'render_sidebar',
            'render_authentication',
            'render_chat_interface',
            'process_user_query',
            'run'
        ]
        
        for method_name in required_methods:
            if hasattr(interface, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ StreamlitWebInterface test failed: {e}")
        return False

def test_requirements():
    """Test that requirements.txt contains Streamlit dependencies"""
    print("\n📦 Testing Requirements...")
    
    try:
        with open(current_dir / "requirements.txt", "r") as f:
            content = f.read()
        
        required_deps = ["streamlit", "fastapi", "uvicorn"]
        all_found = True
        
        for dep in required_deps:
            if dep in content:
                print(f"✅ {dep} found in requirements.txt")
            else:
                print(f"❌ {dep} missing from requirements.txt")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Phase 8A Web Interface Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("File Structure", test_file_structure),
        ("Web Interface Class", test_web_interface_class),
        ("Requirements", test_requirements)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 8A Web Interface is ready.")
        print("\n🚀 To start the web interface:")
        print("   python run_web_ui.py")
        return True
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
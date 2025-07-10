#!/usr/bin/env python3
"""
Launch script for Boomi DataHub Web Interface - Phase 8A
Starts the Streamlit web application
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit web interface"""
    print("🚀 Starting Boomi DataHub Web Interface - Phase 8A")
    print("=" * 60)
    
    # Get the web_ui directory
    web_ui_dir = Path(__file__).parent / "web_ui"
    streamlit_app = web_ui_dir / "streamlit_app.py"
    
    if not streamlit_app.exists():
        print(f"❌ Error: {streamlit_app} not found")
        sys.exit(1)
    
    print(f"📂 Web UI Directory: {web_ui_dir}")
    print(f"📄 Streamlit App: {streamlit_app}")
    print("🌐 Starting web server...")
    print()
    print("📋 Instructions:")
    print("1. The web interface will open in your browser")
    print("2. Use demo accounts: martha.stewart / good.business.2024")
    print("3. Make sure the unified server is running separately")
    print()
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(streamlit_app),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
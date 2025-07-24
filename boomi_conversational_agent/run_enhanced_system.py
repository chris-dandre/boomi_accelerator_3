"""
Enhanced System Launcher for Phase 8B
Launch CLI or Web interface with LangGraph orchestration
"""

import sys
import os
import argparse
import asyncio

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def launch_cli():
    """Launch the enhanced CLI interface"""
    print("🚀 Starting Enhanced CLI with LangGraph Orchestration")
    print("=" * 50)
    
    try:
        from cli.enhanced_interactive_cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"❌ Error importing CLI: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error launching CLI: {e}")

def launch_web():
    """Launch the enhanced web interface"""
    print("🚀 Starting Enhanced Web UI with LangGraph Orchestration")
    print("=" * 50)
    
    try:
        # Launch Streamlit app
        os.system("streamlit run web_ui/enhanced_streamlit_app.py --server.port 8501 --server.headless true")
    except Exception as e:
        print(f"❌ Error launching Web UI: {e}")

def test_orchestrator():
    """Test the orchestrator functionality"""
    print("🧪 Testing Enhanced Orchestrator")
    print("=" * 50)
    
    try:
        from test_orchestrator import main as test_main
        test_main()
    except ImportError as e:
        print(f"❌ Error importing test: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error running tests: {e}")

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description="Enhanced SWX MCP Server Launcher")
    parser.add_argument(
        'interface', 
        choices=['cli', 'web', 'test'],
        help='Interface to launch: cli, web, or test'
    )
    
    args = parser.parse_args()
    
    if args.interface == 'cli':
        launch_cli()
    elif args.interface == 'web':
        launch_web()
    elif args.interface == 'test':
        test_orchestrator()
    else:
        print("❌ Invalid interface. Use 'cli', 'web', or 'test'")

if __name__ == "__main__":
    main()
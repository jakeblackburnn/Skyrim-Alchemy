#!/usr/bin/env python
"""
Skyrim Alchemy Calculator Web UI Entry Point

This script launches the Django web application for the Skyrim Alchemy Calculator.
Supports local development, Docker, and Railway deployment with automatic environment detection.
"""
import os
import sys
import subprocess


def main():
    """Launch the Django development server with environment-aware binding."""
    # Add the web_ui directory to the Python path
    web_ui_path = os.path.join(os.path.dirname(__file__), 'web_ui')

    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skyrim_alchemy.settings')

    # Path to manage.py
    manage_py = os.path.join(web_ui_path, 'manage.py')

    # Environment detection
    is_docker = os.path.exists('/.dockerenv')  # Docker creates this file
    port = os.environ.get('PORT', '8000')

    # Security: Bind to 0.0.0.0 only in Docker/Railway, otherwise localhost
    # - Local dev (127.0.0.1): Prevents accidental LAN exposure
    # - Docker/Railway (0.0.0.0): Required for external connections
    if is_docker or os.environ.get('PORT'):
        host = '0.0.0.0'
        environment = "Docker/Cloud"
    else:
        host = '127.0.0.1'
        environment = "Local Development"

    print("=" * 60)
    print("  SKYRIM ALCHEMY CALCULATOR WEB UI")
    print("=" * 60)
    print()
    print(f"Environment: {environment}")
    print(f"Starting Django development server on {host}:{port}...")

    if host == '127.0.0.1':
        print(f"Access the application at: http://localhost:{port}")
    else:
        print(f"Server binding to: {host}:{port}")
        print(f"Access via your Docker/Railway URL")

    print()
    print("Press CTRL+C to quit.")
    print()

    # Run the Django development server with explicit host:port
    try:
        subprocess.run(
            [sys.executable, manage_py, 'runserver', f'{host}:{port}'],
            cwd=web_ui_path,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
    except subprocess.CalledProcessError as e:
        print(f"\nError running server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

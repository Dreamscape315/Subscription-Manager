#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subscription Management System Startup Script
"""

import os
import sys
from app import app, db, update_setting, SystemSettings

def init_database():
    """Initialize database"""
    print("Initializing database...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize default settings
        if not SystemSettings.query.filter_by(key='subconverter_url').first():
            update_setting('subconverter_url', 'https://api.subconverter.com/sub', 'Subconverter API Address')
            print("✓ Default Subconverter API address set")
        
        if not SystemSettings.query.filter_by(key='base_url').first():
            update_setting('base_url', 'http://localhost:5000', 'Application Base URL')
            print("✓ Default application base URL set")
    
    print("✓ Database initialization completed")

def main():
    """Main function"""
    print("=" * 50)
    print("🚀 Subscription Management System")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher required")
        sys.exit(1)
    
    # Initialize database
    init_database()
    
    # Get configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"\n📡 Server Configuration:")
    print(f"   Address: http://{host}:{port}")
    print(f"   Debug Mode: {'Enabled' if debug else 'Disabled'}")
    
    print(f"\n🎯 Usage Instructions:")
    print(f"   1. Open browser and visit: http://localhost:{port}")
    print(f"   2. Register first user (automatically becomes admin)")
    print(f"   3. Start managing your subscriptions")
    
    print(f"\n⚡ Starting...")
    print("=" * 50)
    
    try:
        # Start application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
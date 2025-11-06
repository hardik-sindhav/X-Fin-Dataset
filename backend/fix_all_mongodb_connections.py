#!/usr/bin/env python3
"""
Fix all MongoDB connections to include authSource parameter
This fixes the "Authentication failed" error
"""

import os
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).parent

# Pattern to find MongoDB connection code
OLD_PATTERN = r'''if MONGO_USERNAME and MONGO_PASSWORD:
                # URL-encode username and password to handle special characters like @, :, etc.
                encoded_username = quote_plus\(MONGO_USERNAME\)
                encoded_password = quote_plus\(MONGO_PASSWORD\)
                mongo_uri = f"mongodb://\{encoded_username\}:\{encoded_password\}@\{MONGO_HOST\}:\{MONGO_PORT\}/"'''

NEW_CODE = '''if MONGO_USERNAME and MONGO_PASSWORD:
                # URL-encode username and password to handle special characters like @, :, etc.
                encoded_username = quote_plus(MONGO_USERNAME)
                encoded_password = quote_plus(MONGO_PASSWORD)
                # Get auth source (default to 'admin' for MongoDB)
                MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
                # Build connection string with authSource parameter (required for MongoDB auth)
                mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"'''

def fix_file(filepath):
    """Fix MongoDB connection in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already fixed
        if 'authSource' in content and 'MONGO_AUTH_SOURCE' in content:
            print(f"⏭  {filepath.name} - Already fixed, skipping")
            return False
        
        # Replace the pattern
        # Use a more flexible regex pattern
        pattern = r'(if MONGO_USERNAME and MONGO_PASSWORD:.*?mongo_uri = f"mongodb://\{encoded_username\}:\{encoded_password\}@\{MONGO_HOST\}:\{MONGO_PORT\}/")'
        
        replacement = r'''if MONGO_USERNAME and MONGO_PASSWORD:
                # URL-encode username and password to handle special characters like @, :, etc.
                encoded_username = quote_plus(MONGO_USERNAME)
                encoded_password = quote_plus(MONGO_PASSWORD)
                # Get auth source (default to 'admin' for MongoDB)
                MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
                # Build connection string with authSource parameter (required for MongoDB auth)
                mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"'''
        
        # Try multiline replacement
        new_content = re.sub(
            r'(if MONGO_USERNAME and MONGO_PASSWORD:.*?encoded_password = quote_plus\(MONGO_PASSWORD\))\s+(mongo_uri = f"mongodb://\{encoded_username\}:\{encoded_password\}@\{MONGO_HOST\}:\{MONGO_PORT\}/")',
            r'\1\n                # Get auth source (default to \'admin\' for MongoDB)\n                MONGO_AUTH_SOURCE = os.getenv(\'MONGO_AUTH_SOURCE\', \'admin\')\n                # Build connection string with authSource parameter (required for MongoDB auth)\n                mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"',
            content,
            flags=re.DOTALL
        )
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓  Fixed {filepath.name}")
            return True
        else:
            # Try simpler approach - just add the lines
            lines = content.split('\n')
            new_lines = []
            i = 0
            fixed = False
            
            while i < len(lines):
                line = lines[i]
                new_lines.append(line)
                
                # Check if this is the mongo_uri line we need to fix
                if 'mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/"' in line and not fixed:
                    # Check previous lines for MONGO_PASSWORD
                    if i > 0 and 'encoded_password = quote_plus(MONGO_PASSWORD)' in lines[i-1]:
                        # Insert authSource code before this line
                        new_lines.pop()  # Remove the line we just added
                        new_lines.append('                # Get auth source (default to \'admin\' for MongoDB)')
                        new_lines.append("                MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')")
                        new_lines.append('                # Build connection string with authSource parameter (required for MongoDB auth)')
                        # Fix the URI line
                        fixed_line = line.replace(
                            'mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/"',
                            'mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"'
                        )
                        new_lines.append(fixed_line)
                        fixed = True
                    else:
                        new_lines.append(line)
                
                i += 1
            
            if fixed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                print(f"✓  Fixed {filepath.name}")
                return True
            else:
                print(f"✗  {filepath.name} - Pattern not found or already different")
                return False
                
    except Exception as e:
        print(f"✗  {filepath.name} - Error: {str(e)}")
        return False

def main():
    """Fix all collector files"""
    print("=" * 60)
    print("Fixing MongoDB Connection Strings")
    print("=" * 60)
    print()
    print("This will add 'authSource' parameter to all MongoDB connections")
    print("This is REQUIRED for MongoDB authentication to work")
    print()
    
    # Find all collector files
    collector_files = list(BACKEND_DIR.glob('nse_*_collector.py'))
    collector_files.append(BACKEND_DIR / 'admin_panel.py')
    
    fixed_count = 0
    for filepath in sorted(collector_files):
        if fix_file(filepath):
            fixed_count += 1
    
    print()
    print("=" * 60)
    print(f"Fixed {fixed_count} files")
    print("=" * 60)
    print()
    print("IMPORTANT: Add to your .env file:")
    print("MONGO_AUTH_SOURCE=admin")
    print()
    print("Then restart your backend:")
    print("pm2 restart x-fin-backend")
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()


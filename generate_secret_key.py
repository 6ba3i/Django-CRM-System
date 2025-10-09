#!/usr/bin/env python
"""
Generate a secure SECRET_KEY for Django
"""

import secrets
import string

def generate_secret_key(length=50):
    """Generate a secure random string for Django SECRET_KEY"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(characters) for _ in range(length))

def update_env_file(secret_key):
    """Update .env file with new SECRET_KEY"""
    try:
        # Read existing .env
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update SECRET_KEY line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('SECRET_KEY='):
                lines[i] = f'SECRET_KEY={secret_key}\n'
                updated = True
                break
        
        # If SECRET_KEY not found, add it
        if not updated:
            lines.insert(0, f'SECRET_KEY={secret_key}\n')
        
        # Write back
        with open('.env', 'w') as f:
            f.writelines(lines)
        
        return True
    except FileNotFoundError:
        return False

if __name__ == '__main__':
    print("\n🔐 Django SECRET_KEY Generator")
    print("=" * 40)
    
    # Generate new key
    new_key = generate_secret_key()
    
    print(f"\n✨ Generated SECRET_KEY:")
    print(f"   {new_key}")
    
    # Try to update .env file
    if update_env_file(new_key):
        print("\n✅ Successfully updated .env file!")
    else:
        print("\n⚠️ Could not find .env file")
        print("\n📝 Add this to your .env file:")
        print(f"SECRET_KEY={new_key}")
    
    print("\n🔒 Keep this key secret and never commit it to git!")
    print("   Add .env to your .gitignore file")
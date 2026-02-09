import os

with open('.env', 'rb') as f:
    content = f.read()
    print(f"Content repr: {content}")
    
    # Check specifically GOOGLE_API_KEY line
    lines = content.split(b'\n')
    for line in lines:
        if b'GOOGLE_API_KEY' in line:
            print(f"Key Line: {line}")

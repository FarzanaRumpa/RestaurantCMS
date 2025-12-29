# Helper script to create run.py with proper encoding
content = """from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
"""

with open('run.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('run.py created successfully!')
print('Content:')
print(content)


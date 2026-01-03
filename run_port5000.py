"""Run the server on port 5000 for compatibility"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting server on http://127.0.0.1:5000")
    print("Admin login: http://127.0.0.1:5000/rock/login")
    print("Owner login: http://127.0.0.1:5000/owner/login")
    print("Pricing Plans: http://127.0.0.1:5000/rock/pricing-plans")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)


from app import create_app

app = create_app()

if __name__ == '__main__':
    # Port 5000/5001 may conflict with AirPlay on macOS
    # Run on port 8000 instead
    print("Starting server on http://127.0.0.1:8000")
    print("Admin login: http://127.0.0.1:8000/rock/login")
    print("Owner login: http://127.0.0.1:8000/owner/login")
    app.run(debug=True, host='127.0.0.1', port=8000, use_reloader=False)

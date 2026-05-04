import os
from backend.app import app

if __name__ == '__main__':
    # Run the Flask app from root
    app.run(debug=True, port=5000)

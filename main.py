import logging
from app import app

if __name__ == '__main__':
    logging.info("Starting Bookstore Management System")
    app.run(host='0.0.0.0', port=5000, debug=True)

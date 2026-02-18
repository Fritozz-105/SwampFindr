"""Application entry point."""
import os
from app import create_app
from app.config import config_by_name
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file


# Get configuration from environment or use default
config_name = os.getenv('FLASK_ENV', 'development') #config name can be set to development or production, or testing
app = create_app(config_by_name.get(config_name, config_by_name['default']))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

from app import create_app
from app.config import DevelopmentConfig, ProductionConfig
import os
# from app.config import get_config

# config_class = get_config()

app = create_app()

if __name__ == '__main__':

    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000)

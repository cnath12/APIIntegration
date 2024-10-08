from app import create_app
from app.config import DevelopmentConfig, ProductionConfig
import os

app = create_app()

if __name__ == '__main__':

    app.run(debug=True)


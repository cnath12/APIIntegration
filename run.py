import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
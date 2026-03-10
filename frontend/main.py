# In main.py (at the project root)

import os

from app import create_app

config_name = os.getenv("FLASK_CONFIG") or "default"
app = create_app(config_name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

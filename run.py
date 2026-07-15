import os
from backend import create_app

# Create the Flask application
app = create_app(os.getenv("FLASK_ENV", "development"))
print(app.config["SQLALCHEMY_DATABASE_URI"])

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=app.config["DEBUG"])

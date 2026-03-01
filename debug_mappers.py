from app import create_app
from extensions import db
import models # Import models to ensure they are registered
app = create_app()
with app.app_context():
    try:
        from sqlalchemy.orm import configure_mappers
        configure_mappers()
        print("MAPPERS_OK")
    except Exception as e:
        import traceback
        print(f"MAPPERS_ERROR: {e}")
        traceback.print_exc()

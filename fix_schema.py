from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Use native SQL to add the column if it doesn't exist
        # SQLite
        db.session.execute(text("ALTER TABLE submission ADD COLUMN flowchart_path VARCHAR(256)"))
        db.session.commit()
        print("Column flowchart_path added to submission table successfully!")
    except Exception as e:
        print(f"Error (probably already exists): {e}")
        db.session.rollback()

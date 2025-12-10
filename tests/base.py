import unittest
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app import create_app, db

# --- listener pro SQLite ---
# SQLAlchemy se připojí k SQLite
# vytvoří se alias 'bds', aby fungovaly dotazy jako 'SELECT * FROM bds.product'
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("ATTACH DATABASE ':memory:' AS bds")
    except sqlite3.OperationalError:
        # Pokud je už databáze připojená
        pass
    finally:
        cursor.close()

class BaseTestCase(unittest.TestCase):
   
    def setUp(self):
        self.app = create_app(test_config={
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'TESTING': True,
            'WTF_CSRF_ENABLED': False
        })
        
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        
        db.engine.dispose()
        
        self.app_context.pop()
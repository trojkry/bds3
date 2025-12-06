import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sshtunnel import SSHTunnelForwarder

load_dotenv()

ssh_host = os.getenv('SSH_HOST')
ssh_user = os.getenv('SSH_USER')
ssh_key_path = os.getenv('SSH_KEY_PATH')

db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

print("Attempting to open SSH tunnel...")

try:
    with SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_user,
        ssh_pkey=ssh_key_path,
        remote_bind_address=('127.0.0.1', 5432)
    ) as server:
        
        print(f"SSH Tunnel active. Local port: {server.local_bind_port}")

        db_url = f"postgresql://{db_user}:{db_pass}@127.0.0.1:{server.local_bind_port}/{db_name}"
        
        print(f"Database URL: {db_url}")

        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            print("Database connection successful:", result.fetchone())

except Exception as e:
    print("Database connection failed:", e)
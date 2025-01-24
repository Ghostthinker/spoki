import os
from dotenv import load_dotenv
import subprocess
from utils.helpers import create_config

load_dotenv()

port = os.getenv("STREAMLIT_PORT", "9307")
base_url_path = os.getenv("STREAMLIT_SERVER_BASEURLPATH", "")

print(base_url_path)
create_config(base_url_path)

subprocess.run(["streamlit", "run", "app.py", "--server.port", port])

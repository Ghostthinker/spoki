import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth


def authenticate_user(config_file: str, app_title: str = "Login"):

    try:
        with open(config_file) as file:
            config = yaml.load(file, Loader=SafeLoader)

        stauth.Hasher.hash_passwords(config['credentials'])
        # Create the authenticator object
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )


        return authenticator


    except Exception as e:
        st.error(f"Error loading authentication: {e}")


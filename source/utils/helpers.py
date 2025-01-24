import os

def load_css(file_name):
    """Load and return the content of the CSS file as a style tag."""
    with open(file_name) as f:
        return f"<style>{f.read()}</style>"

def render_header(st):
    logo_url = "https://cdn.dosb.de/_processed_/c/3/csm_DOSB-Logo_Ringe_Farbe_702f233ba7.jpg"  # Replace with your actual logo URL or local file path
    intro_text = "SpoKI unterstützt die Bildungsreferent*innen und Ausbilder*innen der Sportverbände dabei, kompetenzorientierte Aufgaben für Trainer*innen/ÜL-Lehrgänge zu erstellen, indem es Feedback auf Basis des DOSB-Kompetenzmodells zu Aufgaben-Entwürfen gibt."

    text_input_container = st.empty()

    """Generate the header HTML with a logo and introductory text."""
    header_html = f"""
    <div class="custom-header">
        <div>
            <h1>        <img src="{logo_url}" alt="Logo">Willkommen bei SpoKI</h1>
            <p class="intro-text">{intro_text}</p>
        </div>
    </div>
    """

    text_input_container.markdown(header_html, unsafe_allow_html=True)

    return text_input_container


def create_config(base_url_path):
    # Definiere den Pfad zur Konfigurationsdatei
    config_path = os.path.join(".streamlit", "config.toml")

    # Wenn die Datei existiert, keine Änderungen vornehmen
    if os.path.exists(config_path):
        print(f"Config file already exists at {config_path}. Skipping creation.")
        return

    # Sicherstellen, dass das Verzeichnis existiert
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Inhalt der Konfigurationsdatei
    config_content = f"""
[browser]
gatherUsageStats = false

[theme]
primaryColor = "#fcb131"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#1b1b1b"
font = "sans serif"

[server]
baseUrlPath = "{base_url_path}"
    """

    with open(config_path, "w") as config_file:
        config_file.write(config_content)
        print(f"Config file created at {config_path}")


import subprocess
import os

def generate_cert(host="127.0.0.1"):
    os.makedirs("certs", exist_ok=True)
    cert_path = "certs/cert.pem"
    key_path = "certs/key.pem"

    try:
        # instalar CA (solo la primera vez)
        subprocess.run(["mkcert", "-install"], check=True)

        # generar certificado
        subprocess.run([
            "mkcert",
            "-key-file", key_path,
            "-cert-file", cert_path,
            "localhost",
            "127.0.0.1",
            host
        ], check=True)

        print("✅ Certificado generado con mkcert")

    except Exception as e:
        print("❌ Error generando certificado:", e)
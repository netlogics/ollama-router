"""
SSL certificate management for ollama-router.
Handles self-signed certificate generation and management.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from src.config import SSLConfig


class SSLManager:
    """Manages SSL certificates for the router."""

    def __init__(self, config: SSLConfig):
        self.config = config
        self.cert_file = config.cert_path or config.cert_dir / "server.crt"
        self.key_file = config.key_path or config.cert_dir / "server.key"

    def ensure_certificates(self) -> tuple[Path, Path]:
        """Ensure certificates exist, generate if needed.

        Returns:
            Tuple of (cert_path, key_path)
        """
        if not self.config.auto_generate:
            if not self.cert_file.exists() or not self.key_file.exists():
                raise FileNotFoundError(
                    f"SSL certificates not found at {self.cert_file} and {self.key_file}. "
                    "Set auto_generate=True to create self-signed certificates."
                )
            return self.cert_file, self.key_file

        # Check if certificates exist and are valid
        if self._certificates_valid():
            return self.cert_file, self.key_file

        # Generate new certificates
        self._generate_self_signed_cert()
        return self.cert_file, self.key_file

    def _certificates_valid(self) -> bool:
        """Check if existing certificates are valid and not expired."""
        if not self.cert_file.exists() or not self.key_file.exists():
            return False

        try:
            with open(self.cert_file, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())

            # Check if expired
            if cert.not_valid_after_utc < datetime.utcnow():
                return False

            return True
        except Exception:
            return False

    def _generate_self_signed_cert(self) -> None:
        """Generate self-signed SSL certificates."""
        # Ensure cert directory exists
        self.config.cert_dir.mkdir(parents=True, exist_ok=True)

        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Subject and issuer (self-signed, so same)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Ollama Router"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ]
        )

        # Build certificate
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(
                datetime.utcnow() + timedelta(days=self.config.validity_days)
            )
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName("localhost"),
                        x509.IPAddress("127.0.0.1"),
                        x509.IPAddress("0.0.0.0"),
                    ]
                ),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        # Write certificate
        with open(self.cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Write private key
        with open(self.key_file, "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Set restrictive permissions on key file
        os.chmod(self.key_file, 0o600)

        print(f"Generated self-signed certificate: {self.cert_file}")
        print(f"Generated private key: {self.key_file}")
        print(f"Valid for {self.config.validity_days} days")

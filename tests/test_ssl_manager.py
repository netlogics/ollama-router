"""Test SSL certificate management."""

import pytest
from pathlib import Path
from src.ssl_manager import SSLManager
from src.config import SSLConfig


class TestSSLManager:
    """Tests for SSLManager."""

    def test_init_with_default_paths(self, tmp_path):
        """Test SSLManager uses default paths when cert_path is None."""
        config = SSLConfig(cert_dir=tmp_path)
        manager = SSLManager(config)
        
        assert manager.cert_file == tmp_path / "server.crt"
        assert manager.key_file == tmp_path / "server.key"

    def test_init_with_custom_paths(self, tmp_path):
        """Test SSLManager uses custom paths when provided."""
        config = SSLConfig(
            cert_path=tmp_path / "custom.crt",
            key_path=tmp_path / "custom.key",
        )
        manager = SSLManager(config)
        
        assert manager.cert_file == tmp_path / "custom.crt"
        assert manager.key_file == tmp_path / "custom.key"

    def test_ensure_certificates_generates_new_certs(self, tmp_path):
        """Test that ensure_certificates generates certs when they don't exist."""
        config = SSLConfig(cert_dir=tmp_path, auto_generate=True)
        manager = SSLManager(config)
        
        cert_path, key_path = manager.ensure_certificates()
        
        assert cert_path.exists()
        assert key_path.exists()
        assert cert_path == tmp_path / "server.crt"
        assert key_path == tmp_path / "server.key"

    def test_ensure_certificates_returns_existing_valid_certs(self, tmp_path):
        """Test that ensure_certificates returns existing valid certs without regenerating."""
        config = SSLConfig(cert_dir=tmp_path, auto_generate=True)
        manager = SSLManager(config)
        
        # First call generates certs
        cert_path1, key_path1 = manager.ensure_certificates()
        
        # Second call should return same paths
        cert_path2, key_path2 = manager.ensure_certificates()
        
        assert cert_path1 == cert_path2
        assert key_path1 == key_path2

    def test_ensure_certificates_raises_when_auto_generate_false_and_missing(self, tmp_path):
        """Test that ensure_certificates raises error when auto_generate=False and certs missing."""
        config = SSLConfig(
            cert_path=tmp_path / "nonexistent.crt",
            key_path=tmp_path / "nonexistent.key",
            auto_generate=False,
        )
        manager = SSLManager(config)
        
        with pytest.raises(FileNotFoundError) as exc_info:
            manager.ensure_certificates()
        
        assert "SSL certificates not found" in str(exc_info.value)
        assert "Set auto_generate=True" in str(exc_info.value)

    def test_ensure_certificates_returns_custom_certs_when_exist(self, tmp_path):
        """Test that ensure_certificates returns custom certs when they exist and auto_generate=False."""
        cert_file = tmp_path / "custom.crt"
        key_file = tmp_path / "custom.key"
        
        # Create dummy files
        cert_file.write_text("dummy cert")
        key_file.write_text("dummy key")
        
        config = SSLConfig(
            cert_path=cert_file,
            key_path=key_file,
            auto_generate=False,
        )
        manager = SSLManager(config)
        
        cert_path, key_path = manager.ensure_certificates()
        
        assert cert_path == cert_file
        assert key_path == key_file

    def test_certificates_valid_returns_false_when_files_missing(self, tmp_path):
        """Test _certificates_valid returns False when cert files don't exist."""
        config = SSLConfig(cert_dir=tmp_path)
        manager = SSLManager(config)
        
        assert manager._certificates_valid() is False

    def test_certificates_valid_returns_true_for_valid_cert(self, tmp_path):
        """Test _certificates_valid returns True for valid non-expired cert."""
        config = SSLConfig(cert_dir=tmp_path, auto_generate=True)
        manager = SSLManager(config)
        
        # Generate a cert
        manager.ensure_certificates()
        
        assert manager._certificates_valid() is True

    def test_generate_self_signed_cert_creates_proper_cert(self, tmp_path):
        """Test that generated certificate has correct properties."""
        from datetime import timedelta
        from cryptography import x509
        
        config = SSLConfig(cert_dir=tmp_path, validity_days=365)
        manager = SSLManager(config)
        
        manager._generate_self_signed_cert()
        
        cert_file = tmp_path / "server.crt"
        key_file = tmp_path / "server.key"
        
        # Verify files exist
        assert cert_file.exists()
        assert key_file.exists()
        
        # Load and verify certificate
        with open(cert_file, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        
        # Verify it's a self-signed cert
        assert cert.subject == cert.issuer
        
        # Verify subject attributes
        subject_dict = {attr.oid._name: attr.value for attr in cert.subject}
        assert subject_dict.get("countryName") == "US"
        assert subject_dict.get("organizationName") == "Ollama Router"
        assert subject_dict.get("commonName") == "localhost"
        
        # Verify validity period (approximately 365 days)
        duration = cert.not_valid_after_utc - cert.not_valid_before_utc
        assert duration.days >= 364  # Allow slight tolerance

    def test_generate_self_signed_cert_key_file_permissions(self, tmp_path):
        """Test that key file has restrictive permissions (0o600)."""
        import os
        
        config = SSLConfig(cert_dir=tmp_path)
        manager = SSLManager(config)
        
        manager._generate_self_signed_cert()
        
        key_file = tmp_path / "server.key"
        assert key_file.exists()
        
        # Check permissions
        mode = os.stat(key_file).st_mode
        assert mode & 0o777 == 0o600

    def test_cert_dir_created_if_not_exists(self, tmp_path):
        """Test that cert directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "certs"
        
        config = SSLConfig(cert_dir=nested_dir)
        manager = SSLManager(config)
        
        assert not nested_dir.exists()
        
        manager._generate_self_signed_cert()
        
        assert nested_dir.exists()

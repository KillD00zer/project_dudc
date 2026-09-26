"""
DUDC Lightweight Stream Encryption Engine (Module 3)
====================================================
Encrypts and decrypts 210-bit certificate payloads using the ChaCha20 stream cipher.
Key Features:
- Exact 1-to-1 bit length preservation (Zero bit expansion)
- In-memory key obfuscation using split seeds & runtime cryptographic hashing
- Master Passphrase verification for Director/Manager authorization
"""

import os
import hashlib
from typing import Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend

# ---------------------------------------------------------------------------
# Obfuscated Key Components (Assembled only in volatile memory at runtime)
# ---------------------------------------------------------------------------
_RAW_SEED_A = b"\x9e\x37\x79\xb9\x7f\x4a\x7c\x15\xf3\x9c\xc0\x60\x5d\xec\x47\x21"
_RAW_SEED_B = b"\xd1\x13\x8b\x45\x6b\x24\xa8\x91\x3f\x82\x71\x29\x5e\x3a\x99\x0b"
_OBFUSCATION_SALT = b"DUDC_DAKAHLIA_SECURE_TOKEN_SYSTEM_2026"

def _derive_runtime_key() -> bytes:
    """Dynamically reconstruct 256-bit symmetric stream key in memory."""
    hasher = hashlib.sha256()
    hasher.update(_RAW_SEED_A)
    hasher.update(_OBFUSCATION_SALT)
    hasher.update(_RAW_SEED_B)
    return hasher.digest()  # 32 bytes = 256 bits

# Fixed deterministic 16-byte nonce for reproducible stream cipher
_STREAM_NONCE = b"DUDC_NONCE_2026_"

def encrypt_210bits(payload_int: int) -> int:
    """
    Encrypt 210-bit integer using ChaCha20 stream cipher.
    Guarantees output stays strictly within 210 bits.
    """
    key = _derive_runtime_key()
    raw_bytes = payload_int.to_bytes(27, byteorder='big')
    
    algorithm = algorithms.ChaCha20(key, _STREAM_NONCE)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(raw_bytes)
    
    cipher_int = int.from_bytes(ciphertext, byteorder='big')
    mask_210 = (1 << 210) - 1
    return cipher_int & mask_210

def decrypt_210bits(cipher_int: int) -> int:
    """
    Decrypt 210-bit integer back to original payload using ChaCha20.
    """
    key = _derive_runtime_key()
    raw_bytes = cipher_int.to_bytes(27, byteorder='big')
    
    algorithm = algorithms.ChaCha20(key, _STREAM_NONCE)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(raw_bytes)
    
    plain_int = int.from_bytes(plaintext, byteorder='big')
    mask_210 = (1 << 210) - 1
    return plain_int & mask_210

# ---------------------------------------------------------------------------
# Manager Master Password Verification
# ---------------------------------------------------------------------------
# Default master password hash for Director: DUDC@Admin2026
_DEFAULT_MANAGER_HASH = hashlib.sha256(b"DUDC@Admin2026").hexdigest()

def verify_manager_password(password: str) -> bool:
    """Validate Director access password."""
    if not password:
        return False
    calc_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return calc_hash == _DEFAULT_MANAGER_HASH

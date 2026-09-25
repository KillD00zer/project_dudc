"""
DUDC Security System - RSA Key Pair Generator
============================================
Generates asymmetric cryptographic key pairs:
1. dudc_public.pem          -> Placed in src/keys/ for the certificate generator (Encryption only)
2. dudc_director_private.pem -> Kept exclusively in admin_tools/keys/ (Decryption only for Director)
"""

import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_key_pair(output_dir_admin=None, output_dir_src=None, passphrase=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if output_dir_admin is None:
        output_dir_admin = os.path.join(base_dir, "admin_tools", "keys")
    if output_dir_src is None:
        output_dir_src = os.path.join(base_dir, "src", "keys")
        
    os.makedirs(output_dir_admin, exist_ok=True)
    os.makedirs(output_dir_src, exist_ok=True)
    
    print("[1/3] Generating RSA-2048 Cryptographic Key Pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # 2. Serialize Private Key (Kept strictly with Director / Admin)
    encryption_algorithm = (
        serialization.BestAvailableEncryption(passphrase.encode('utf-8'))
        if passphrase else serialization.NoEncryption()
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm
    )
    
    private_path = os.path.join(output_dir_admin, "dudc_director_private.pem")
    with open(private_path, "wb") as f:
        f.write(private_pem)
    print(f"[2/3] Private Key saved to (STRICTLY PRIVATE): {private_path}")
    
    # 3. Serialize Public Key (Distributed with generator application)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    public_path = os.path.join(output_dir_src, "dudc_public.pem")
    with open(public_path, "wb") as f:
        f.write(public_pem)
        
    # Also save a backup of public key in admin directory
    with open(os.path.join(output_dir_admin, "dudc_public.pem"), "wb") as f:
        f.write(public_pem)
    print(f"[3/3] Public Key saved to: {public_path}")
    
    return private_path, public_path

if __name__ == "__main__":
    generate_key_pair()
    print("\nKeys generated successfully! System is ready for hybrid encryption.")

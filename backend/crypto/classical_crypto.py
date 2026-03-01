"""
QuantumGuard AI — Classical Cryptographic Implementations
RSA, ECC (ECDH), AES-GCM using the `cryptography` Python library.
All operations are real — no simulations.
"""
import os
import time
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class ClassicalCrypto:
    """Real cryptographic operations using pyca/cryptography."""

    def rsa_demo(self, key_size=2048):
        """Generate RSA keypair, encrypt a 32-byte message, decrypt it."""
        message = os.urandom(32)

        # Key generation
        t0 = time.perf_counter()
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        public_key = private_key.public_key()
        key_gen_ms = (time.perf_counter() - t0) * 1000

        # Serialize public key for size measurement
        pub_bytes = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Encrypt
        t0 = time.perf_counter()
        ciphertext = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        encrypt_ms = (time.perf_counter() - t0) * 1000

        # Decrypt
        t0 = time.perf_counter()
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        decrypt_ms = (time.perf_counter() - t0) * 1000

        success = plaintext == message

        return {
            "algorithm": f"RSA-{key_size}",
            "key_gen_ms": round(key_gen_ms, 3),
            "encrypt_ms": round(encrypt_ms, 3),
            "decrypt_ms": round(decrypt_ms, 3),
            "public_key_bytes": len(pub_bytes),
            "ciphertext_bytes": len(ciphertext),
            "success": success,
        }

    def ecc_demo(self, curve="P-256"):
        """ECDH key exchange: generate two keypairs, derive shared secret."""
        curve_map = {
            "P-256": ec.SECP256R1(),
            "P-384": ec.SECP384R1(),
            "P-521": ec.SECP521R1(),
        }
        curve_obj = curve_map.get(curve, ec.SECP256R1())

        # Key generation (two parties)
        t0 = time.perf_counter()
        private_key_a = ec.generate_private_key(curve_obj)
        private_key_b = ec.generate_private_key(curve_obj)
        public_key_a = private_key_a.public_key()
        public_key_b = private_key_b.public_key()
        key_gen_ms = (time.perf_counter() - t0) * 1000

        pub_bytes = public_key_a.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Key exchange
        t0 = time.perf_counter()
        shared_key_a = private_key_a.exchange(ec.ECDH(), public_key_b)
        shared_key_b = private_key_b.exchange(ec.ECDH(), public_key_a)
        exchange_ms = (time.perf_counter() - t0) * 1000

        # Derive keys with HKDF
        derived_a = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"QuantumGuard ECDH",
        ).derive(shared_key_a)
        derived_b = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"QuantumGuard ECDH",
        ).derive(shared_key_b)

        success = derived_a == derived_b

        return {
            "algorithm": f"ECC-{curve}",
            "key_gen_ms": round(key_gen_ms, 3),
            "exchange_ms": round(exchange_ms, 3),
            "encrypt_ms": round(exchange_ms, 3),  # for compatibility
            "decrypt_ms": 0.0,
            "public_key_bytes": len(pub_bytes),
            "shared_secret_hex": derived_a[:16].hex(),
            "success": success,
        }

    def aes_demo(self, key_size=256, data_size_kb=1):
        """AES-256-GCM encrypt/decrypt data_size_kb of random data."""
        data = os.urandom(data_size_kb * 1024)

        # Key generation
        t0 = time.perf_counter()
        key = AESGCM.generate_key(bit_length=key_size)
        key_gen_ms = (time.perf_counter() - t0) * 1000

        aesgcm = AESGCM(key)
        nonce = os.urandom(12)

        # Encrypt
        t0 = time.perf_counter()
        ciphertext = aesgcm.encrypt(nonce, data, None)
        encrypt_ms = (time.perf_counter() - t0) * 1000

        # Decrypt
        t0 = time.perf_counter()
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        decrypt_ms = (time.perf_counter() - t0) * 1000

        success = plaintext == data
        overhead = len(ciphertext) - len(data)  # GCM tag = 16 bytes

        return {
            "algorithm": f"AES-{key_size}-GCM",
            "key_gen_ms": round(key_gen_ms, 3),
            "encrypt_ms": round(encrypt_ms, 3),
            "decrypt_ms": round(decrypt_ms, 3),
            "key_bytes": key_size // 8,
            "public_key_bytes": key_size // 8,
            "ciphertext_overhead_bytes": overhead,
            "ciphertext_bytes": len(ciphertext),
            "success": success,
        }

    def rsa_1024_demo(self):
        """RSA-1024 demo (for CRITICAL risk demonstration)."""
        return self.rsa_demo(key_size=1024)

    def benchmark_all(self, iterations=50):
        """Run each algorithm `iterations` times and collect averages."""
        benchmarks = [
            ("RSA-1024", lambda: self.rsa_demo(1024)),
            ("RSA-2048", lambda: self.rsa_demo(2048)),
            ("ECC-P256", lambda: self.ecc_demo("P-256")),
            ("ECC-P384", lambda: self.ecc_demo("P-384")),
            ("AES-128-GCM", lambda: self.aes_demo(128, 1)),
            ("AES-256-GCM", lambda: self.aes_demo(256, 1)),
        ]

        results = []
        for algo_name, func in benchmarks:
            keygen_times = []
            encrypt_times = []
            decrypt_times = []
            key_size = 0
            ct_overhead = 0

            for _ in range(iterations):
                r = func()
                keygen_times.append(r.get("key_gen_ms", 0))
                encrypt_times.append(r.get("encrypt_ms", 0))
                decrypt_times.append(r.get("decrypt_ms", 0))
                key_size = r.get("public_key_bytes", 0)
                ct_overhead = r.get("ciphertext_overhead_bytes", r.get("ciphertext_bytes", 0))

            results.append({
                "algorithm": algo_name,
                "variant": algo_name,
                "avg_keygen_ms": round(sum(keygen_times) / len(keygen_times), 3),
                "avg_encrypt_ms": round(sum(encrypt_times) / len(encrypt_times), 3),
                "avg_decrypt_ms": round(sum(decrypt_times) / len(decrypt_times), 3),
                "key_size_bytes": key_size,
                "ciphertext_overhead_bytes": ct_overhead,
                "quantum_safe": False,
                "using_liboqs": False,
                "iterations": iterations,
            })

        return results

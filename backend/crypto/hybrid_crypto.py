"""
QuantumGuard AI — Hybrid Cryptography Module
Combines ECDH (classical) + Kyber (PQC) shared secrets via HKDF
to derive an AES-256-GCM session key.
"""
import os
import time
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from crypto.pqc_crypto import PQCCrypto


class HybridCrypto:
    """Implements the recommended transition strategy: ECDH + Kyber → HKDF → AES-256-GCM."""

    def __init__(self):
        self.pqc = PQCCrypto()

    def hybrid_kem_demo(self):
        """Full hybrid key exchange:
        1. ECDH key exchange → shared_secret_classical (32 bytes)
        2. Kyber-512 KEM → shared_secret_pqc (32 bytes)
        3. HKDF(classical || pqc) → session_key (32 bytes)
        4. AES-256-GCM encrypt 1KB test payload
        5. Decrypt and verify
        """
        test_payload = os.urandom(1024)  # 1KB test data

        # Step 1: ECDH key exchange
        t0 = time.perf_counter()
        ecdh_private_a = ec.generate_private_key(ec.SECP256R1())
        ecdh_private_b = ec.generate_private_key(ec.SECP256R1())
        ecdh_public_a = ecdh_private_a.public_key()
        ecdh_public_b = ecdh_private_b.public_key()
        ecdh_keygen_ms = (time.perf_counter() - t0) * 1000

        # ECDH shared secret
        shared_classical_a = ecdh_private_a.exchange(ec.ECDH(), ecdh_public_b)
        # Derive 32 bytes
        shared_secret_classical = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"QuantumGuard Hybrid ECDH",
        ).derive(shared_classical_a)

        ecdh_pub_bytes = ecdh_public_a.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Step 2: Kyber-512 KEM
        t0 = time.perf_counter()
        kyber_result = self.pqc.kyber_demo("Kyber512")
        kyber_keygen_ms = kyber_result["key_gen_ms"]

        # For simulation, shared_secret_pqc is derived from the Kyber result
        shared_secret_pqc = bytes.fromhex(
            kyber_result["shared_secret_hex"].ljust(64, "0")
        )[:32]

        # Step 3: HKDF to combine both secrets
        t0 = time.perf_counter()
        combined_secret = shared_secret_classical + shared_secret_pqc
        session_key = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"QuantumGuard Hybrid Session Key",
        ).derive(combined_secret)
        hybrid_exchange_ms = (time.perf_counter() - t0) * 1000

        # Step 4: AES-256-GCM encrypt
        t0 = time.perf_counter()
        aesgcm = AESGCM(session_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, test_payload, None)
        aes_encrypt_ms = (time.perf_counter() - t0) * 1000

        # Step 5: Decrypt and verify
        t0 = time.perf_counter()
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        aes_decrypt_ms = (time.perf_counter() - t0) * 1000

        success = plaintext == test_payload

        total_ms = (
            ecdh_keygen_ms + kyber_keygen_ms + hybrid_exchange_ms +
            aes_encrypt_ms + aes_decrypt_ms
        )

        return {
            "algorithm": "Hybrid-ECDH-Kyber512",
            "variant": "ECDH-P256 + Kyber-512 + AES-256-GCM",
            "ecdh_keygen_ms": round(ecdh_keygen_ms, 3),
            "kyber_keygen_ms": round(kyber_keygen_ms, 3),
            "hybrid_exchange_ms": round(hybrid_exchange_ms, 3),
            "aes_encrypt_ms": round(aes_encrypt_ms, 3),
            "aes_decrypt_ms": round(aes_decrypt_ms, 3),
            "total_ms": round(total_ms, 3),
            "key_gen_ms": round(ecdh_keygen_ms + kyber_keygen_ms, 3),
            "encrypt_ms": round(hybrid_exchange_ms + aes_encrypt_ms, 3),
            "decrypt_ms": round(aes_decrypt_ms, 3),
            "session_key_bits": 256,
            "ecdh_public_key_bytes": len(ecdh_pub_bytes),
            "kyber_public_key_bytes": kyber_result["public_key_bytes"],
            "public_key_bytes": len(ecdh_pub_bytes) + kyber_result["public_key_bytes"],
            "combined_ciphertext_bytes": len(ciphertext) + kyber_result["ciphertext_bytes"],
            "ciphertext_overhead_bytes": len(ciphertext) - len(test_payload) + kyber_result["ciphertext_bytes"],
            "quantum_safe": True,
            "using_liboqs": self.pqc.using_liboqs,
            "note": "Hybrid: breaks only if BOTH ECDH AND Kyber are broken",
            "success": success,
        }

    def benchmark_all(self, iterations=50):
        """Benchmark hybrid KEM."""
        keygen_times = []
        encrypt_times = []
        decrypt_times = []
        key_size = 0
        ct_overhead = 0
        is_liboqs = False

        for _ in range(iterations):
            r = self.hybrid_kem_demo()
            keygen_times.append(r.get("key_gen_ms", 0))
            encrypt_times.append(r.get("encrypt_ms", 0))
            decrypt_times.append(r.get("decrypt_ms", 0))
            key_size = r.get("public_key_bytes", 0)
            ct_overhead = r.get("ciphertext_overhead_bytes", 0)
            is_liboqs = r.get("using_liboqs", False)

        return [{
            "algorithm": "Hybrid-ECDH-Kyber512",
            "variant": "ECDH-P256 + Kyber-512 + AES-256-GCM",
            "avg_keygen_ms": round(sum(keygen_times) / len(keygen_times), 3),
            "avg_encrypt_ms": round(sum(encrypt_times) / len(encrypt_times), 3),
            "avg_decrypt_ms": round(sum(decrypt_times) / len(decrypt_times), 3),
            "key_size_bytes": key_size,
            "ciphertext_overhead_bytes": ct_overhead,
            "quantum_safe": True,
            "using_liboqs": is_liboqs,
            "iterations": iterations,
        }]

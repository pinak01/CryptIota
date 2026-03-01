"""
QuantumGuard AI — Post-Quantum Cryptography Module
Attempts to use liboqs for real Kyber/Dilithium/Falcon.
Falls back to mathematically realistic simulation if liboqs not available.
"""
import os
import time
import hashlib
import struct


class PQCCrypto:
    """Post-Quantum Cryptographic operations (Kyber, Dilithium, Falcon)."""

    # Real Kyber spec sizes (NIST Round 3 / FIPS 203)
    KYBER_SPECS = {
        "Kyber512": {"pubkey": 800, "ciphertext": 768, "secret": 32, "level": 1},
        "Kyber768": {"pubkey": 1184, "ciphertext": 1088, "secret": 32, "level": 3},
        "Kyber1024": {"pubkey": 1568, "ciphertext": 1568, "secret": 32, "level": 5},
    }

    # Real Dilithium spec sizes (NIST FIPS 204)
    DILITHIUM_SPECS = {
        "Dilithium2": {"pubkey": 1312, "signature": 2420, "level": 2},
        "Dilithium3": {"pubkey": 1952, "signature": 3293, "level": 3},
        "Dilithium5": {"pubkey": 2592, "signature": 4595, "level": 5},
    }

    # Falcon spec sizes
    FALCON_SPECS = {
        "Falcon-512": {"pubkey": 897, "signature": 690, "level": 1},
    }

    # Realistic timing baselines (ms per operation, from real benchmarks on ~3GHz CPU)
    TIMING_BASELINES = {
        "Kyber512": {"keygen": 0.08, "encap": 0.10, "decap": 0.12},
        "Kyber768": {"keygen": 0.12, "encap": 0.15, "decap": 0.18},
        "Kyber1024": {"keygen": 0.18, "encap": 0.22, "decap": 0.25},
        "Dilithium2": {"keygen": 0.15, "sign": 0.50, "verify": 0.15},
        "Dilithium3": {"keygen": 0.25, "sign": 0.80, "verify": 0.25},
        "Dilithium5": {"keygen": 0.40, "sign": 1.20, "verify": 0.40},
        "Falcon-512": {"keygen": 8.0, "sign": 0.40, "verify": 0.08},
    }

    def __init__(self):
        """Try to import liboqs. Set fallback mode if unavailable."""
        self.using_liboqs = False
        self.oqs = None

        try:
            import oqs
            self.oqs = oqs
            self.using_liboqs = True
            print("[PQC] liboqs loaded — using real post-quantum algorithms")
        except ImportError:
            print("[PQC] ⚠ liboqs not found — using simulated PQC "
                  "(realistic timing + sizes based on NIST specs)")

    # ------------------------------------------------------------------
    # Simulation helpers — use real crypto primitives for computation
    # to produce realistic timings (not time.sleep)
    # ------------------------------------------------------------------

    def _simulate_lattice_operation(self, complexity_factor: int):
        """Simulate lattice-based crypto computation using real hash work.
        Uses iterative hashing to produce realistic CPU-bound timing
        proportional to the complexity factor.
        """
        data = os.urandom(64)
        for _ in range(complexity_factor):
            data = hashlib.sha3_256(data).digest() + hashlib.sha3_256(
                data + struct.pack(">I", complexity_factor)
            ).digest()
        return data

    # ------------------------------------------------------------------
    # KYBER KEM
    # ------------------------------------------------------------------

    def kyber_demo(self, variant="Kyber512"):
        """Kyber KEM: keygen → encapsulate → decapsulate."""
        spec = self.KYBER_SPECS.get(variant, self.KYBER_SPECS["Kyber512"])

        if self.using_liboqs:
            return self._kyber_liboqs(variant, spec)
        return self._kyber_simulated(variant, spec)

    def _kyber_liboqs(self, variant, spec):
        """Real Kyber using liboqs."""
        kem_name = f"ML-KEM-{variant.replace('Kyber', '')}"
        try:
            kem = self.oqs.KeyEncapsulation(kem_name)
        except Exception:
            # Fallback name format
            kem = self.oqs.KeyEncapsulation(variant)

        # Keygen
        t0 = time.perf_counter()
        public_key = kem.generate_keypair()
        key_gen_ms = (time.perf_counter() - t0) * 1000

        # Encapsulate
        t0 = time.perf_counter()
        ciphertext, shared_secret_enc = kem.encap_secret(public_key)
        encap_ms = (time.perf_counter() - t0) * 1000

        # Decapsulate
        t0 = time.perf_counter()
        shared_secret_dec = kem.decap_secret(ciphertext)
        decap_ms = (time.perf_counter() - t0) * 1000

        success = shared_secret_enc == shared_secret_dec

        return {
            "algorithm": variant,
            "variant": variant,
            "key_gen_ms": round(key_gen_ms, 3),
            "encap_ms": round(encap_ms, 3),
            "decap_ms": round(decap_ms, 3),
            "encrypt_ms": round(encap_ms, 3),
            "decrypt_ms": round(decap_ms, 3),
            "public_key_bytes": len(public_key),
            "ciphertext_bytes": len(ciphertext),
            "ciphertext_overhead_bytes": len(ciphertext),
            "shared_secret_hex": shared_secret_enc[:16].hex(),
            "using_liboqs": True,
            "quantum_safe": True,
            "success": success,
        }

    def _kyber_simulated(self, variant, spec):
        """Simulated Kyber with realistic computation."""
        timing = self.TIMING_BASELINES[variant]
        complexity = spec["level"] * 200

        # Keygen — simulate lattice key generation
        t0 = time.perf_counter()
        key_material = self._simulate_lattice_operation(complexity)
        public_key = key_material[:spec["pubkey"] % 64] + os.urandom(spec["pubkey"] - (spec["pubkey"] % 64))
        key_gen_ms = (time.perf_counter() - t0) * 1000

        # Encapsulate
        t0 = time.perf_counter()
        ct_material = self._simulate_lattice_operation(complexity)
        shared_secret_enc = hashlib.sha3_256(ct_material).digest()
        encap_ms = (time.perf_counter() - t0) * 1000

        # Decapsulate
        t0 = time.perf_counter()
        dec_material = self._simulate_lattice_operation(complexity)
        shared_secret_dec = shared_secret_enc  # In simulation, always succeeds
        decap_ms = (time.perf_counter() - t0) * 1000

        return {
            "algorithm": variant,
            "variant": variant,
            "key_gen_ms": round(key_gen_ms, 3),
            "encap_ms": round(encap_ms, 3),
            "decap_ms": round(decap_ms, 3),
            "encrypt_ms": round(encap_ms, 3),
            "decrypt_ms": round(decap_ms, 3),
            "public_key_bytes": spec["pubkey"],
            "ciphertext_bytes": spec["ciphertext"],
            "ciphertext_overhead_bytes": spec["ciphertext"],
            "shared_secret_hex": shared_secret_enc[:16].hex(),
            "using_liboqs": False,
            "quantum_safe": True,
            "success": True,
            "note": "Simulated — install liboqs for real measurements",
        }

    # ------------------------------------------------------------------
    # DILITHIUM Digital Signatures
    # ------------------------------------------------------------------

    def dilithium_demo(self, variant="Dilithium2"):
        """Dilithium signature: keygen → sign → verify."""
        spec = self.DILITHIUM_SPECS.get(variant, self.DILITHIUM_SPECS["Dilithium2"])

        if self.using_liboqs:
            return self._dilithium_liboqs(variant, spec)
        return self._dilithium_simulated(variant, spec)

    def _dilithium_liboqs(self, variant, spec):
        """Real Dilithium using liboqs."""
        level = variant.replace("Dilithium", "")
        sig_name = f"ML-DSA-{level}"
        try:
            sig = self.oqs.Signature(sig_name)
        except Exception:
            sig = self.oqs.Signature(variant)

        message = b"QuantumGuard AI test message for digital signature verification"

        # Keygen
        t0 = time.perf_counter()
        public_key = sig.generate_keypair()
        key_gen_ms = (time.perf_counter() - t0) * 1000

        # Sign
        t0 = time.perf_counter()
        signature = sig.sign(message)
        sign_ms = (time.perf_counter() - t0) * 1000

        # Verify
        t0 = time.perf_counter()
        valid = sig.verify(message, signature, public_key)
        verify_ms = (time.perf_counter() - t0) * 1000

        return {
            "algorithm": variant,
            "variant": variant,
            "key_gen_ms": round(key_gen_ms, 3),
            "sign_ms": round(sign_ms, 3),
            "verify_ms": round(verify_ms, 3),
            "encrypt_ms": round(sign_ms, 3),
            "decrypt_ms": round(verify_ms, 3),
            "public_key_bytes": len(public_key),
            "signature_bytes": len(signature),
            "ciphertext_overhead_bytes": len(signature),
            "using_liboqs": True,
            "quantum_safe": True,
            "success": valid,
        }

    def _dilithium_simulated(self, variant, spec):
        """Simulated Dilithium with realistic computation."""
        timing = self.TIMING_BASELINES[variant]
        complexity = spec["level"] * 300

        message = b"QuantumGuard AI test message for digital signature verification"

        # Keygen
        t0 = time.perf_counter()
        key_material = self._simulate_lattice_operation(complexity)
        key_gen_ms = (time.perf_counter() - t0) * 1000

        # Sign
        t0 = time.perf_counter()
        sig_material = self._simulate_lattice_operation(complexity * 2)
        signature = hashlib.sha3_512(sig_material + message).digest()
        sign_ms = (time.perf_counter() - t0) * 1000

        # Verify
        t0 = time.perf_counter()
        verify_material = self._simulate_lattice_operation(complexity)
        verify_ms = (time.perf_counter() - t0) * 1000

        return {
            "algorithm": variant,
            "variant": variant,
            "key_gen_ms": round(key_gen_ms, 3),
            "sign_ms": round(sign_ms, 3),
            "verify_ms": round(verify_ms, 3),
            "encrypt_ms": round(sign_ms, 3),
            "decrypt_ms": round(verify_ms, 3),
            "public_key_bytes": spec["pubkey"],
            "signature_bytes": spec["signature"],
            "ciphertext_overhead_bytes": spec["signature"],
            "using_liboqs": False,
            "quantum_safe": True,
            "success": True,
            "note": "Simulated — install liboqs for real measurements",
        }

    # ------------------------------------------------------------------
    # FALCON Digital Signatures
    # ------------------------------------------------------------------

    def falcon_demo(self):
        """FALCON-512 signature demo."""
        spec = self.FALCON_SPECS["Falcon-512"]

        if self.using_liboqs:
            return self._falcon_liboqs(spec)
        return self._falcon_simulated(spec)

    def _falcon_liboqs(self, spec):
        """Real Falcon using liboqs."""
        try:
            sig = self.oqs.Signature("Falcon-512")
        except Exception:
            return self._falcon_simulated(spec)

        message = b"QuantumGuard AI Falcon signature test"

        t0 = time.perf_counter()
        public_key = sig.generate_keypair()
        key_gen_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        signature = sig.sign(message)
        sign_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        valid = sig.verify(message, signature, public_key)
        verify_ms = (time.perf_counter() - t0) * 1000

        return {
            "algorithm": "Falcon-512",
            "variant": "Falcon-512",
            "key_gen_ms": round(key_gen_ms, 3),
            "sign_ms": round(sign_ms, 3),
            "verify_ms": round(verify_ms, 3),
            "encrypt_ms": round(sign_ms, 3),
            "decrypt_ms": round(verify_ms, 3),
            "public_key_bytes": len(public_key),
            "signature_bytes": len(signature),
            "ciphertext_overhead_bytes": len(signature),
            "using_liboqs": True,
            "quantum_safe": True,
            "success": valid,
        }

    def _falcon_simulated(self, spec):
        """Simulated Falcon-512."""
        message = b"QuantumGuard AI Falcon signature test"

        # Falcon keygen is notably slow (tree-based)
        t0 = time.perf_counter()
        self._simulate_lattice_operation(2000)
        key_gen_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        self._simulate_lattice_operation(500)
        sign_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        self._simulate_lattice_operation(200)
        verify_ms = (time.perf_counter() - t0) * 1000

        return {
            "algorithm": "Falcon-512",
            "variant": "Falcon-512",
            "key_gen_ms": round(key_gen_ms, 3),
            "sign_ms": round(sign_ms, 3),
            "verify_ms": round(verify_ms, 3),
            "encrypt_ms": round(sign_ms, 3),
            "decrypt_ms": round(verify_ms, 3),
            "public_key_bytes": spec["pubkey"],
            "signature_bytes": spec["signature"],
            "ciphertext_overhead_bytes": spec["signature"],
            "using_liboqs": False,
            "quantum_safe": True,
            "success": True,
            "note": "Simulated — install liboqs for real measurements",
        }

    # ------------------------------------------------------------------
    # Benchmark all PQC algorithms
    # ------------------------------------------------------------------

    def benchmark_all(self, iterations=50):
        """Benchmark all PQC algorithms."""
        configs = [
            ("Kyber512", lambda: self.kyber_demo("Kyber512")),
            ("Kyber768", lambda: self.kyber_demo("Kyber768")),
            ("Kyber1024", lambda: self.kyber_demo("Kyber1024")),
            ("Dilithium2", lambda: self.dilithium_demo("Dilithium2")),
            ("Dilithium3", lambda: self.dilithium_demo("Dilithium3")),
        ]

        results = []
        for algo_name, func in configs:
            keygen_times = []
            encrypt_times = []
            decrypt_times = []
            key_size = 0
            ct_overhead = 0
            is_liboqs = False

            for _ in range(iterations):
                r = func()
                keygen_times.append(r.get("key_gen_ms", 0))
                encrypt_times.append(r.get("encrypt_ms", 0))
                decrypt_times.append(r.get("decrypt_ms", 0))
                key_size = r.get("public_key_bytes", 0)
                ct_overhead = r.get("ciphertext_overhead_bytes", 0)
                is_liboqs = r.get("using_liboqs", False)

            results.append({
                "algorithm": algo_name,
                "variant": algo_name,
                "avg_keygen_ms": round(sum(keygen_times) / len(keygen_times), 3),
                "avg_encrypt_ms": round(sum(encrypt_times) / len(encrypt_times), 3),
                "avg_decrypt_ms": round(sum(decrypt_times) / len(decrypt_times), 3),
                "key_size_bytes": key_size,
                "ciphertext_overhead_bytes": ct_overhead,
                "quantum_safe": True,
                "using_liboqs": is_liboqs,
                "iterations": iterations,
            })

        return results

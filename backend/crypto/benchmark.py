"""
QuantumGuard AI — Unified Crypto Benchmark
Orchestrates benchmarks across classical, PQC, and hybrid modules.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crypto.classical_crypto import ClassicalCrypto
from crypto.pqc_crypto import PQCCrypto
from crypto.hybrid_crypto import HybridCrypto


class CryptoBenchmark:
    """Orchestrates all benchmarks and returns unified results."""

    def __init__(self):
        self.classical = ClassicalCrypto()
        self.pqc = PQCCrypto()
        self.hybrid = HybridCrypto()

    def run_full_benchmark(self, iterations=50):
        """Run all benchmark suites and combine results.
        Optionally stores results in the SQLite database.
        """
        print(f"[Benchmark] Running full benchmark ({iterations} iterations)...")

        # Classical
        print("  [1/3] Classical algorithms...")
        classical_results = self.classical.benchmark_all(iterations)

        # PQC
        print("  [2/3] Post-quantum algorithms...")
        pqc_results = self.pqc.benchmark_all(iterations)

        # Hybrid
        print("  [3/3] Hybrid algorithms...")
        hybrid_results = self.hybrid.benchmark_all(iterations)

        all_results = classical_results + pqc_results + hybrid_results

        # Store in database
        self._store_results(all_results, iterations)

        print(f"[Benchmark] Complete — {len(all_results)} algorithms benchmarked.")
        return all_results

    def _store_results(self, results, iterations):
        """Store benchmark results in the database."""
        try:
            from database import get_db
            from models import CryptoBenchmarkResult

            db = get_db()
            for r in results:
                entry = CryptoBenchmarkResult(
                    algorithm=r["algorithm"],
                    variant=r.get("variant", r["algorithm"]),
                    avg_keygen_ms=r.get("avg_keygen_ms"),
                    avg_encrypt_ms=r.get("avg_encrypt_ms"),
                    avg_decrypt_ms=r.get("avg_decrypt_ms"),
                    key_size_bytes=r.get("key_size_bytes"),
                    ciphertext_overhead_bytes=r.get("ciphertext_overhead_bytes"),
                    quantum_safe=1 if r.get("quantum_safe") else 0,
                    using_liboqs=1 if r.get("using_liboqs") else 0,
                    iterations=iterations,
                    benchmarked_at=datetime.utcnow(),
                )
                db.add(entry)
            db.commit()
            db.close()
            print("  [✓] Results stored in database.")
        except Exception as e:
            print(f"  [!] Could not store in DB: {e}")

    def get_comparison_summary(self):
        """Return a comparison dict suitable for frontend charts."""
        try:
            from database import get_db
            from models import CryptoBenchmarkResult

            db = get_db()
            # Get most recent benchmark run for each algorithm
            results = (
                db.query(CryptoBenchmarkResult)
                .order_by(CryptoBenchmarkResult.benchmarked_at.desc())
                .all()
            )
            db.close()

            if not results:
                return self._empty_comparison()

            # Deduplicate: keep only the most recent per algorithm
            seen = {}
            for r in results:
                if r.algorithm not in seen:
                    seen[r.algorithm] = r

            algos = list(seen.values())

            return {
                "algorithms": [a.algorithm for a in algos],
                "keygen_times": [a.avg_keygen_ms for a in algos],
                "encrypt_times": [a.avg_encrypt_ms for a in algos],
                "decrypt_times": [a.avg_decrypt_ms for a in algos],
                "key_sizes": [a.key_size_bytes for a in algos],
                "ciphertext_sizes": [a.ciphertext_overhead_bytes for a in algos],
                "quantum_safe": [bool(a.quantum_safe) for a in algos],
                "using_liboqs": [bool(a.using_liboqs) for a in algos],
                "details": [a.to_dict() for a in algos],
            }
        except Exception as e:
            print(f"[Benchmark] Error getting comparison: {e}")
            return self._empty_comparison()

    def _empty_comparison(self):
        return {
            "algorithms": [],
            "keygen_times": [],
            "encrypt_times": [],
            "decrypt_times": [],
            "key_sizes": [],
            "ciphertext_sizes": [],
            "quantum_safe": [],
            "using_liboqs": [],
            "details": [],
        }

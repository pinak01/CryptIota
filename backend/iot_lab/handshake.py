"""
QuantumGuard AI — IoT Security Lab: Cryptographic Handshake Engine
Supports PQC (Kyber), Classical (ECDH), and Hybrid session establishment.
"""
import os
import time
import uuid
import hashlib
from datetime import datetime, timedelta

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Try to import liboqs for real PQC
try:
    import oqs
    HAS_LIBOQS = True
except ImportError:
    HAS_LIBOQS = False


# ---------------------------------------------------------------------------
# In-memory session store (session keys never hit the DB)
# ---------------------------------------------------------------------------
_active_sessions = {}  # session_id -> { key, nonces_used, mode, device_id, ... }


def _derive_key(shared_secret: bytes, session_id: str) -> bytes:
    """HKDF-SHA256 to derive a 32-byte AES-256 session key."""
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=session_id.encode(),
        info=b"QuantumGuard IoT Lab",
    ).derive(shared_secret)


# ---------------------------------------------------------------------------
# Handshake: Init (server generates keypair, returns public key)
# ---------------------------------------------------------------------------

def handshake_init(device_id: int, mode: str):
    """
    Phase 1: Server generates keypair.
    Returns session_id + server's public key (hex) for the device.
    """
    session_id = str(uuid.uuid4())
    t0 = time.perf_counter()

    if mode == "pqc":
        result = _init_pqc(session_id)
    elif mode == "classical":
        result = _init_classical(session_id)
    elif mode == "hybrid":
        result = _init_hybrid(session_id)
    else:
        raise ValueError(f"Unknown mode: {mode}. Use pqc/classical/hybrid.")

    init_time_ms = (time.perf_counter() - t0) * 1000

    # Store pending session
    _active_sessions[session_id] = {
        **result["_internal"],
        "device_id": device_id,
        "mode": mode,
        "init_time_ms": init_time_ms,
        "init_at": datetime.utcnow(),
        "nonces_used": set(),
        "nonce_counter": 0,
    }

    return {
        "session_id": session_id,
        "mode": mode,
        "server_public_key": result["server_public_key_hex"],
        "key_bytes": result["key_bytes"],
        "using_liboqs": HAS_LIBOQS if mode in ("pqc", "hybrid") else False,
    }


def _init_pqc(session_id: str):
    """Generate Kyber-512 keypair."""
    if HAS_LIBOQS:
        kem = oqs.KeyEncapsulation("ML-KEM-512")
        public_key = kem.generate_keypair()
        return {
            "server_public_key_hex": public_key.hex(),
            "key_bytes": len(public_key),
            "_internal": {"kem_obj": kem, "pubkey_raw": public_key},
        }
    else:
        # Simulated: generate random bytes matching Kyber-512 public key size
        fake_pk = os.urandom(800)
        fake_sk = os.urandom(32)
        return {
            "server_public_key_hex": fake_pk.hex(),
            "key_bytes": 800,
            "_internal": {"simulated_sk": fake_sk, "simulated_pk": fake_pk},
        }


def _init_classical(session_id: str):
    """Generate ECDH P-256 keypair."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    return {
        "server_public_key_hex": pub_bytes.hex(),
        "key_bytes": len(pub_bytes),
        "_internal": {"ecdh_private": private_key, "pubkey_raw": pub_bytes},
    }


def _init_hybrid(session_id: str):
    """Generate both ECDH + Kyber keypairs for hybrid mode."""
    pqc_result = _init_pqc(session_id)
    classical_result = _init_classical(session_id)

    combined_key_hex = classical_result["server_public_key_hex"] + "|" + pqc_result["server_public_key_hex"]

    return {
        "server_public_key_hex": combined_key_hex,
        "key_bytes": classical_result["key_bytes"] + pqc_result["key_bytes"],
        "_internal": {
            **{f"classical_{k}": v for k, v in classical_result["_internal"].items()},
            **{f"pqc_{k}": v for k, v in pqc_result["_internal"].items()},
        },
    }


# ---------------------------------------------------------------------------
# Handshake: Complete (device sends ciphertext/pubkey, server derives key)
# ---------------------------------------------------------------------------

def handshake_complete(session_id: str, device_data: dict):
    """
    Phase 2: Device sends its ciphertext (PQC) or public key (classical).
    Server derives the shared session key. Returns metrics.
    """
    if session_id not in _active_sessions:
        raise ValueError(f"Unknown session: {session_id}")

    sess = _active_sessions[session_id]
    mode = sess["mode"]
    t0 = time.perf_counter()

    if mode == "pqc":
        shared_secret, ct_bytes = _complete_pqc(sess, device_data)
    elif mode == "classical":
        shared_secret, ct_bytes = _complete_classical(sess, device_data)
    elif mode == "hybrid":
        shared_secret, ct_bytes = _complete_hybrid(sess, device_data)
    else:
        raise ValueError(f"Unknown mode in session: {mode}")

    # Derive session key
    session_key = _derive_key(shared_secret, session_id)
    total_handshake_ms = (time.perf_counter() - t0) * 1000 + sess["init_time_ms"]

    # Store in session
    sess["session_key"] = session_key
    sess["established"] = True
    sess["handshake_time_ms"] = total_handshake_ms
    sess["shared_secret_hash"] = hashlib.sha256(shared_secret).hexdigest()
    sess["ciphertext_bytes"] = ct_bytes
    sess["established_at"] = datetime.utcnow()
    sess["expires_at"] = datetime.utcnow() + timedelta(hours=1)

    # Device-side metrics (optional, reported by ESP32)
    sess["device_cpu_time_ms"] = device_data.get("device_cpu_time_ms")
    sess["device_free_heap_before"] = device_data.get("free_heap_before")
    sess["device_free_heap_after"] = device_data.get("free_heap_after")

    return {
        "status": "established",
        "session_id": session_id,
        "mode": mode,
        "handshake_time_ms": round(total_handshake_ms, 3),
        "public_key_bytes": sess.get("key_bytes_actual", 0),
        "ciphertext_bytes": ct_bytes,
        "shared_secret_hash": sess["shared_secret_hash"][:16],
        "using_liboqs": HAS_LIBOQS if mode in ("pqc", "hybrid") else False,
        "session_expires_at": sess["expires_at"].isoformat(),
    }


def _complete_pqc(sess, device_data):
    """Decapsulate Kyber ciphertext from device."""
    ct_hex = device_data.get("device_ciphertext", "")

    if HAS_LIBOQS:
        kem = sess.get("kem_obj")
        if not kem:
            raise ValueError("No KEM object in session (liboqs)")
        ciphertext = bytes.fromhex(ct_hex)
        shared_secret = kem.decap_secret(ciphertext)
        sess["key_bytes_actual"] = len(sess.get("pubkey_raw", b""))
        return shared_secret, len(ciphertext)
    else:
        # Simulated: derive from ciphertext hash
        ct_bytes = bytes.fromhex(ct_hex) if ct_hex else os.urandom(768)
        shared_secret = hashlib.sha3_256(ct_bytes + sess.get("simulated_sk", b"")).digest()
        sess["key_bytes_actual"] = 800
        return shared_secret, len(ct_bytes)


def _complete_classical(sess, device_data):
    """ECDH key exchange using device's public key."""
    dev_pub_hex = device_data.get("device_public_key", "")

    if dev_pub_hex:
        dev_pub_bytes = bytes.fromhex(dev_pub_hex)
        device_pub_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), dev_pub_bytes
        )
        shared_secret = sess["ecdh_private"].exchange(ec.ECDH(), device_pub_key)
    else:
        # Simulated: generate device side on server
        dev_priv = ec.generate_private_key(ec.SECP256R1())
        dev_pub = dev_priv.public_key()
        shared_secret = sess["ecdh_private"].exchange(ec.ECDH(), dev_pub)

    sess["key_bytes_actual"] = len(sess.get("pubkey_raw", b""))
    return shared_secret, 0  # No ciphertext for ECDH


def _complete_hybrid(sess, device_data):
    """Combine both ECDH and Kyber shared secrets."""
    # Classical part
    classical_sess = {"ecdh_private": sess.get("classical_ecdh_private")}
    classical_sess["pubkey_raw"] = sess.get("classical_pubkey_raw", b"")
    classical_secret, _ = _complete_classical(classical_sess, device_data)

    # PQC part
    pqc_sess = {
        "kem_obj": sess.get("pqc_kem_obj"),
        "simulated_sk": sess.get("pqc_simulated_sk", b""),
        "pubkey_raw": sess.get("pqc_pubkey_raw", b""),
    }
    pqc_secret, ct_bytes = _complete_pqc(pqc_sess, device_data)

    # Combine
    combined = classical_secret + pqc_secret
    sess["key_bytes_actual"] = len(classical_sess["pubkey_raw"]) + len(pqc_sess.get("pubkey_raw", b""))
    return combined, ct_bytes


# ---------------------------------------------------------------------------
# Telemetry: Decrypt + validate
# ---------------------------------------------------------------------------

def process_telemetry(session_id: str, encrypted_payload_hex: str,
                      iv_hex: str, tag_hex: str, nonce: int):
    """
    Decrypt and validate incoming telemetry.
    Returns (plaintext_bytes, attack_type_or_none).
    """
    if session_id not in _active_sessions:
        return None, "mitm"  # Unknown session = possible MITM

    sess = _active_sessions[session_id]

    if not sess.get("established"):
        return None, "mitm"

    # Check session expiry
    if datetime.utcnow() > sess.get("expires_at", datetime.utcnow()):
        return None, "mitm"

    # Replay detection
    if nonce in sess["nonces_used"]:
        return None, "replay"

    if nonce <= sess["nonce_counter"] and sess["nonce_counter"] > 0:
        return None, "replay"

    # Try decryption
    try:
        session_key = sess["session_key"]
        aesgcm = AESGCM(session_key)
        iv = bytes.fromhex(iv_hex)
        ciphertext_with_tag = bytes.fromhex(encrypted_payload_hex) + bytes.fromhex(tag_hex)
        plaintext = aesgcm.decrypt(iv, ciphertext_with_tag, None)

        # Update nonce tracking
        sess["nonces_used"].add(nonce)
        sess["nonce_counter"] = max(sess["nonce_counter"], nonce)

        return plaintext, None
    except Exception:
        return None, "tampering"


def encrypt_telemetry(session_id: str, plaintext: bytes):
    """
    Server-side encryption helper (used for simulation).
    Returns (encrypted_payload_hex, iv_hex, tag_hex, nonce).
    """
    if session_id not in _active_sessions:
        raise ValueError(f"Unknown session: {session_id}")

    sess = _active_sessions[session_id]
    session_key = sess["session_key"]

    aesgcm = AESGCM(session_key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    # AES-GCM appends 16-byte tag
    payload = ciphertext[:-16]
    tag = ciphertext[-16:]
    nonce = sess["nonce_counter"] + 1

    return payload.hex(), iv.hex(), tag.hex(), nonce


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def get_session(session_id: str):
    """Get session info (safe, no key material)."""
    sess = _active_sessions.get(session_id)
    if not sess:
        return None
    return {
        "session_id": session_id,
        "device_id": sess.get("device_id"),
        "mode": sess.get("mode"),
        "established": sess.get("established", False),
        "handshake_time_ms": sess.get("handshake_time_ms"),
        "shared_secret_hash": sess.get("shared_secret_hash", "")[:16],
        "nonce_counter": sess.get("nonce_counter", 0),
        "ciphertext_bytes": sess.get("ciphertext_bytes", 0),
        "key_bytes_actual": sess.get("key_bytes_actual", 0),
        "device_cpu_time_ms": sess.get("device_cpu_time_ms"),
        "device_free_heap_before": sess.get("device_free_heap_before"),
        "device_free_heap_after": sess.get("device_free_heap_after"),
    }


def list_active_sessions():
    """Return all active session IDs and their metadata."""
    return [
        get_session(sid)
        for sid, sess in _active_sessions.items()
        if sess.get("established")
    ]


def get_session_key_exists(session_id: str) -> bool:
    """Check if a session has a valid key (without exposing it)."""
    sess = _active_sessions.get(session_id)
    return sess is not None and "session_key" in sess

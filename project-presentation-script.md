# QuantumGuard AI Presentation Script

## 1. Opening

Good morning. My project is **QuantumGuard AI**, a risk-aware post-quantum cryptographic migration platform for IoT systems.

The main problem I am addressing is that many IoT devices still use classical cryptography such as RSA and ECC. These are secure today against classical attackers, but they become vulnerable in a future where large-scale quantum computers are available. That creates a serious "harvest now, decrypt later" risk, especially for devices handling sensitive data with long retention periods.

So instead of waiting for quantum computers to become practical, this project helps organizations identify which devices are most exposed, classify their risk, and generate a migration path toward post-quantum or hybrid cryptography.

## 2. What The Project Does

At a high level, the system has four major capabilities:

1. It stores and manages IoT device profiles.
2. It uses a machine learning model to classify each device into `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` quantum risk.
3. It benchmarks cryptographic algorithms across classical, post-quantum, and hybrid approaches.
4. It converts the risk result into an actionable migration roadmap.

This makes the project more than just a dashboard. It is a decision-support system for quantum-safe migration.

## 3. System Architecture

The project is divided into two main parts:

- The **frontend** is built in React and displays the dashboard, device inventory, heatmap, benchmark view, migration planner, and CSV upload screen.
- The **backend** is built with Flask and contains the core logic: database handling, ML inference, crypto demonstrations, benchmark orchestration, report generation, and migration policy decisions.

The database layer uses **SQLite with SQLAlchemy ORM**. The key backend entities are:

- `Device`
- `RiskAssessment`
- `CryptoBenchmarkResult`
- `MigrationPlan`
- `Alert`

So the flow is: device data comes in, the ML model scores it, the policy engine recommends a strategy, and the frontend visualizes the results.

## 4. Machine Learning Pipeline

The ML part of the project is inside the `backend/ml` folder.

The classifier uses a trained model plus a preprocessing pipeline. The input features include:

- device type
- encryption algorithm
- data sensitivity
- retention period
- network exposure
- update capability
- battery status
- CPU and RAM
- key rotation period
- deployment age
- connected device count
- daily data volume

The training pipeline does the following:

1. Loads the IoT dataset.
2. Separates features and target risk labels.
3. Applies preprocessing using a `ColumnTransformer`.
4. Encodes categorical values and scales numeric features.
5. Uses **SMOTE** to balance the classes.
6. Trains three models:
   - Random Forest
   - Gradient Boosting
   - Logistic Regression
7. Evaluates them using stratified 5-fold cross-validation and macro F1-score.
8. Saves the best model, the preprocessor, and metadata.

During inference, the classifier predicts:

- the final risk level
- confidence scores for each class
- a weighted overall risk score from 0 to 1

This is useful because the system does not only say "high risk"; it also explains how strong that prediction is.

## 5. Backend Decision Logic

After the ML model produces a risk level, the **MigrationPolicyEngine** translates that into a real recommendation.

The mapping is:

- `CRITICAL` -> full post-quantum migration
- `HIGH` -> hybrid migration
- `MEDIUM` -> staged long-term migration
- `LOW` -> continue monitoring

It also calculates a **priority score**. That score is not only based on ML risk. It is adjusted using real-world operational factors such as:

- device type
- whether the device is internet-facing
- whether the device can be remotely updated
- how long the data must remain confidential

So the final recommendation is both data-driven and operationally practical.

## 6. Cryptography Deep Dive

This is the most important technical section of the project.

### 6.1 Classical Cryptography

The `classical_crypto.py` module implements real cryptographic operations using Python's `cryptography` library.

It includes:

- **RSA**
- **ECC using ECDH**
- **AES-GCM**

For RSA, the code:

1. generates a keypair,
2. encrypts a random 32-byte message,
3. decrypts it,
4. records timing and key sizes.

For ECC, it simulates secure key exchange using **ECDH** between two parties, then derives a shared key using **HKDF**.

For AES, it uses **AES-GCM**, which provides both encryption and integrity protection. It measures encryption and decryption time and also tracks ciphertext overhead.

Why these matter:

- RSA and ECC are classical public-key systems.
- AES is symmetric and is considered more resilient in the quantum era than RSA and ECC, although key sizes still matter.

### 6.2 Post-Quantum Cryptography

The `pqc_crypto.py` module focuses on post-quantum algorithms.

It supports:

- **Kyber** for key encapsulation
- **Dilithium** for digital signatures
- **Falcon** for digital signatures

If `liboqs` is available, it uses real implementations. If not, it falls back to realistic simulation based on:

- official algorithm sizes
- realistic operation timing
- CPU-bound hash computations instead of fake sleep-based delays

This is a strong design choice because the fallback is still educational and benchmark-friendly.

#### Kyber

Kyber is used as a **Key Encapsulation Mechanism**, or KEM.

The flow is:

1. generate keypair
2. encapsulate a shared secret using the public key
3. decapsulate using the private key

The project benchmarks variants like:

- Kyber512
- Kyber768
- Kyber1024

Kyber is important because it is the project’s main post-quantum replacement for vulnerable public-key exchange schemes like RSA and ECC.

#### Dilithium

Dilithium is a post-quantum **digital signature** algorithm.

The project measures:

- key generation
- signing
- verification

This is relevant because secure migration is not only about encryption. It is also about authentication and software integrity.

#### Falcon

Falcon is another post-quantum signature scheme. In this project it is available mainly as a specialized demo, with realistic benchmarking behavior. Falcon is known for compact signatures but more complex math.

### 6.3 Hybrid Cryptography

The `hybrid_crypto.py` module demonstrates the transition strategy.

This is one of the strongest parts of the project.

The hybrid flow is:

1. perform classical **ECDH** key exchange,
2. perform **Kyber-512** key encapsulation,
3. combine both shared secrets,
4. derive the session key using **HKDF**,
5. encrypt actual payload data with **AES-256-GCM**.

This is useful because hybrid crypto provides security even if one side of the transition has weaknesses. In simple words:

- if classical crypto fails in the future, Kyber still protects the session
- if PQC deployment has unknown issues, the classical part still adds protection today

So hybrid cryptography is the safest migration bridge.

### 6.4 Benchmark Orchestration

The `benchmark.py` module runs all classical, PQC, and hybrid benchmarks together.

It stores:

- average key generation time
- average encryption or encapsulation time
- average decryption or decapsulation time
- key size
- ciphertext overhead
- whether the algorithm is quantum-safe
- whether real `liboqs` was used

This benchmark data powers the frontend charts and lets users compare performance tradeoffs instead of making purely theoretical decisions.

## 7. API And Backend Flow

The main Flask app in `backend/app.py` exposes the project through REST endpoints.

Important routes include:

- health check
- model metadata
- dashboard summary
- device listing and device detail
- single-device classification
- CSV bulk upload
- benchmark execution
- migration roadmap
- alert acknowledgement
- per-device report generation
- live crypto demo endpoints

A typical request flow is:

1. A device is submitted.
2. The classifier predicts the risk.
3. The policy engine creates a migration recommendation.
4. The result is stored in the database.
5. The frontend fetches and visualizes the updated state.

## 8. Frontend Walkthrough

On the frontend, the app is organized into focused pages:

- **Dashboard**: high-level portfolio overview
- **Device Inventory**: searchable and filterable list of devices
- **Device Detail**: per-device technical breakdown, confidence scores, and migration plan
- **Risk Heatmap**: visual hotspot analysis by device type and sensitivity
- **Benchmarks**: comparison of cryptographic performance
- **Migration Planner**: kanban-style phased roadmap
- **Upload Analysis**: CSV-based bulk assessment

For my UI improvement work, I made the interface more minimal, aligned, and presentation-friendly, especially in spacing, card hierarchy, table structure, and responsive layout.

## 9. Why This Project Is Strong

I believe this project is strong for five reasons:

1. It combines **machine learning** with **cybersecurity decision-making**.
2. It covers both **risk detection** and **migration planning**.
3. It does not stop at theory; it includes actual crypto demos and benchmarks.
4. It supports both **current practicality** and **future quantum readiness**.
5. It is built as a complete full-stack system, not just a model or just a UI.

## 10. Limitations

No project is complete without limitations.

The main limitations are:

- Some PQC algorithms may run in simulation mode when `liboqs` is unavailable.
- The ML dataset is synthetic, so real enterprise datasets would improve realism.
- SQLite is fine for demo and academic use, but production would require a stronger database setup.
- Policy recommendations are rule-based after classification, so they can be made even smarter with cost, compliance, and hardware feasibility models.

## 11. Future Improvements

If I continue this project, I would add:

- real-time device ingestion from live IoT platforms
- stronger role-based access and authentication
- production deployment with PostgreSQL
- more detailed cost estimation for migration
- real hardware benchmarking on constrained devices
- support for additional NIST-standardized post-quantum algorithms

## 12. Closing

To conclude, QuantumGuard AI is a full-stack platform that helps organizations prepare for the post-quantum era by identifying vulnerable IoT devices, classifying their risk with machine learning, benchmarking crypto choices, and generating a practical migration roadmap.

So this project is not only about detecting quantum vulnerability. It is about helping organizations move from awareness to action.

Thank you.

---

## Short Viva Answers

### Why use hybrid cryptography instead of directly replacing everything with PQC?

Because hybrid cryptography reduces transition risk. It combines trusted classical methods with post-quantum methods, so security does not depend on only one family during migration.

### Why is RSA considered vulnerable in the quantum era?

Because Shor's algorithm can solve integer factorization efficiently on a sufficiently powerful quantum computer, which breaks RSA.

### Why is AES still relevant?

AES is symmetric cryptography. Quantum attacks like Grover's algorithm weaken brute-force security, but increasing key size, such as using AES-256, keeps it practical and strong.

### Why did you use ML in this project?

Because risk is influenced by many interacting features, not just the encryption algorithm. ML helps combine device type, sensitivity, retention, hardware constraints, and exposure into a more realistic risk assessment.

### What is the role of the policy engine?

The policy engine converts model output into actionable migration strategy, timeline, effort estimate, reasoning, and priority score.

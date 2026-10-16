# Chain of Custody - Performance Benchmark Suite

This benchmark suite evaluates the end-to-end performance and latency characteristics of the **SSI-Governed Hyperledger Fabric Digital Chain of Custody (CoC)** platform.

It is designed to generate empirical, reproducible metrics for academic research, full-paper submissions, and thesis evaluation.

---

## 1. Pipeline Architecture & Execution Flow

Each benchmark iteration runs a complete forensic evidence lifecycle from initialization to custody transfer. The pipeline is structured into **3 distinct phases** comprising **11 measured milestones**:

```
+---------------------------------------------------------------------------------------------------------+
| PHASE 1: SSI Setup & Authority Initialization                                                           |
|   [1] Issuer DID Creation       -> did:prism registered on Prism node & trusted in MockDB               |
|   [2] AnonCreds Schema Creation -> anoncred-forensic-cert schema published to registry                  |
|   [3] Credential Definition     -> CL-signature CredDef with non-revocation generated                   |
|   [4] Holder DID Creation       -> Expert did:prism registered on Prism node & MockDB                   |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
| PHASE 2: DIDComm Handshake & Credential Delegation                                                      |
|   [5] Connection Handshake      -> OOB invitation -> Holder accept -> ConnectionResponseSent state    |
|   [6] Credential Issuance       -> Offer (Auth Level 2) -> Holder accept & store (CredentialReceived)  |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
| PHASE 3: Blockchain & Gateway Evidence Operations                                                       |
|   Tests ALL 5 operational capabilities of the Chain of Custody platform:                                |
|   [7]  Evidence Creation        -> ZKP Level 2 verify + Ed25519 VC sign + Mongo insert + Fabric Create  |
|   [8]  Metadata Query           -> ZKP Level 0 verify + Mongo read + Fabric ReadAsset                   |
|   [9]  Chain Verification       -> ZKP Level 1 verify + SHA-256 hash check + JWT sig verify (all links)|
|   [10] Evidence Update          -> ZKP Level 2 verify + new VC link + Fabric Create + Fabric Revoke     |
|   [11] Custody Transfer         -> ZKP Level 2 verify + Fabric TransferOwnership + Mongo owner update   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Why Phase 3 Takes Longer

Phase 3 accounts for the largest share of the pipeline duration. This is because **Phase 3 is not a single operation**—it sequentially executes and tests **all 5 core capabilities** of the Gateway and Fabric blockchain in a single run:

1. **Evidence Creation (`POST /create-evidence`)**:
   Genesis registration of digital evidence. Requires authorization level 2.
2. **Metadata Query (`POST /chain-of-custody`)**:
   Retrieval of chain metadata with sensitive VC signatures stripped for restricted read-only access (level 0).
3. **Cryptographic Chain Verification (`POST /verify-chain-of-custody`)**:
   Traverses every link in the custody chain, verifying that ledger hashes match off-chain records and validating Ed25519 digital signatures (level 1).
4. **Evidence Update & Revocation (`POST /update-evidence`)**:
   Appends a new custody record (with updated 5W1H data) linked to the previous credential, commits the new asset to Fabric, and revokes the previous asset on-chain (level 2).
5. **Custody Ownership Transfer (`POST /transfer-ownership`)**:
   Reassigns evidence custody to a new custodian DID on both MongoDB and the Fabric ledger after verifying current owner identity (level 2).

### Internal Latency Breakdown per Gateway Operation

Each of the 5 operations in Phase 3 is protected by an SSI Zero-Knowledge Proof (ZKP) gate. Therefore, each operation involves two distinct sub-layers:

$$\text{Operation Latency} = \text{SSI ZKP Presentation Cycle} + \text{Data Storage \& Fabric Ledger Consensus}$$

- **SSI ZKP Presentation Layer**:
  1. Gateway requests presentation from Verifier API (`POST :5017/presentation_request`).
  2. Verifier Agent issues proof request with AnonCreds predicate (`authorization_level >= required`).
  3. Holder API (`holder_api.py`) receives request, pauses (`asyncio.sleep` for agent state synchronization), and accepts.
  4. Holder agent generates zero-knowledge proof and transmits over DIDComm to Verifier agent.
  5. Verifier agent verifies cryptographic proof and fires webhook event to `webhook_handler.py`.
  6. Gateway polls `mockdb_service` and retrieves verified attributes.
- **Data Persistence & Fabric Consensus Layer**:
  1. Off-chain W3C Verifiable Credential creation and Ed25519 digital signature signing.
  2. MongoDB record insertion/update.
  3. Hyperledger Fabric gRPC transaction submission (`CreateAsset`, `RevokeAsset`, `ReadAsset`, or `TransferOwnership`).
  4. Endorsement by Org1 peer + Raft orderer batching + block commit to the distributed ledger.

Because all 5 operations are executed consecutively, Phase 3 evaluates the full cumulative overhead of repeated zero-knowledge presentations and blockchain transaction endorsements.

---

## 3. Measured Milestones & Paper Reference Table

| # | Milestone Name | Subsystem | Protocol / Endpoint | Academic Significance |
|---|---|---|---|---|
| **1** | Issuer DID Creation | Identus / Prism | `POST /did-registrar/dids` | Authority identity generation cost |
| **2** | Schema Creation | Identus / Prism | `POST /schema-registry/schemas` | Credential structure registration |
| **3** | Credential Definition | Identus / Prism | `POST /credential-definition-registry/definitions` | Heavy CL cryptographic key & accumulator generation |
| **4** | Holder DID Creation | Identus / Prism | `POST /did-registrar/dids` | Forensic expert identity generation |
| **5** | Connection Handshake | Identus DIDComm | OOB Invitation $\rightarrow$ `ConnectionResponseSent` | Peer DIDComm v2 channel establishment |
| **6** | Credential Issuance | Identus AnonCreds | Offer $\rightarrow$ Holder wallet storage | Delegation of authority from Judge to Expert |
| **7** | Evidence Creation | Gateway + Fabric | `POST /create-evidence` | End-to-end evidence intake latency |
| **8** | Metadata Query | Gateway + Fabric | `POST /chain-of-custody` | Restricted metadata audit latency |
| **9** | Chain Verification | Gateway + Fabric | `POST /verify-chain-of-custody` | Full cryptographic chain audit & tamper check |
| **10** | Evidence Update | Gateway + Fabric | `POST /update-evidence` | Chain extension & on-chain revocation overhead |
| **11** | Custody Transfer | Gateway + Fabric | `POST /transfer-ownership` | Custodian transition on blockchain |
| **—** | **Total Pipeline** | **End-to-End** | **All 11 steps combined** | **Complete lifecycle evaluation** |

---

## 4. How to Run the Benchmark

### Prerequisites
Make sure all 3 service stacks are running:
1. **Fabric & Gateway**: `cd FabricChainofCustody && ./run.sh`
2. **Identus Stack**: `cd identus-agent-2.0.0/st-multi && docker compose up -d`
3. **SSI Services**: `cd SSI-App && ./start_services.sh`

### Commands

```bash
cd SSI-App

# 1. Health Check (verify all 7 ports are up)
./run_benchmark.sh --check-health

# 2. Run a Single Test Iteration
./run_benchmark.sh -n 1

# 3. Run a Research Batch (e.g. 10)
./run_benchmark.sh -n 10

# 4. Quiet Mode (only show final summary table)
./run_benchmark.sh -n 10 -q

# 5. Custom Output Directory
./run_benchmark.sh -n 10 -o ./my_paper_data
```

---

## 5. Exported Results & Analysis

All results are automatically exported to `SSI-App/benchmark_results/`:

- **`benchmark_raw_<timestamp>.csv` & `benchmark_raw_latest.csv`**:
  Row-by-row raw timings for each iteration. Columns match each of the 11 milestones plus aggregated totals (`total_ssi_s`, `total_fabric_coc_s`, `total_pipeline_s`). Suitable for plotting CDFs, boxplots, and histograms in Python/Matplotlib/Pandas or R.
- **`benchmark_summary_<timestamp>.json` & `benchmark_summary_latest.json`**:
  Pre-calculated statistical metrics across all iterations:
  - `mean`: Arithmetic mean
  - `median`: 50th percentile
  - `stdev`: Sample standard deviation
  - `min` / `max`: Lower and upper bounds
  - `p95`: 95th percentile latency
  Directly usable for generating LaTeX tables for academic publication.

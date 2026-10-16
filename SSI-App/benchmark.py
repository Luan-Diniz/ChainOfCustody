#!/usr/bin/env python3
"""
Chain of Custody Automated Performance Benchmark Suite

This suite automates the complete multi-actor flow:
  1. SSI Setup: Issuer & Holder DID creation, AnonCreds Schema, Credential Definition
  2. Credential Issuance: DIDComm connection establishment, AnonCreds issuance
  3. Evidence Operations: Creation, Metadata Retrieval, Cryptographic Verification,
     Evidence Update, and Ownership Transfer via the Gateway & Fabric blockchain.

Metrics are measured with microsecond precision (time.perf_counter), displayed in a
formatted table, and exported to CSV and JSON summary files for paper evaluation.
"""

import os
import sys
import time
import uuid
import hashlib
import asyncio
import argparse
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
import statistics

# Set up module resolution for SSI-App subdirectories
BASE_DIR = Path(__file__).resolve().parent
sys.path.extend([
    str(BASE_DIR),
    str(BASE_DIR / "issuer"),
    str(BASE_DIR / "holder"),
    str(BASE_DIR / "mockDbservice")
])

import aiohttp
import issuer_controller
import holder_controller
import local_database
from credential_data import CredentialData

# Ensure SQLite shared_data.db path is absolute
local_database.DB_FILE = str(BASE_DIR / "shared_data.db")

# Configuration defaults (overridable via environment variables)
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:3000")
MOCKDB_URL = os.getenv("MOCKDB_URL", "http://localhost:49152")
HOLDER_API_URL = os.getenv("HOLDER_API_URL", "http://localhost:5001")
VERIFIER_API_URL = os.getenv("VERIFIER_API_URL", "http://localhost:5017")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:5000")
ISSUER_AGENT_URL = os.getenv("ISSUER_AGENT_URL", "http://localhost:8080/cloud-agent")
HOLDER_AGENT_URL = os.getenv("HOLDER_AGENT_URL", "http://localhost:8083/cloud-agent")


# --- Health Check ---
async def check_service_health() -> Dict[str, bool]:
    """Pings all required services to verify they are running before benchmarking."""
    services = {
        "Fabric Gateway (:3000)": f"{GATEWAY_URL}/chain-of-custody",
        "Mock DB Service (:49152)": f"{MOCKDB_URL}/identities",
        "Holder API (:5001)": f"{HOLDER_API_URL}/docs",
        "Verifier API (:5017)": f"{VERIFIER_API_URL}/docs",
        "Webhook Handler (:5000)": f"{WEBHOOK_URL}/docs",
        "Issuer Cloud Agent (:8080)": f"{ISSUER_AGENT_URL}/_system/health",
        "Holder Cloud Agent (:8083)": f"{HOLDER_AGENT_URL}/_system/health",
    }

    results = {}
    timeout = aiohttp.ClientTimeout(total=3.0)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for name, url in services.items():
            try:
                async with session.get(url) as resp:
                    # Any response (even 404/405) indicates the server is listening
                    results[name] = resp.status < 500 or resp.status in (404, 405)
            except Exception:
                results[name] = False
    return results


def print_health_table(health: Dict[str, bool]) -> bool:
    print("\n" + "=" * 65)
    print(f"{'SERVICE':<35} | {'STATUS':<12} | {'HEALTH'}")
    print("-" * 65)
    all_ok = True
    for service, ok in health.items():
        status = "ONLINE" if ok else "OFFLINE"
        symbol = "[OK]" if ok else "[FAIL]"
        print(f"{service:<35} | {status:<12} | {symbol}")
        if not ok:
            all_ok = False
    print("=" * 65)
    return all_ok


# --- Single Iteration Execution ---
async def run_single_iteration(iteration_num: int, verbose: bool = True) -> Dict[str, Any]:
    """
    Executes one complete lifecycle iteration and returns recorded latency metrics in seconds.
    """
    timings: Dict[str, float] = {}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    unique_run_id = uuid.uuid4().hex[:8]
    expert_name = f"Perito Benchmark {unique_run_id}"
    judge_id = f"Juiz-{unique_run_id}"
    jurisdiction = "Vara Federal - Secao Judiciaria"
    evidence_content = f"raw_evidence_data_{unique_run_id}_{time.time()}"
    evidence_hash = hashlib.sha256(evidence_content.encode()).hexdigest()

    if verbose:
        print(f"\n>>> Starting Iteration {iteration_num} (Evidence Hash: {evidence_hash[:12]}...)")

    await local_database.init_db()

    async with aiohttp.ClientSession(headers=headers) as session:
        # ---------------------------------------------------------
        # 1. SSI Setup: Issuer DID, Schema, CredDef
        # ---------------------------------------------------------
        if verbose:
            print("  [1/11] Creating and publishing Issuer DID...")
        t0 = time.perf_counter()
        issuer_long_did = await issuer_controller.create_did()
        issuer_did = await issuer_controller.publish_did(issuer_long_did)
        timings["issuer_did_creation_s"] = time.perf_counter() - t0

        # Register issuer in mockdb
        async with session.post(f"{MOCKDB_URL}/trusted-issuers/{issuer_did}") as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to add trusted issuer: {await resp.text()}")

        if verbose:
            print("  [2/11] Creating AnonCreds Schema...")
        t0 = time.perf_counter()
        schema_guid = await issuer_controller.create_anoncreds_schema(issuer_did)
        timings["schema_creation_s"] = time.perf_counter() - t0

        if verbose:
            print("  [3/11] Creating Credential Definition...")
        t0 = time.perf_counter()
        cred_def_guid = await issuer_controller.create_credential_definition(schema_guid, issuer_did)
        timings["cred_def_creation_s"] = time.perf_counter() - t0

        # ---------------------------------------------------------
        # 2. SSI Setup: Holder DID
        # ---------------------------------------------------------
        if verbose:
            print("  [4/11] Creating and publishing Holder DID...")
        t0 = time.perf_counter()
        holder_long_did = await holder_controller.create_did()
        holder_did = await holder_controller.publish_did(holder_long_did)
        timings["holder_did_creation_s"] = time.perf_counter() - t0

        # Register holder in mockdb
        async with session.post(f"{MOCKDB_URL}/identities", json={"name": expert_name, "did": holder_did}) as resp:
            if resp.status != 201:
                raise RuntimeError(f"Failed to register identity: {await resp.text()}")

        # ---------------------------------------------------------
        # 3. DIDComm Connection Establishment
        # ---------------------------------------------------------
        if verbose:
            print("  [5/11] Establishing DIDComm connection...")
        t0 = time.perf_counter()
        raw_invitation, connection_id = await issuer_controller.create_connection(f"conn_{unique_run_id}")
        await local_database.add_connection(connection_id, expert_name, holder_did)

        # Update CredDef in mockdb
        async with session.post(f"{MOCKDB_URL}/credential-definition", json={
            "credential_def_guid": cred_def_guid,
            "connectionId": connection_id
        }) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to set credential definition in mockdb: {await resp.text()}")

        # Send invitation to holder
        async with session.post(f"{HOLDER_API_URL}/receive_oob_invitation", json={"raw_invitation": raw_invitation}) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Holder failed to accept connection invitation: {await resp.text()}")

        # Await DIDComm handshake completion (ConnectionResponseSent or Connected)
        conn_ready = False
        for _ in range(30):
            async with session.get(f"{ISSUER_AGENT_URL}/connections/{connection_id}") as c_resp:
                if c_resp.status == 200:
                    c_data = await c_resp.json()
                    if c_data.get("state") in ("ConnectionResponseSent", "Connected"):
                        conn_ready = True
                        break
            await asyncio.sleep(0.5)

        if not conn_ready:
            raise TimeoutError(f"Connection {connection_id} did not reach ConnectionResponseSent in time")

        timings["connection_establishment_s"] = time.perf_counter() - t0

        # ---------------------------------------------------------
        # 4. AnonCreds Credential Issuance
        # ---------------------------------------------------------
        if verbose:
            print("  [6/11] Issuing AnonCreds Credential to Holder...")
        cred_data = CredentialData(
            expert_name=expert_name,
            issuing_judge_id=judge_id,
            evidence_hash=evidence_hash,
            authorization_level="2",
            court_jurisdiction=jurisdiction,
            subject_did=holder_did
        )

        t0 = time.perf_counter()
        offer_thid = await issuer_controller.create_credential_offer_anoncreds(
            issuer_did=issuer_did,
            connection_id=connection_id,
            credential_definition_id=cred_def_guid,
            credential_data=cred_data,
            validity_period_in_seconds=3600.0
        )

        # Notify holder API (holder_api.py has internal wait & accept)
        async with session.post(f"{HOLDER_API_URL}/receive_credential_offer", json={"thid": offer_thid}) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Holder failed to accept credential offer: {await resp.text()}")

        # Await holder agent storing the issued credential
        cred_stored = False
        for _ in range(30):
            async with session.get(f"{HOLDER_AGENT_URL}/issue-credentials/records") as h_resp:
                if h_resp.status == 200:
                    records = (await h_resp.json()).get("contents", [])
                    for rec in records:
                        if rec.get("thid") == offer_thid and rec.get("protocolState") == "CredentialReceived":
                            cred_stored = True
                            break
                    if cred_stored:
                        break
            await asyncio.sleep(0.5)

        if not cred_stored:
            raise TimeoutError(f"Holder did not reach CredentialReceived for offer {offer_thid} in time")

        timings["credential_issuance_s"] = time.perf_counter() - t0

        # ---------------------------------------------------------
        # 5. Fabric & Gateway: Create Evidence
        # ---------------------------------------------------------
        if verbose:
            print("  [7/11] Submitting Create Evidence to Gateway & Fabric...")
        create_payload = {
            "owner_did": holder_did,
            "evidence_hash": evidence_hash,
            "tags": ["forensic", "benchmark", unique_run_id],
            "evidence_record": {
                "what": "Forensic disk image dump",
                "who": expert_name,
                "where": "Laboratorio de Pericia Computacional",
                "when": "2026-10-16T18:00:00Z",
                "why": "Judicial forensic preservation",
                "how": "Physical write-blocker image acquisition"
            }
        }

        t0 = time.perf_counter()
        async with session.post(f"{GATEWAY_URL}/create-evidence", json=create_payload) as resp:
            if resp.status != 201:
                raise RuntimeError(f"create-evidence failed (HTTP {resp.status}): {await resp.text()}")
            create_data = await resp.json()
        timings["evidence_creation_s"] = time.perf_counter() - t0
        credential_id = create_data["credentialId"]

        # ---------------------------------------------------------
        # 6. Fabric & Gateway: Read Chain Metadata
        # ---------------------------------------------------------
        if verbose:
            print("  [8/11] Reading Chain of Custody Metadata...")
        meta_payload = {
            "owner_did": holder_did,
            "evidence_hash": evidence_hash
        }
        t0 = time.perf_counter()
        async with session.post(f"{GATEWAY_URL}/chain-of-custody", json=meta_payload) as resp:
            if resp.status != 200:
                raise RuntimeError(f"chain-of-custody failed (HTTP {resp.status}): {await resp.text()}")
        timings["metadata_query_s"] = time.perf_counter() - t0

        # ---------------------------------------------------------
        # 7. Fabric & Gateway: Cryptographic Verification of Chain
        # ---------------------------------------------------------
        if verbose:
            print("  [9/11] Cryptographically Verifying Chain of Custody...")
        verify_payload = {
            "owner_did": holder_did,
            "evidence_hash": evidence_hash
        }
        t0 = time.perf_counter()
        async with session.post(f"{GATEWAY_URL}/verify-chain-of-custody", json=verify_payload) as resp:
            if resp.status != 200:
                raise RuntimeError(f"verify-chain-of-custody failed (HTTP {resp.status}): {await resp.text()}")
        timings["chain_verification_s"] = time.perf_counter() - t0

        # ---------------------------------------------------------
        # 8. Fabric & Gateway: Update Evidence (Revocation + Append Link)
        # ---------------------------------------------------------
        if verbose:
            print("  [10/11] Updating Evidence (Revoke old + Create new revision)...")
        update_payload = {
            "owner_did": holder_did,
            "evidence_hash": evidence_hash,
            "old_credential_id": credential_id,
            "tags": ["forensic", "benchmark", "updated"],
            "new_evidence_record": {
                "what": "Extracted timeline artifacts and event logs",
                "who": expert_name,
                "where": "Laboratorio de Pericia Computacional",
                "when": "2026-10-16T18:30:00Z",
                "why": "Timeline correlation analysis",
                "how": "Automated artifact triage parsing"
            }
        }
        t0 = time.perf_counter()
        async with session.post(f"{GATEWAY_URL}/update-evidence", json=update_payload) as resp:
            if resp.status != 200:
                raise RuntimeError(f"update-evidence failed (HTTP {resp.status}): {await resp.text()}")
            update_data = await resp.json()
        timings["evidence_update_s"] = time.perf_counter() - t0
        new_credential_id = update_data["newCredentialId"]

        # ---------------------------------------------------------
        # 9. Fabric & Gateway: Transfer Custody Ownership
        # ---------------------------------------------------------
        if verbose:
            print("  [11/11] Transferring Custody Ownership on Blockchain...")
        # Generate new custodian DID
        new_holder_long = await holder_controller.create_did()
        new_holder_did = await holder_controller.publish_did(new_holder_long)

        transfer_payload = {
            "evidence_hash": evidence_hash,
            "current_owner_did": holder_did,
            "new_owner_did": new_holder_did,
            "credential_id": new_credential_id
        }
        t0 = time.perf_counter()
        async with session.post(f"{GATEWAY_URL}/transfer-ownership", json=transfer_payload) as resp:
            if resp.status != 200:
                raise RuntimeError(f"transfer-ownership failed (HTTP {resp.status}): {await resp.text()}")
        timings["ownership_transfer_s"] = time.perf_counter() - t0

    # Aggregate metric categories
    ssi_total = (
        timings["issuer_did_creation_s"] +
        timings["schema_creation_s"] +
        timings["cred_def_creation_s"] +
        timings["holder_did_creation_s"] +
        timings["connection_establishment_s"] +
        timings["credential_issuance_s"]
    )
    fabric_total = (
        timings["evidence_creation_s"] +
        timings["metadata_query_s"] +
        timings["chain_verification_s"] +
        timings["evidence_update_s"] +
        timings["ownership_transfer_s"]
    )

    result = {
        "iteration": iteration_num,
        "evidence_hash": evidence_hash,
        **timings,
        "total_ssi_s": ssi_total,
        "total_fabric_coc_s": fabric_total,
        "total_pipeline_s": ssi_total + fabric_total
    }

    if verbose:
        print(f"  --> Completed Iteration {iteration_num} | SSI: {ssi_total:.3f}s | Fabric/Gateway: {fabric_total:.3f}s | Total: {ssi_total + fabric_total:.3f}s")

    return result


# --- Statistics & Reporting ---
def calculate_summary_stats(raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates Mean, Median, StDev, Min, Max, P95 for each metric across iterations."""
    if not raw_data:
        return {}

    metric_keys = [k for k in raw_data[0].keys() if k not in ("iteration", "evidence_hash")]
    summary = {}

    for key in metric_keys:
        values = [row[key] for row in raw_data if isinstance(row.get(key), (int, float))]
        if not values:
            continue
        n = len(values)
        sorted_v = sorted(values)
        p95_idx = int(0.95 * n) if n > 1 else 0
        summary[key] = {
            "count": n,
            "mean": round(statistics.mean(values), 4),
            "median": round(statistics.median(values), 4),
            "stdev": round(statistics.stdev(values), 4) if n > 1 else 0.0,
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "p95": round(sorted_v[p95_idx], 4)
        }

    return summary


def display_results_table(summary: Dict[str, Any]):
    print("\n" + "=" * 95)
    print(f"{'PERFORMANCE METRIC':<36} | {'MEAN (s)':<10} | {'MEDIAN':<10} | {'STDEV':<10} | {'MIN':<10} | {'MAX':<10}")
    print("=" * 95)

    categories = [
        ("SSI Operations (Identus Agent)", [
            ("issuer_did_creation_s", "Issuer DID Creation"),
            ("schema_creation_s", "AnonCreds Schema Creation"),
            ("cred_def_creation_s", "Credential Definition Creation"),
            ("holder_did_creation_s", "Holder DID Creation"),
            ("connection_establishment_s", "DIDComm Connection Handshake"),
            ("credential_issuance_s", "AnonCreds Credential Issuance"),
            ("total_ssi_s", "Total SSI Operations")
        ]),
        ("Blockchain & Gateway Operations (Fabric & MongoDB)", [
            ("evidence_creation_s", "Evidence Creation (Fabric + VC)"),
            ("metadata_query_s", "Metadata Query"),
            ("chain_verification_s", "Cryptographic Chain Verification"),
            ("evidence_update_s", "Evidence Update & Revocation"),
            ("ownership_transfer_s", "Custody Ownership Transfer"),
            ("total_fabric_coc_s", "Total Blockchain & Gateway")
        ]),
        ("Overall Pipeline", [
            ("total_pipeline_s", "Total End-to-End Pipeline")
        ])
    ]

    for cat_name, items in categories:
        print(f"\n--- {cat_name} ---")
        for key, label in items:
            if key in summary:
                s = summary[key]
                print(f"{label:<36} | {s['mean']:<10.4f} | {s['median']:<10.4f} | {s['stdev']:<10.4f} | {s['min']:<10.4f} | {s['max']:<10.4f}")
    print("=" * 95 + "\n")


def export_results(raw_data: List[Dict[str, Any]], summary: Dict[str, Any], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    csv_path = output_dir / f"benchmark_raw_{timestamp}.csv"
    latest_csv = output_dir / "benchmark_raw_latest.csv"
    json_path = output_dir / f"benchmark_summary_{timestamp}.json"
    latest_json = output_dir / "benchmark_summary_latest.json"

    # Export CSV
    if raw_data:
        keys = list(raw_data[0].keys())
        for path in (csv_path, latest_csv):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(raw_data)
        print(f"[+] Raw metrics exported to: {csv_path}")

    # Export JSON
    payload = {
        "timestamp": timestamp,
        "iterations": len(raw_data),
        "summary": summary,
        "raw": raw_data
    }
    for path in (json_path, latest_json):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    print(f"[+] Statistical summary exported to: {json_path}")


# --- Main Runner ---
async def main():
    parser = argparse.ArgumentParser(description="Chain of Custody Automated Performance Benchmark")
    parser.add_argument("-n", "--iterations", type=int, default=int(os.getenv("BENCHMARK_ITERATIONS", "1")),
                        help="Number of full benchmark iterations (default: 1 or $BENCHMARK_ITERATIONS)")
    parser.add_argument("-o", "--output-dir", type=str, default=os.getenv("BENCHMARK_OUTPUT_DIR", str(BASE_DIR / "benchmark_results")),
                        help="Directory to save CSV and JSON results (default: SSI-App/benchmark_results)")
    parser.add_argument("--check-health", action="store_true",
                        help="Only run service health check and exit")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress step-by-step progress logging")

    args = parser.parse_args()

    print("\n" + "#" * 65)
    print("#  Chain of Custody SSI + Fabric Performance Benchmark Suite  #")
    print("#" * 65)

    # 1. Health check
    print("\n[*] Checking service availability...")
    health = await check_service_health()
    all_ok = print_health_table(health)

    if args.check_health:
        sys.exit(0 if all_ok else 1)

    if not all_ok:
        print("\n[!] Error: One or more services are OFFLINE.")
        print("    Please ensure all 3 stacks are running before benchmarking:")
        print("    1. cd FabricChainofCustody && ./run.sh")
        print("    2. cd identus-agent-2.0.0/st-multi && docker compose up -d")
        print("    3. cd SSI-App && ./start_services.sh\n")
        sys.exit(1)

    # 2. Benchmark execution
    output_dir = Path(args.output_dir)
    raw_results = []
    print(f"\n[*] Starting benchmark with {args.iterations} iteration(s)...")

    start_time = time.perf_counter()
    for i in range(1, args.iterations + 1):
        try:
            row = await run_single_iteration(i, verbose=not args.quiet)
            raw_results.append(row)
        except Exception as e:
            print(f"\n[!] Error during iteration {i}: {e}")
            import traceback
            traceback.print_exc()
            break

    total_elapsed = time.perf_counter() - start_time
    print(f"\n[*] Completed {len(raw_results)}/{args.iterations} iteration(s) in {total_elapsed:.2f} seconds.")

    # 3. Compute and display statistics
    if raw_results:
        summary = calculate_summary_stats(raw_results)
        display_results_table(summary)
        export_results(raw_results, summary, output_dir)
    else:
        print("[!] No successful iterations to summarize.")


if __name__ == "__main__":
    asyncio.run(main())

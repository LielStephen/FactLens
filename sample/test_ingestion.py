import os
import time
import httpx

files_to_upload = [
    "sample/Document_A_Annual_Report_2023.pdf",
    "sample/Document_B_Annual_Report_2024.pdf",
    "sample/Document_C_Audit_Filing_2024.pdf"
]

def main():
    doc_ids = []
    with httpx.Client(timeout=30.0) as client:
        for fpath in files_to_upload:
            fname = os.path.basename(fpath)
            with open(fpath, "rb") as f:
                resp = client.post("http://127.0.0.1:8000/api/documents", files={"file": (fname, f, "application/pdf")})
            data = resp.json()
            print(f"Uploaded {fname} -> ID: {data['document_id']}, Status: {data['status']}")
            doc_ids.append((data['document_id'], fname))

        print("\n--- Monitoring Processing Pipeline ---")
        for doc_id, fname in doc_ids:
            for _ in range(40):
                res = client.get(f"http://127.0.0.1:8000/api/documents/{doc_id}/status").json()
                print(f"[{fname[:15]}] Stage: {res.get('stage')} | Progress: {res.get('progress')}% | Status: {res.get('status')}")
                if res.get("status") in ["completed", "failed"]:
                    print(f"[{fname[:15]}] Finished: {res.get('message')}\nTimings: {res.get('timings')}\n")
                    break
                time.sleep(2)

        # Inspect resulting Knowledge Layer
        print("\n--- Knowledge Layer Overview ---")
        overview = client.get("http://127.0.0.1:8000/api/overview").json()
        print("Overview Stats:", overview.get("stats"))

        print("\n--- Extracted Facts Sample ---")
        facts = client.get("http://127.0.0.1:8000/api/facts?limit=10").json()
        for f in facts.get("facts", []):
            print(f"Fact: {f['subject']} | {f['predicate']} = {f['raw_value']} ({f['time'].get('label') if f.get('time') else 'N/A'}) [Conf: {f['confidence']}]")

        print("\n--- Cross-Document Relationships ---")
        rels = client.get("http://127.0.0.1:8000/api/relationships").json()
        for r in rels.get("relationships", []):
            print(f"[{r['relationship_type']}] {r['fact_a']['subject']} · {r['fact_a']['predicate']}: {r['fact_a']['raw_value']} ({r['fact_a']['document_filename']}) vs {r['fact_b']['raw_value']} ({r['fact_b']['document_filename']})")
            print(f"   Reasoning: {r['explanation']}\n")

if __name__ == "__main__":
    main()

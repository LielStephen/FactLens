import os
import time
import httpx
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def main():
    pdf_path = "sample/Document_D_Quarterly_Update.pdf"
    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("ACME CORPORATION Q1 2025 UPDATE", styles['Heading1']),
        Paragraph("Acme Corporation achieved revenue of $135 million in Q1 2025.", styles['Normal']),
        Paragraph("The company remains headquartered in San Francisco, California.", styles['Normal']),
        Paragraph("Global workforce reached 9,500 employees as of March 2025.", styles['Normal']),
    ]
    doc.build(story)

    with httpx.Client(timeout=30.0) as client:
        with open(pdf_path, "rb") as f:
            resp = client.post("http://127.0.0.1:8000/api/documents", files={"file": ("Document_D_Quarterly_Update.pdf", f, "application/pdf")})
        data = resp.json()
        doc_id = data["document_id"]
        print(f"Uploaded Doc D -> ID: {doc_id}")

        t0 = time.time()
        for i in range(30):
            status = client.get(f"http://127.0.0.1:8000/api/documents/{doc_id}/status").json()
            print(f"[{i}s] Progress: {status.get('progress')}% | Stage: {status.get('stage')}")
            if status.get("status") in ["completed", "failed"]:
                total_elapsed = round(time.time() - t0, 2)
                print(f"\n🚀 COMPLETED in {total_elapsed}s!")
                print("Stage Latency Timings:", status.get("timings"))
                break
            time.sleep(1)

if __name__ == "__main__":
    main()

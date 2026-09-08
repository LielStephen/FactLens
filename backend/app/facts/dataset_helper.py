def get_dataset_for_filename(filename: str) -> str:
    """Categorizes document into starter dataset groups."""
    fn = filename.lower()
    if "delhivery" in fn:
        return "delhivery"
    if any(k in fn for k in ["economic", "rbi", "imf", "india"]):
        return "india-macroeconomy"
    return "synthetic"


def get_dataset_metadata(dataset_id: str):
    info = {
        "all": {
            "id": "all",
            "name": "All Datasets",
            "badge": "Global Knowledge Base",
            "description": "Complete cross-document evidence knowledge graph across all corporate, macroeconomic, and synthetic filings."
        },
        "delhivery": {
            "id": "delhivery",
            "name": "Delhivery Logistics (FY22–FY24)",
            "badge": "Corporate Starter Dataset",
            "description": "3 Corporate Filings (227 pages): 2022 Prospectus, FY24 Annual Report, and Q4 FY24 Earnings Deck."
        },
        "india-macroeconomy": {
            "id": "india-macroeconomy",
            "name": "India Macroeconomy (MoF / RBI / IMF)",
            "badge": "Institutional Starter Dataset",
            "description": "3 Macroeconomic Filings (284 pages): Economic Survey 2024-25, RBI Annual Report, and IMF Article IV Consultation."
        },
        "synthetic": {
            "id": "synthetic",
            "name": "Synthetic Showcase (Acme Corp)",
            "badge": "Evaluation Benchmark",
            "description": "4 Curated Benchmark Documents designed to test Corroboration, Contradiction, Contextual Variance, and Diagnostics."
        }
    }
    return info.get(dataset_id, info["all"])

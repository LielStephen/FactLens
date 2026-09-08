import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_sample_pdfs():
    sample_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(sample_dir, exist_ok=True)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    # -------------------------------------------------------------
    # Document A: Acme Corp Annual Report FY2023
    # -------------------------------------------------------------
    doc_a_path = os.path.join(sample_dir, "Document_A_Annual_Report_2023.pdf")
    doc_a = SimpleDocTemplate(doc_a_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story_a = [
        Paragraph("ACME CORPORATION", title_style),
        Paragraph("Annual Report & Shareholder Letter — Fiscal Year 2023", body_style),
        Spacer(1, 15),
        Paragraph("Corporate Overview", h2_style),
        Paragraph("Acme Corporation maintains its global headquarters in San Francisco, California. The company serves global enterprise clients.", body_style),
        Paragraph("Executive leadership was guided by Director John Smith throughout the reporting period.", body_style),
        Spacer(1, 15),
        Paragraph("Financial Performance Summary", h2_style),
        Paragraph("For the fiscal year FY2023, Acme Corporation achieved total revenue of $100 million.", body_style),
        Paragraph("Consolidated net income reached $15 million, reflecting steady operational discipline.", body_style),
        Paragraph("As of year-end 2023, Acme Corporation employed 8,500 employees worldwide.", body_style),
        Spacer(1, 15),
        Paragraph("FY2023 Consolidated Metrics Table", h2_style),
        Table(
            [
                ["Financial Metric", "Fiscal Year 2023", "Reporting Basis"],
                ["Revenue", "$100 million", "Consolidated USD"],
                ["Net Income", "$15 million", "GAAP"],
                ["Global Workforce", "8,500 employees", "Headcount"]
            ],
            colWidths=[200, 150, 150],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ])
        )
    ]
    doc_a.build(story_a)
    print(f"Generated: {doc_a_path}")

    # -------------------------------------------------------------
    # Document B: Acme Corp Annual Report FY2024
    # -------------------------------------------------------------
    doc_b_path = os.path.join(sample_dir, "Document_B_Annual_Report_2024.pdf")
    doc_b = SimpleDocTemplate(doc_b_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story_b = [
        Paragraph("ACME CORPORATION", title_style),
        Paragraph("Annual Report & Performance Review — Fiscal Year 2024", body_style),
        Spacer(1, 15),
        Paragraph("Corporate Governance & Facilities", h2_style),
        Paragraph("Acme Corporation remains headquartered in San Francisco, California across its primary corporate offices.", body_style),
        Paragraph("The board notes that Director John Smith transitioned out of the board in early 2024.", body_style),
        Spacer(1, 15),
        Paragraph("Financial Results & Highlights", h2_style),
        Paragraph("In FY2024, Acme Corporation achieved revenue of $125 million, demonstrating strong market growth.", body_style),
        Paragraph("Operating income increased to $25 million while net profit settled at $22 million.", body_style),
        Paragraph("The global team expanded to 9,200 employees by the conclusion of FY2024.", body_style),
        Spacer(1, 15),
        Paragraph("FY2024 Performance Metrics Table", h2_style),
        Table(
            [
                ["Segment / Metric", "Fiscal Year 2024", "Accounting Unit"],
                ["Revenue", "$125 million", "USD"],
                ["Net Income", "$22 million", "USD"],
                ["Total Workforce", "9,200 employees", "Headcount"]
            ],
            colWidths=[200, 150, 150],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ])
        )
    ]
    doc_b.build(story_b)
    print(f"Generated: {doc_b_path}")

    # -------------------------------------------------------------
    # Document C: Regulatory Audit Filing FY2024
    # -------------------------------------------------------------
    doc_c_path = os.path.join(sample_dir, "Document_C_Audit_Filing_2024.pdf")
    doc_c = SimpleDocTemplate(doc_c_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story_c = [
        Paragraph("INDEPENDENT AUDITOR FILING", title_style),
        Paragraph("Regulatory Review & Financial Audit for Acme Corporation — FY2024", body_style),
        Spacer(1, 15),
        Paragraph("Audited Entity Identification", h2_style),
        Paragraph("Entity Name: Acme Corporation. Registered Corporate Headquarters: San Francisco, California.", body_style),
        Spacer(1, 15),
        Paragraph("Audited Financial Findings", h2_style),
        Paragraph("Under revised statutory accounting principles, Acme Corporation revenue for FY2024 was determined to be $142 million.", body_style),
        Paragraph("This adjusted figure accounts for deferred enterprise license subscriptions.", body_style),
        Spacer(1, 15),
        Paragraph("Audit Reconciliation Schedule", h2_style),
        Table(
            [
                ["Audit Category", "Determined Amount", "Scope"],
                ["Revenue", "$142 million", "Global Consolidated"],
                ["Statutory Adjustments", "$17 million", "Deferred Licenses"]
            ],
            colWidths=[200, 150, 150],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ])
        ),
        Spacer(1, 15),
        Paragraph("Footnote 14B: Unverified restatement clause (* ambiguous currency conversion rate applied without baseline documentation)", body_style)
    ]
    doc_c.build(story_c)
    print(f"Generated: {doc_c_path}")


if __name__ == "__main__":
    generate_sample_pdfs()

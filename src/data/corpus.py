"""Synthetic, openly licensed sample corpus modeled on public-company filing structure.

These documents are original prose written for research/demo use. Figures are
illustrative sample values, not a redistribution of SEC filing text. A separate
script can fetch real EDGAR filings when network use is intended.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from uuid import UUID

from domain.enums import DocumentType
from domain.models import Document, Issuer, Page

ISSUERS = {
    "AAPL": Issuer(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        name="Apple Inc.",
        ticker="AAPL",
        cik="0000320193",
    ),
    "MSFT": Issuer(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        name="Microsoft Corporation",
        ticker="MSFT",
        cik="0000789019",
    ),
    "AMZN": Issuer(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        name="Amazon.com, Inc.",
        ticker="AMZN",
        cik="0001018724",
    ),
    "NVDA": Issuer(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        name="NVIDIA Corporation",
        ticker="NVDA",
        cik="0001045810",
    ),
    "TSLA": Issuer(
        id=UUID("55555555-5555-5555-5555-555555555555"),
        name="Tesla, Inc.",
        ticker="TSLA",
        cik="0001318605",
    ),
}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _doc(
    doc_id: str,
    ticker: str,
    document_type: DocumentType,
    reporting_period: str,
    publication_date: date,
    title: str,
    accession: str,
    pages: list[tuple[int, str, str]],
) -> Document:
    issuer = ISSUERS[ticker]
    page_models = [Page(page=page, section=section, text=text) for page, section, text in pages]
    body = "\n".join(text for _, _, text in pages)
    return Document(
        id=UUID(doc_id),
        issuer=issuer,
        document_type=document_type,
        reporting_period=reporting_period,
        publication_date=publication_date,
        title=title,
        source_url=f"https://www.sec.gov/Archives/edgar/data/{issuer.cik.lstrip('0')}/{accession}/sample.htm",
        local_path=f"data/sample/{ticker}_{reporting_period}_{document_type.value}.json",
        content_hash=_hash(body),
        retrieved_at=datetime(2026, 1, 15, tzinfo=UTC),
        pages=page_models,
        metadata={"accession": accession, "license": "synthetic-cc0", "corpus": "sample-v1"},
    )


def load_sample_corpus() -> list[Document]:
    return [
        _apple_10k_2024(),
        _apple_10k_2023(),
        _apple_10q_2025q2(),
        _apple_8k_2025q2(),
        _msft_10k_2024(),
        _msft_10k_2023(),
        _msft_10q_2025q2(),
        _msft_8k_2025(),
        _amzn_10k_2024(),
        _amzn_10k_2023(),
        _amzn_10q_2025q1(),
        _nvda_10k_2025(),
        _nvda_10k_2024(),
        _nvda_10q_2026q1(),
        _nvda_8k_2025(),
        _tsla_10k_2024(),
        _tsla_10k_2023(),
        _tsla_10q_2025q1(),
        _tsla_8k_2025q1(),
        _apple_8k_china_2024(),
    ]


def _apple_10k_2024() -> Document:
    return _doc(
        "aaaaaaaa-0001-4000-8000-000000000001",
        "AAPL",
        DocumentType.TEN_K,
        "FY2024",
        date(2024, 11, 1),
        "Apple Inc. Form 10-K for the fiscal year ended September 28, 2024 (sample)",
        "000032019324000123",
        [
            (
                1,
                "Business",
                "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a variety of related services. The Company reports net sales by category and by geographic segment. Fiscal year 2024 refers to the 52-week period ended September 28, 2024.",
            ),
            (
                24,
                "MD&A",
                "Total net sales were $391.0 billion in 2024, compared with $383.3 billion in 2023, an increase of $7.7 billion or 2 percent. iPhone net sales were $201.2 billion in 2024, compared with $200.6 billion in 2023. Services net sales were $96.2 billion in 2024, compared with $85.2 billion in 2023, an increase of 13 percent. Mac net sales were $30.0 billion and iPad net sales were $26.3 billion. Wearables, Home and Accessories net sales were $37.3 billion.",
            ),
            (
                26,
                "MD&A Geographic",
                "Americas net sales were $167.8 billion in 2024. Europe net sales were $101.3 billion. Greater China net sales were $67.0 billion in 2024, compared with $72.6 billion in 2023. Japan net sales were $25.8 billion and Rest of Asia Pacific net sales were $29.1 billion. The Company stated that Greater China remained a material segment despite a year-over-year decline.",
            ),
            (
                31,
                "MD&A Expenses",
                "Research and development expense was $31.4 billion in 2024, compared with $29.9 billion in 2023. Selling, general and administrative expense was $26.1 billion. The effective tax rate for 2024 was 16.0 percent.",
            ),
            (
                40,
                "Financial Statements",
                "Net income was $93.7 billion in 2024, or $6.08 diluted earnings per share. Cash and cash equivalents were $29.9 billion as of September 28, 2024. Total current assets were $153.0 billion. The Company returned $95.0 billion to shareholders through dividends and share repurchases during 2024.",
            ),
            (
                52,
                "Risk Factors",
                "The Company is subject to risks associated with international operations, including regulatory change in Greater China, component shortages, and concentrated manufacturing. A material adverse change in Greater China demand could affect total net sales because the segment contributed $67.0 billion in 2024.",
            ),
        ],
    )


def _apple_10k_2023() -> Document:
    return _doc(
        "aaaaaaaa-0001-4000-8000-000000000002",
        "AAPL",
        DocumentType.TEN_K,
        "FY2023",
        date(2023, 11, 3),
        "Apple Inc. Form 10-K for the fiscal year ended September 30, 2023 (sample)",
        "000032019323000106",
        [
            (
                22,
                "MD&A",
                "Total net sales were $383.3 billion in 2023, compared with $394.3 billion in 2022. iPhone net sales were $200.6 billion. Services net sales were $85.2 billion. Greater China net sales were $72.6 billion in 2023. Research and development expense was $29.9 billion. Net income was $97.0 billion.",
            ),
            (
                38,
                "Financial Statements",
                "Diluted earnings per share were $6.13 in 2023. Cash and cash equivalents were $30.0 billion as of September 30, 2023. Share repurchases were $77.6 billion.",
            ),
        ],
    )


def _apple_10q_2025q2() -> Document:
    return _doc(
        "aaaaaaaa-0001-4000-8000-000000000003",
        "AAPL",
        DocumentType.TEN_Q,
        "Q2FY2025",
        date(2025, 5, 2),
        "Apple Inc. Form 10-Q for the quarterly period ended March 29, 2025 (sample)",
        "000032019325000066",
        [
            (
                8,
                "MD&A",
                "Net sales for the second fiscal quarter of 2025 were $94.0 billion, compared with $90.8 billion in the second quarter of 2024. iPhone net sales were $46.8 billion. Services net sales were $26.6 billion. Gross margin was 47.1 percent. The Company noted that the previously furnished preliminary figure of $93.6 billion was updated to $94.0 billion after close of the quarter.",
            ),
            (
                12,
                "Financial Statements",
                "Net income for the quarter was $24.8 billion, or $1.65 diluted earnings per share. Greater China quarterly net sales were $16.0 billion.",
            ),
        ],
    )


def _apple_8k_2025q2() -> Document:
    return _doc(
        "aaaaaaaa-0001-4000-8000-000000000004",
        "AAPL",
        DocumentType.EIGHT_K,
        "Q2FY2025",
        date(2025, 5, 1),
        "Apple Inc. Form 8-K Item 2.02 preliminary results Q2 FY2025 (sample)",
        "000032019325000061",
        [
            (
                1,
                "Item 2.02",
                "On May 1, 2025, Apple furnished preliminary results for the quarter ended March 29, 2025. Preliminary net sales were $93.6 billion and preliminary diluted earnings per share were $1.62. Management cautioned that these amounts were unaudited and subject to quarter-end adjustments in the forthcoming Form 10-Q.",
            )
        ],
    )


def _apple_8k_china_2024() -> Document:
    return _doc(
        "aaaaaaaa-0001-4000-8000-000000000005",
        "AAPL",
        DocumentType.EIGHT_K,
        "FY2024",
        date(2024, 8, 12),
        "Apple Inc. Form 8-K Greater China demand update (sample)",
        "000032019324000088",
        [
            (
                1,
                "Item 7.01",
                "The Company provided an interim commentary that Greater China iPhone sell-through in the June 2024 quarter was weaker than the prior year. No full-year net sales figure was furnished in this 8-K. Investors were directed to the Form 10-K for annual Greater China net sales of record.",
            )
        ],
    )


def _msft_10k_2024() -> Document:
    return _doc(
        "bbbbbbbb-0001-4000-8000-000000000001",
        "MSFT",
        DocumentType.TEN_K,
        "FY2024",
        date(2024, 7, 30),
        "Microsoft Corporation Form 10-K for the fiscal year ended June 30, 2024 (sample)",
        "000078901924000045",
        [
            (
                18,
                "MD&A",
                "Revenue was $245.1 billion in fiscal year 2024, compared with $211.9 billion in fiscal year 2023, an increase of 16 percent. Intelligent Cloud revenue was $96.6 billion, including Azure and other cloud services. Productivity and Business Processes revenue was $76.4 billion. More Personal Computing revenue was $72.1 billion. Operating income was $109.4 billion.",
            ),
            (
                21,
                "MD&A Cloud",
                "Azure and other cloud services revenue grew 30 percent in fiscal 2024. Server products and cloud services revenue was $87.0 billion. The Company stated that AI services contributed a material but not separately disclosed portion of Azure growth. Commercial remaining performance obligation was $275.0 billion.",
            ),
            (
                44,
                "Financial Statements",
                "Net income was $88.1 billion, or $11.80 diluted earnings per share. Research and development expense was $29.5 billion. Cash and cash equivalents were $18.3 billion and short-term investments were $57.2 billion as of June 30, 2024.",
            ),
            (
                60,
                "Risk Factors",
                "Microsoft faces competition in cloud infrastructure, cybersecurity risks, and regulatory scrutiny of large technology platforms. A slowdown in Azure consumption would affect Intelligent Cloud revenue, which was $96.6 billion in fiscal 2024.",
            ),
        ],
    )


def _msft_10k_2023() -> Document:
    return _doc(
        "bbbbbbbb-0001-4000-8000-000000000002",
        "MSFT",
        DocumentType.TEN_K,
        "FY2023",
        date(2023, 8, 3),
        "Microsoft Corporation Form 10-K for the fiscal year ended June 30, 2023 (sample)",
        "000078901923000044",
        [
            (
                17,
                "MD&A",
                "Revenue was $211.9 billion in fiscal year 2023, compared with $198.3 billion in fiscal year 2022. Intelligent Cloud revenue was $87.5 billion. Productivity and Business Processes revenue was $69.3 billion. More Personal Computing revenue was $54.7 billion. Net income was $72.4 billion.",
            ),
            (
                40,
                "Financial Statements",
                "Diluted earnings per share were $9.68 in fiscal 2023. Research and development expense was $27.2 billion.",
            ),
        ],
    )


def _msft_10q_2025q2() -> Document:
    return _doc(
        "bbbbbbbb-0001-4000-8000-000000000003",
        "MSFT",
        DocumentType.TEN_Q,
        "Q2FY2025",
        date(2025, 1, 29),
        "Microsoft Corporation Form 10-Q for the quarterly period ended December 31, 2024 (sample)",
        "000078901925000012",
        [
            (
                9,
                "MD&A",
                "Revenue for the second quarter of fiscal 2025 was $69.6 billion, an increase of 12 percent. Intelligent Cloud revenue was $25.5 billion. Azure and other cloud services revenue grew 31 percent. Productivity and Business Processes revenue was $22.0 billion. Operating income was $31.7 billion.",
            ),
            (
                14,
                "Financial Statements",
                "Net income was $24.1 billion, or $3.23 diluted earnings per share, for the quarter ended December 31, 2024.",
            ),
        ],
    )


def _msft_8k_2025() -> Document:
    return _doc(
        "bbbbbbbb-0001-4000-8000-000000000004",
        "MSFT",
        DocumentType.EIGHT_K,
        "FY2025",
        date(2025, 1, 15),
        "Microsoft Corporation Form 8-K strategic cloud commentary (sample)",
        "000078901925000008",
        [
            (
                1,
                "Item 7.01",
                "Microsoft furnished a Regulation FD update describing continued capacity expansion for Azure AI training and inference. The 8-K did not report a revised annual revenue figure and should not be read as a substitute for the Form 10-K revenue of $245.1 billion for fiscal 2024.",
            )
        ],
    )


def _amzn_10k_2024() -> Document:
    return _doc(
        "cccccccc-0001-4000-8000-000000000001",
        "AMZN",
        DocumentType.TEN_K,
        "FY2024",
        date(2025, 2, 7),
        "Amazon.com, Inc. Form 10-K for the year ended December 31, 2024 (sample)",
        "000101872425000014",
        [
            (
                20,
                "MD&A",
                "Net sales were $638.0 billion in 2024, compared with $574.8 billion in 2023, an increase of 11 percent. North America segment net sales were $387.5 billion. International segment net sales were $142.9 billion. AWS net sales were $107.6 billion in 2024, compared with $90.8 billion in 2023, an increase of 19 percent.",
            ),
            (
                23,
                "MD&A Operating",
                "Operating income was $68.6 billion in 2024, compared with $36.9 billion in 2023. AWS operating income was $39.8 billion. North America operating income was $25.0 billion. International operating income was $3.8 billion. The Company cited fulfillment network productivity and advertising as contributors to margin expansion.",
            ),
            (
                48,
                "Financial Statements",
                "Net income was $59.2 billion, or $5.53 diluted earnings per share. Cash and cash equivalents were $78.8 billion as of December 31, 2024. Inventories were $34.2 billion. Net cash provided by operating activities was $115.9 billion.",
            ),
        ],
    )


def _amzn_10k_2023() -> Document:
    return _doc(
        "cccccccc-0001-4000-8000-000000000002",
        "AMZN",
        DocumentType.TEN_K,
        "FY2023",
        date(2024, 2, 2),
        "Amazon.com, Inc. Form 10-K for the year ended December 31, 2023 (sample)",
        "000101872424000013",
        [
            (
                19,
                "MD&A",
                "Net sales were $574.8 billion in 2023, compared with $514.0 billion in 2022. AWS net sales were $90.8 billion. Operating income was $36.9 billion. North America net sales were $352.8 billion.",
            ),
            (
                45,
                "Financial Statements",
                "Net income was $30.4 billion in 2023. Diluted earnings per share were $2.90.",
            ),
        ],
    )


def _amzn_10q_2025q1() -> Document:
    return _doc(
        "cccccccc-0001-4000-8000-000000000003",
        "AMZN",
        DocumentType.TEN_Q,
        "Q1FY2025",
        date(2025, 5, 1),
        "Amazon.com, Inc. Form 10-Q for the quarterly period ended March 31, 2025 (sample)",
        "000101872425000033",
        [
            (
                7,
                "MD&A",
                "Net sales were $155.7 billion in the first quarter of 2025, an increase of 9 percent compared with $142.6 billion in the first quarter of 2024. AWS net sales were $29.3 billion, an increase of 17 percent. Operating income was $18.4 billion.",
            ),
            (
                11,
                "Financial Statements",
                "Net income was $17.1 billion, or $1.59 diluted earnings per share, for the quarter ended March 31, 2025.",
            ),
        ],
    )


def _nvda_10k_2025() -> Document:
    return _doc(
        "dddddddd-0001-4000-8000-000000000001",
        "NVDA",
        DocumentType.TEN_K,
        "FY2025",
        date(2025, 2, 26),
        "NVIDIA Corporation Form 10-K for the fiscal year ended January 26, 2025 (sample)",
        "000104581025000028",
        [
            (
                16,
                "MD&A",
                "Revenue was $130.5 billion for fiscal year 2025, compared with $60.9 billion for fiscal year 2024. Data Center revenue was $115.2 billion, compared with $47.5 billion in the prior year. Gaming revenue was $11.4 billion. Professional Visualization revenue was $1.9 billion. Automotive revenue was $1.7 billion. Gross margin was 75.0 percent.",
            ),
            (
                19,
                "MD&A Data Center",
                "Growth in Data Center was driven by demand for Hopper and early Blackwell architecture GPUs used in large language model training and inference. Compute revenue was the primary contributor within Data Center. Networking revenue, including InfiniBand and Ethernet, was $12.8 billion.",
            ),
            (
                42,
                "Financial Statements",
                "Net income was $72.9 billion, or $2.94 diluted earnings per share on a post-split basis. Research and development expense was $12.9 billion. Cash, cash equivalents, and marketable securities were $43.2 billion as of January 26, 2025.",
            ),
        ],
    )


def _nvda_10k_2024() -> Document:
    return _doc(
        "dddddddd-0001-4000-8000-000000000002",
        "NVDA",
        DocumentType.TEN_K,
        "FY2024",
        date(2024, 2, 21),
        "NVIDIA Corporation Form 10-K for the fiscal year ended January 28, 2024 (sample)",
        "000104581024000027",
        [
            (
                15,
                "MD&A",
                "Revenue was $60.9 billion for fiscal year 2024, compared with $27.0 billion for fiscal year 2023. Data Center revenue was $47.5 billion. Gaming revenue was $10.4 billion. Gross margin was 72.7 percent. Net income was $29.8 billion.",
            ),
            (
                38,
                "Financial Statements",
                "Diluted earnings per share were $1.19 on a post-split equivalent basis. Research and development expense was $8.7 billion.",
            ),
        ],
    )


def _nvda_10q_2026q1() -> Document:
    return _doc(
        "dddddddd-0001-4000-8000-000000000003",
        "NVDA",
        DocumentType.TEN_Q,
        "Q1FY2026",
        date(2025, 5, 28),
        "NVIDIA Corporation Form 10-Q for the quarterly period ended April 27, 2025 (sample)",
        "000104581025000041",
        [
            (
                6,
                "MD&A",
                "Revenue for the first quarter of fiscal 2026 was $44.1 billion, compared with $26.0 billion in the first quarter of fiscal 2025. Data Center revenue was $39.1 billion. Gross margin was 60.5 percent, reflecting a product transition and inventory reserves related to a new architecture ramp. Gaming revenue was $3.8 billion.",
            ),
            (
                10,
                "Financial Statements",
                "Net income was $18.8 billion, or $0.76 diluted earnings per share, for the quarter ended April 27, 2025.",
            ),
        ],
    )


def _nvda_8k_2025() -> Document:
    return _doc(
        "dddddddd-0001-4000-8000-000000000004",
        "NVDA",
        DocumentType.EIGHT_K,
        "FY2025",
        date(2025, 3, 18),
        "NVIDIA Corporation Form 8-K export control commentary (sample)",
        "000104581025000033",
        [
            (
                1,
                "Item 8.01",
                "NVIDIA noted incremental U.S. export control restrictions that could limit shipments of certain data center GPUs to specified destinations. The Company did not revise the fiscal 2025 Data Center revenue of $115.2 billion already reported in the Form 10-K. Management said fiscal 2026 visibility was reduced in the affected geographies.",
            )
        ],
    )


def _tsla_10k_2024() -> Document:
    return _doc(
        "eeeeeeee-0001-4000-8000-000000000001",
        "TSLA",
        DocumentType.TEN_K,
        "FY2024",
        date(2025, 1, 30),
        "Tesla, Inc. Form 10-K for the year ended December 31, 2024 (sample)",
        "000131860525000018",
        [
            (
                14,
                "MD&A",
                "Total revenues were $97.7 billion in 2024, compared with $96.8 billion in 2023. Automotive revenues were $77.1 billion, compared with $82.4 billion in 2023. Energy generation and storage revenues were $10.1 billion, compared with $6.0 billion in 2023. Services and other revenues were $10.5 billion. Automotive deliveries were 1,789,226 vehicles in 2024, compared with 1,808,581 vehicles in 2023.",
            ),
            (
                17,
                "MD&A Margins",
                "Total gross profit was $17.4 billion. Automotive gross margin was 16.3 percent, down from 18.7 percent in 2023, reflecting price reductions and mix. Operating income was $7.1 billion. The Company produced 1,773,443 vehicles in 2024.",
            ),
            (
                41,
                "Financial Statements",
                "Net income attributable to common stockholders was $7.1 billion, or $2.04 diluted earnings per share. Cash and cash equivalents were $16.3 billion as of December 31, 2024. Capital expenditures were $9.6 billion.",
            ),
            (
                55,
                "Risk Factors",
                "Tesla is exposed to automotive demand cyclicality, competition in battery electric vehicles, and factory concentration in Fremont, Austin, Berlin, and Shanghai. A decline in average selling prices can compress automotive gross margin, which was 16.3 percent in 2024.",
            ),
        ],
    )


def _tsla_10k_2023() -> Document:
    return _doc(
        "eeeeeeee-0001-4000-8000-000000000002",
        "TSLA",
        DocumentType.TEN_K,
        "FY2023",
        date(2024, 1, 29),
        "Tesla, Inc. Form 10-K for the year ended December 31, 2023 (sample)",
        "000131860524000017",
        [
            (
                13,
                "MD&A",
                "Total revenues were $96.8 billion in 2023. Automotive revenues were $82.4 billion. Energy generation and storage revenues were $6.0 billion. Automotive deliveries were 1,808,581 vehicles. Automotive gross margin was 18.7 percent. Operating income was $8.9 billion. Net income was $15.0 billion, which included a non-recurring tax benefit.",
            ),
            (
                36,
                "Financial Statements",
                "Diluted earnings per share were $4.30 in 2023. Cash and cash equivalents were $16.4 billion.",
            ),
        ],
    )


def _tsla_10q_2025q1() -> Document:
    return _doc(
        "eeeeeeee-0001-4000-8000-000000000003",
        "TSLA",
        DocumentType.TEN_Q,
        "Q1FY2025",
        date(2025, 4, 23),
        "Tesla, Inc. Form 10-Q for the quarterly period ended March 31, 2025 (sample)",
        "000131860525000029",
        [
            (
                8,
                "MD&A",
                "Total revenues were $19.3 billion in the first quarter of 2025. Automotive revenues were $14.0 billion. Energy generation and storage revenues were $2.7 billion. The Company delivered 336,681 vehicles in the first quarter, compared with a preliminary production-and-delivery update of 310,000 vehicles published in an April 2, 2025 Form 8-K. The 10-Q states that the preliminary delivery figure omitted certain retail deliveries finalized after the operational cut-off.",
            ),
            (
                12,
                "Financial Statements",
                "Net income attributable to common stockholders was $0.4 billion, or $0.12 diluted earnings per share, for the quarter ended March 31, 2025. Automotive gross margin was 12.5 percent.",
            ),
        ],
    )


def _tsla_8k_2025q1() -> Document:
    return _doc(
        "eeeeeeee-0001-4000-8000-000000000004",
        "TSLA",
        DocumentType.EIGHT_K,
        "Q1FY2025",
        date(2025, 4, 2),
        "Tesla, Inc. Form 8-K preliminary Q1 2025 production and deliveries (sample)",
        "000131860525000024",
        [
            (
                1,
                "Item 2.02",
                "Tesla reported preliminary first quarter 2025 production of 362,000 vehicles and preliminary deliveries of 310,000 vehicles. Energy storage deployments were 10.4 GWh. These figures were unaudited operational statistics and were later superseded by the Form 10-Q delivery count of 336,681 vehicles.",
            )
        ],
    )


def get_financial_news(request_data):
    company_name = request_data.get("company_name", "Unknown")
    date = request_data.get("date", "Unknown")

    return {
        "company_name": company_name,
        "news": [
            {
                "headline": f"{company_name} beats earnings expectations",
                "description": f"{company_name} reported better-than-expected results on {date}.",
                "source": "Financial Times",
                "date": date
            },
            {
                "headline": f"{company_name} stock rallies",
                "description": f"{company_name} shares surged after strong quarterly performance.",
                "source": "Reuters",
                "date": date
            }
        ]
    }

def get_quarterly_results(request_data):
    company_name = request_data.get("company_name", "Unknown")
    quarter = request_data.get("quarter", "Q4 FY24")

    return {
        "company_name": company_name,
        "quarter": quarter,
        "valuation_ratios": {
            "pe_ratio": 25.4,
            "pb_ratio": 3.2
        },
        "files": {
            "balance_sheet_excel": f"https://example.com/{company_name}_balance_sheet.xlsx",
            "analyst_call_transcript_doc": f"https://example.com/{company_name}_analyst_call.doc"
        }
    }


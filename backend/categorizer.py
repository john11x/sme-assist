"""
Smart Categorizer - AI + Rules Engine
Classifies each transaction into accounting categories using a combination of
deterministic keyword rules and LLM intelligence for ambiguous cases.
"""

import json
import re
import pandas as pd
from groq import Groq
from config import settings


# ─────────────────────────────────────────────────────────
# RULE-BASED CATEGORIZATION (Fast, Deterministic)
# ─────────────────────────────────────────────────────────

# Categories used throughout the system
CATEGORIES = {
    "revenue":        "Revenue / Sales",
    "cogs":           "Cost of Goods Sold",
    "rent":           "Rent & Premises",
    "utilities":      "Utilities (Electricity, Water)",
    "salaries":       "Salaries & Wages",
    "casual_labour":  "Casual Labour",
    "statutory":      "Statutory Deductions (NHIF/SHIF, NSSF, Housing Levy)",
    "tax_payment":    "Tax Payments (PAYE, VAT, Income Tax)",
    "transport":      "Transport & Fuel",
    "marketing":      "Marketing & Advertising",
    "insurance":      "Insurance",
    "professional":   "Professional Fees (Audit, Legal, Consulting)",
    "licenses":       "Licenses & Permits",
    "equipment":      "Equipment & Assets",
    "telecom":        "Telecommunication & Internet",
    "repairs":        "Repairs & Maintenance",
    "bank_charges":   "Bank Charges & Fees",
    "personal":       "Personal / Non-Business",
    "other_expense":  "Other Business Expense",
    "other_income":   "Other Income",
}

# Keyword rules - checked against transaction description (case-insensitive)
KEYWORD_RULES = {
    # Revenue patterns
    "revenue": [
        "revenue", "sales", "paybill", "client payment", "customer payment",
        "wholesale", "supply order", "walk-in", "daily sales", "b2c payment",
    ],
    # Cost of Goods Sold
    "cogs": [
        "stock purchase", "stock:", "devki steel", "bamburi cement", "mabati",
        "crown paint", "haco", "east african cable", "inventory", "raw material",
        "supplier payment",
    ],
    # Rent
    "rent": [
        "rent", "shop rent", "warehouse rent", "office rent", "premises",
    ],
    # Utilities
    "utilities": [
        "kplc", "electricity", "nairobi water", "water bill", "kenya power",
    ],
    # Salaries
    "salaries": [
        "salary", "sal-", "payroll", "wage",
    ],
    # Casual Labour
    "casual_labour": [
        "casual labour", "casual labor", "casual worker",
    ],
    # Statutory
    "statutory": [
        "nhif", "shif", "nssf", "housing levy", "hlvy",
    ],
    # Tax payments
    "tax_payment": [
        "kra", "paye", "vat payment", "income tax", "withholding tax",
        "tax payment", "itax",
    ],
    # Transport & Fuel
    "transport": [
        "fuel", "petrol", "diesel", "transport", "delivery", "vehicle service",
        "mechanic",
    ],
    # Marketing
    "marketing": [
        "marketing", "advertising", "social media", "digital marketing",
        "promotion", "branding",
    ],
    # Insurance
    "insurance": [
        "insurance", "indemnity", "cover",
    ],
    # Professional fees
    "professional": [
        "audit", "accounting", "legal", "consultant", "advisory",
    ],
    # Licenses
    "licenses": [
        "license", "licence", "permit", "fire safety", "county license",
        "business permit",
    ],
    # Equipment
    "equipment": [
        "laptop", "computer", "equipment", "machinery", "furniture",
        "printer", "phone",
    ],
    # Telecom
    "telecom": [
        "airtime", "safaricom", "internet", "wifi", "data bundle",
    ],
    # Repairs
    "repairs": [
        "repair", "maintenance", "service",
    ],
    # Bank charges
    "bank_charges": [
        "bank charge", "bank fee", "ledger fee", "transfer fee",
        "atm charge", "transaction fee",
    ],
    # Personal
    "personal": [
        "personal", "pers-", "(personal)", "java house", "restaurant",
        "naivas", "supermarket", "school fees", "uber", "taxi",
        "kempinski", "dstv", "netflix", "gym", "holiday",
        "grocery", "lunch", "dinner",
    ],
}


def categorize_by_rules(description: str, is_credit: bool) -> str:
    """
    Applies keyword rules to categorize a transaction.
    Returns category key or None if no rule matches.
    """
    desc_lower = description.lower()
    
    for category, keywords in KEYWORD_RULES.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    
    # Default: if it's a credit, likely revenue; if debit, likely other expense
    return None


def categorize_batch_llm(transactions: list[dict]) -> list[str]:
    """
    Uses LLM to categorize a batch of transactions that rules couldn't classify.
    Returns a list of category keys.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    category_list = "\n".join([f"- {k}: {v}" for k, v in CATEGORIES.items()])
    
    txn_list = "\n".join([
        f"{i+1}. [{t['type']}] {t['description']} - KES {t['amount']:,.2f}"
        for i, t in enumerate(transactions)
    ])
    
    prompt = f"""You are a Kenyan accountant categorizing business transactions.

Available categories:
{category_list}

Transactions to categorize:
{txn_list}

For each transaction, return ONLY the category KEY (e.g., "revenue", "cogs", "rent").
Return a JSON array of category keys, one per transaction, in the same order.
Return ONLY the JSON array, no explanation.

JSON:"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        response_text = response.choices[0].message.content.strip()
        
        if response_text.startswith("```"):
            response_text = re.sub(r"```(?:json)?\n?", "", response_text)
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()
            
        categories = json.loads(response_text)
        # Validate that all categories are valid keys
        return [c if c in CATEGORIES else "other_expense" for c in categories]
    except Exception as e:
        print(f"⚠️ LLM categorization failed (Rate Limit/Error): {e}")
        return ["other_expense"] * len(transactions)


def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main categorization function. Applies rules first, then LLM for unmatched rows.
    Returns the DataFrame with a new 'category' and 'category_label' column.
    """
    categories = []
    unmatched_indices = []
    unmatched_transactions = []
    
    for idx, row in df.iterrows():
        is_credit = row["credit"] > 0
        category = categorize_by_rules(row["description"], is_credit)
        
        if category:
            categories.append(category)
        else:
            categories.append(None)
            unmatched_indices.append(len(categories) - 1)
            unmatched_transactions.append({
                "description": row["description"],
                "amount": row["debit"] if row["debit"] > 0 else row["credit"],
                "type": "CREDIT" if is_credit else "DEBIT",
            })
    
    # Use LLM for unmatched transactions (in batches of 20)
    if unmatched_transactions:
        print(f"📦 Categorizing {len(unmatched_transactions)} transactions via AI...")
        batch_size = 20
        for i in range(0, len(unmatched_transactions), batch_size):
            batch = unmatched_transactions[i:i + batch_size]
            batch_indices = unmatched_indices[i:i + batch_size]
            
            llm_categories = categorize_batch_llm(batch)
            
            for j, cat_idx in enumerate(batch_indices):
                if j < len(llm_categories):
                    categories[cat_idx] = llm_categories[j]
                else:
                    categories[cat_idx] = "other_expense"
    
    # Fill any remaining None values
    final_categories = []
    for i, c in enumerate(categories):
        if c:
            final_categories.append(c)
        else:
            # Fallback based on money flow
            is_credit = df.iloc[i]["credit"] > 0
            final_categories.append("revenue" if is_credit else "other_expense")
    
    df = df.copy()
    df["category"] = final_categories
    df["category_label"] = df["category"].map(CATEGORIES)
    
    # Add tax relevance flags
    df["is_deductible"] = ~df["category"].isin(["personal", "tax_payment"])
    df["is_vat_applicable"] = df["category"].isin(["cogs", "rent", "utilities", "equipment", "repairs", "telecom"])
    
    print(f"✅ Categorized {len(df)} transactions ({len(unmatched_transactions)} via AI).")
    return df


def get_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a summary of transactions grouped by category.
    """
    summary = df.groupby(["category", "category_label"]).agg(
        total_debit=("debit", "sum"),
        total_credit=("credit", "sum"),
        transaction_count=("description", "count"),
    ).reset_index()
    
    summary["net"] = summary["total_credit"] - summary["total_debit"]
    return summary.sort_values("total_debit", ascending=False)

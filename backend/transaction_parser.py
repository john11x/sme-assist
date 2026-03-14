"""
Transaction Parser - The Foundation
Extracts structured transaction data from bank statements into a pandas DataFrame.
Uses a combination of regex patterns and LLM fallback for complex formats.
"""

import re
import json
import pandas as pd
from datetime import datetime
from groq import Groq
from config import settings


def parse_amount(amount_str: str) -> float:
    """Cleans and converts an amount string to a float."""
    if not amount_str or amount_str.strip() == "" or amount_str.strip() == "-":
        return 0.0
    # Remove commas, spaces, and currency symbols
    cleaned = re.sub(r"[^\d.]", "", amount_str.strip())
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_transactions_regex(text: str) -> list[dict]:
    """
    Attempts to extract transactions using regex patterns common in
    Kenyan bank statements (Equity, KCB, Co-op, etc.)
    """
    transactions = []
    
    # Pattern: DD-MMM-YYYY or DD/MM/YYYY followed by description and amounts
    date_patterns = [
        r"(\d{2}-[A-Z]{3}-\d{4})",   # 05-FEB-2026
        r"(\d{2}/\d{2}/\d{4})",       # 05/02/2026
        r"(\d{4}-\d{2}-\d{2})",       # 2026-02-05
    ]
    
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        # Try each date pattern
        for date_pattern in date_patterns:
            match = re.match(date_pattern, line)
            if match:
                date_str = match.group(1)
                rest = line[match.end():].strip()
                
                # Try to extract amounts (numbers with commas and decimals)
                amounts = re.findall(r"[\d,]+\.\d{2}", rest)
                
                # Remove amounts and reference codes from description
                description = rest
                for amt in amounts:
                    description = description.replace(amt, "")
                
                # Remove common reference patterns
                ref_match = re.search(r"\b([A-Z]{2,}-[\w-]+)\b", description)
                reference = ref_match.group(1) if ref_match else ""
                if reference:
                    description = description.replace(reference, "")
                
                description = re.sub(r"\s+", " ", description).strip()
                description = description.strip(" --")
                
                # Determine debit/credit based on position
                if len(amounts) >= 3:
                    debit = parse_amount(amounts[0])
                    credit = parse_amount(amounts[1])
                    balance = parse_amount(amounts[2])
                elif len(amounts) == 2:
                    # Could be debit+balance or credit+balance
                    debit = parse_amount(amounts[0])
                    credit = 0.0
                    balance = parse_amount(amounts[1])
                elif len(amounts) == 1:
                    debit = 0.0
                    credit = 0.0
                    balance = parse_amount(amounts[0])
                else:
                    continue
                
                transactions.append({
                    "date": date_str,
                    "description": description,
                    "reference": reference,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance,
                })
                break
    
    return transactions


def extract_transactions_llm(text: str) -> list[dict]:
    """
    Uses Gemini LLM to extract structured transaction data when regex fails.
    This is the fallback for complex or non-standard bank statement formats.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    prompt = f"""You are a data extraction specialist. Extract ALL financial transactions from this bank statement into a JSON array.

For each transaction, extract:
- "date": the transaction date (format: YYYY-MM-DD)
- "description": what the transaction is for (clean, readable text)
- "reference": any reference number or code
- "debit": amount debited (money going OUT), 0 if none
- "credit": amount credited (money coming IN), 0 if none  
- "balance": running balance after transaction, 0 if not shown

CRITICAL RULES:
- Return ONLY a valid JSON array, no markdown, no explanation
- Every amount must be a number (no commas, no currency symbols)
- Skip header rows, summary rows, and opening/closing balance lines
- Only include actual transactions (money in or money out)

Bank Statement:
---
{text[:8000]}
---

JSON array:"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        response_text = response.choices[0].message.content.strip()
        
        # Clean up the response - remove markdown code fences if present
        if response_text.startswith("```"):
            response_text = re.sub(r"```(?:json)?\n?", "", response_text)
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()
        
        transactions = json.loads(response_text)
        # Validate and clean
        cleaned = []
        for t in transactions:
            cleaned.append({
                "date": str(t.get("date", "")),
                "description": str(t.get("description", "")),
                "reference": str(t.get("reference", "")),
                "debit": float(t.get("debit", 0)),
                "credit": float(t.get("credit", 0)),
                "balance": float(t.get("balance", 0)),
            })
        return cleaned
    except (json.JSONDecodeError, TypeError) as e:
        print(f"❌ LLM extraction failed to parse JSON: {e}")
        return []


def parse_bank_statement(text: str) -> pd.DataFrame:
    """
    Main entry point. Parses a bank statement into a structured DataFrame.
    Uses regex first, falls back to LLM if regex captures too few transactions.
    """
    # Try regex first (fast, deterministic)
    transactions = extract_transactions_regex(text)
    
    # If regex captured very few transactions, use LLM fallback
    if len(transactions) < 3:
        print("ℹ️ Regex captured few transactions. Using LLM extraction...")
        transactions = extract_transactions_llm(text)
    
    if not transactions:
        print("⚠️ No transactions could be extracted.")
        return pd.DataFrame(columns=["date", "description", "reference", "debit", "credit", "balance"])
    
    df = pd.DataFrame(transactions)
    
    # Normalize date column
    df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=True, errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    
    # Ensure numeric columns
    for col in ["debit", "credit", "balance"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    # Add a net_amount column (positive = money in, negative = money out)
    df["net_amount"] = df["credit"] - df["debit"]
    
    print(f"✅ Parsed {len(df)} transactions from bank statement.")
    return df


def extract_business_info(text: str) -> dict:
    """
    Extracts business metadata from the bank statement header.
    Uses regex for speed and to avoid LLM rate limits.
    """
    # Clean up common Excel to_string artifacts
    header = text[:2000].replace("NaN", "").replace("  ", " ")
    header = re.sub(r'Unnamed: \d+', '', header)
    header = re.sub(r' +', ' ', header) # Final collapse of spaces
    
    # Defaults
    info = {
        "business_name": "Unknown Business",
        "kra_pin": "",
        "account_number": "",
        "bank_name": "Unknown Bank",
        "period_start": "",
        "period_end": "",
        "opening_balance": 0.0,
        "closing_balance": 0.0,
        "tcc_ref": "None Detected",
        "etims_status": "Not Verified",
        "previous_payments": []
    }
    
    # Try find Account Name
    name_match = re.search(r"(?:Name|Account Name|Customer Name|Business Name|Account Holder)\s*:\s*([A-Za-z0-9\s&'.,-]+)", header, re.IGNORECASE)
    if name_match:
        info["business_name"] = name_match.group(1).strip()
    else:
        # Fallback: Many statements put the business name on the first non-numeric/bank line
        lines = [line.strip() for line in header.split("\n") if line.strip()]
        for line in lines:
            line = line.strip()
            # Skip if line is just symbols/separators like ===== or ------- or ═════
            # Rule: Must have at least one letter and not be 90% symbols
            if not re.search(r'[A-Za-z]', line):
                continue
            
            # Skip architectural/formatting lines (lots of repeating symbols)
            if re.search(r'([=\-_─═]{3,})', line):
                continue
                
            # Skip if common header keywords are present
            if any(x in line.lower() for x in ["page", "statement", "period", "account", "equity", "kcb", "bank", "co-op"]):
                continue
            
            info["business_name"] = line.replace('\n', ' ').replace('\r', ' ').strip()
            break
    
    # Try find KRA PIN
    pin_match = re.search(r"PIN\s*:\s*([P]\d{9}[A-Z])", header, re.IGNORECASE)
    if pin_match:
        info["kra_pin"] = pin_match.group(1).strip()
    
    # Try find Account Number
    acc_match = re.search(r"(?:Account No|A/C|Acc No|Account Number)[\.\:]?\s*(\d{8,14})", header, re.IGNORECASE)
    if acc_match:
        info["account_number"] = acc_match.group(1).strip()
        
    # Try find TCC Reference
    tcc_match = re.search(r"(?:TCC|Tax Clearance|Certificate)\s*[:\-]?\s*([A-Za-z0-9\-]{8,25})", header, re.IGNORECASE)
    if tcc_match:
        info["tcc_ref"] = tcc_match.group(1).strip()
    
    # Try find eTIMS Status
    if re.search(r"eTIMS|Device ID|Z-Report", header, re.IGNORECASE):
        info["etims_status"] = "eTIMS Configured"
        
    # Standard Bank Names from common Kenyan banks
    for bank in ["Equity Bank", "KCB", "Co-operative Bank", "NCBA", "Absa", "Standard Chartered"]:
        if bank.lower() in header.lower():
            info["bank_name"] = bank
            break
            
    # Period
    # More flexible period extraction: 01-JAN-2026 to 31-JAN-2026 or 01/01/2026 - 31/01/2026
    # Stop at multiple spaces or newlines to avoid picking up table headers
    period_match = re.search(r"(?:Period|Date|Statement for|Duration)[\.\:]?\s*(\d{1,2}[-/\.\s]\w{2,9}[-/\.\s]\d{2,4})\s*(?:to|–|-)\s*(\d{1,2}[-/\.\s]\w{2,9}[-/\.\s]\d{2,4})", header, re.IGNORECASE)
    if period_match:
        info["period_start"] = period_match.group(1).strip()
        info["period_end"] = period_match.group(2).strip()
    
    # Fallback: Just look for dates if labels missing
    if not info["period_start"]:
        dates = re.findall(r"(\d{2}[-/\.]\w{2,3}[-/\.]\d{4})", header)
        if len(dates) >= 2:
            info["period_start"] = dates[0]
            info["period_end"] = dates[1]
        
    # Closing Balance
    cb_match = re.search(r"(?:Closing Balance|Balance c/f|Balance C/D|Closing Bal)[\.\:]?\s*(?:KES)?\s*([\d,]+\.\d{2})", text[-2000:], re.IGNORECASE)
    if cb_match:
        info["closing_balance"] = parse_amount(cb_match.group(1))

    return info

import pandas as pd
from backend.transaction_parser import parse_bank_statement
from backend.categorizer import categorize_transactions

print("Testing parser + rules...")
with open("data/user_uploads/bank_statement_q1_2026.txt", "r") as f:
    text = f.read()

df = parse_bank_statement(text)

categories = []
unmatched = 0

from backend.categorizer import categorize_by_rules
for idx, row in df.iterrows():
    is_credit = row["credit"] > 0
    cat = categorize_by_rules(row["description"], is_credit)
    if not cat:
        unmatched += 1
        print(f"UNMATCHED: {row['description']} ({'CREDIT' if is_credit else 'DEBIT'})")
    
print(f"Total rows: {len(df)}, Unmatched (need LLM): {unmatched}")

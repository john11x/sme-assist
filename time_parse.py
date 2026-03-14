import time
import sys
from backend.transaction_parser import parse_bank_statement, extract_business_info
from backend.categorizer import categorize_transactions

print("Starting timing test...")
with open("data/user_uploads/bank_statement_q1_2026.txt", "r") as f:
    text = f.read()

start = time.time()
biz_info = extract_business_info(text)
print(f"[{time.time()-start:.2f}s] Extracted business info")

start = time.time()
df = parse_bank_statement(text)
print(f"[{time.time()-start:.2f}s] Parsed bank statement ({len(df)} rows)")

start = time.time()
df = categorize_transactions(df)
print(f"[{time.time()-start:.2f}s] Categorized {len(df)} transactions")

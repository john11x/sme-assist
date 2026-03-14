import os
import sys
from pathlib import Path

# Add project root to python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from backend.consultant import TaxConsultant

def test_consultant():
    """
    Tests the TaxConsultant's ability to analyze a bank statement,
    generate a balance sheet, and draft a tax return.
    """
    print("🚀 Initializing Tax Consultant...")
    try:
        consultant = TaxConsultant()
    except Exception as e:
        print(f"❌ Failed to initialize consultant: {e}")
        return

    user_file = os.path.join(BASE_DIR, "data", "user_uploads", "bank_statement.txt")
    
    if not os.path.exists(user_file):
        print(f"❌ Mock file not found: {user_file}")
        return

    print(f"📂 Found mock file: {user_file}")
    
    # 1. Analyze user data
    print("\n--- Phase 1: Analyzing User Data ---")
    summary = consultant.analyze_user_data(user_file)
    print("Summary Result:")
    print(summary)
    
    # 2. Generate Balance Sheet
    print("\n--- Phase 2: Generating Balance Sheet Draft ---")
    balance_sheet = consultant.generate_balance_sheet_draft(summary)
    print("Balance Sheet Result:")
    print(balance_sheet)
    
    # 3. Draft Tax Return
    print("\n--- Phase 3: Drafting KRA Tax Return ---")
    tax_return = consultant.draft_tax_return(summary)
    print("Tax Return Result:")
    print(tax_return)

if __name__ == "__main__":
    test_consultant()

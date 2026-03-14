"""
Tax Calculator - Deterministic Tax Computation
Computes VAT, Income Tax, PAYE, and other Kenyan taxes using
real numbers from the categorized transaction data.
NO AI guessing - pure math based on current KRA rates.
"""

import pandas as pd
import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────
# KENYAN TAX RATES (2025/2026)
# ─────────────────────────────────────────────────────────

VAT_RATE = 0.16  # Standard VAT rate in Kenya

# Corporate Income Tax
CORPORATE_TAX_RATE = 0.30  # 30% for resident companies
TURNOVER_TAX_RATE = 0.03   # 3% for businesses with turnover < KES 25M

# Individual Income Tax Bands (Monthly)
PAYE_BANDS = [
    (24_000, 0.10),       # First KES 24,000 at 10%
    (8_333, 0.25),        # Next KES 8,333 at 25%
    (467_667, 0.30),      # Next KES 467,667 at 30%
    (300_000, 0.325),     # Next KES 300,000 at 32.5%
    (float("inf"), 0.35), # Above KES 800,000 at 35%
]

# Monthly personal relief
PERSONAL_RELIEF = 2_400  # KES 2,400 per month

# NSSF rates (Tier I + Tier II)
NSSF_TIER1_LIMIT = 7_000
NSSF_TIER1_RATE = 0.06
NSSF_TIER2_LIMIT = 36_000
NSSF_TIER2_RATE = 0.06

# SHIF (Social Health Insurance Fund - replaced NHIF)
SHIF_RATE = 0.0275  # 2.75% of gross salary

# Housing Levy
HOUSING_LEVY_RATE = 0.015  # 1.5% of gross salary


@dataclass
class VATComputation:
    """Structured VAT computation result."""
    output_vat: float = 0.0           # VAT on sales (what you collected)
    input_vat: float = 0.0             # VAT on purchases (what you paid)
    net_vat_payable: float = 0.0       # What you owe KRA (output - input)
    total_sales_excl_vat: float = 0.0
    total_sales_incl_vat: float = 0.0
    total_purchases_excl_vat: float = 0.0
    total_purchases_incl_vat: float = 0.0
    vat_rate: float = VAT_RATE


@dataclass
class IncomeTaxComputation:
    """Structured income tax computation result."""
    total_revenue: float = 0.0
    total_deductible_expenses: float = 0.0
    total_non_deductible: float = 0.0
    taxable_income: float = 0.0
    tax_rate_applied: str = ""
    tax_payable: float = 0.0
    effective_tax_rate: float = 0.0
    qualifies_for_tot: bool = False
    tot_amount: float = 0.0
    recommended_regime: str = ""


@dataclass
class PAYEComputation:
    """PAYE computation for a single employee."""
    employee_name: str = ""
    gross_salary: float = 0.0
    nssf_employee: float = 0.0
    taxable_pay: float = 0.0
    paye_tax: float = 0.0
    personal_relief: float = PERSONAL_RELIEF
    net_paye: float = 0.0
    shif: float = 0.0
    housing_levy: float = 0.0
    net_salary: float = 0.0


@dataclass 
class ProfitAndLoss:
    """Structured Profit & Loss Statement."""
    revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    gross_profit: float = 0.0
    gross_margin: float = 0.0
    
    # Operating expenses breakdown
    rent: float = 0.0
    salaries: float = 0.0
    casual_labour: float = 0.0
    utilities: float = 0.0
    transport: float = 0.0
    marketing: float = 0.0
    insurance: float = 0.0
    professional_fees: float = 0.0
    licenses: float = 0.0
    equipment_depreciation: float = 0.0
    telecom: float = 0.0
    repairs: float = 0.0
    bank_charges: float = 0.0
    other_expenses: float = 0.0
    
    total_operating_expenses: float = 0.0
    operating_profit: float = 0.0
    operating_margin: float = 0.0
    
    # Tax
    tax_provision: float = 0.0
    net_profit: float = 0.0
    net_margin: float = 0.0
    
    # Breakdown details
    expense_breakdown: dict = field(default_factory=dict)
    period: str = ""


@dataclass
class BalanceSheet:
    """Structured Balance Sheet."""
    # Assets
    cash_and_bank: float = 0.0
    accounts_receivable: float = 0.0
    inventory: float = 0.0
    total_current_assets: float = 0.0
    
    equipment: float = 0.0
    less_depreciation: float = 0.0
    total_non_current_assets: float = 0.0
    
    total_assets: float = 0.0
    
    # Liabilities
    vat_payable: float = 0.0
    paye_payable: float = 0.0
    other_tax_payable: float = 0.0
    total_current_liabilities: float = 0.0
    
    total_liabilities: float = 0.0
    
    # Equity
    retained_earnings: float = 0.0
    current_period_profit: float = 0.0
    total_equity: float = 0.0
    
    period: str = ""


# ─────────────────────────────────────────────────────────
# COMPUTATION FUNCTIONS
# ─────────────────────────────────────────────────────────

def compute_vat(df: pd.DataFrame) -> VATComputation:
    """
    Computes VAT from categorized transaction data.
    Assumes all revenue is VAT-inclusive and applicable purchases have VAT.
    """
    vat = VATComputation()
    
    # Output VAT: VAT collected on sales
    revenue_df = df[df["category"] == "revenue"]
    vat.total_sales_incl_vat = revenue_df["credit"].sum()
    vat.total_sales_excl_vat = vat.total_sales_incl_vat / (1 + VAT_RATE)
    vat.output_vat = vat.total_sales_incl_vat - vat.total_sales_excl_vat
    
    # Input VAT: VAT paid on deductible purchases
    vat_purchases = df[df["is_vat_applicable"] == True]
    vat.total_purchases_incl_vat = vat_purchases["debit"].sum()
    vat.total_purchases_excl_vat = vat.total_purchases_incl_vat / (1 + VAT_RATE)
    vat.input_vat = vat.total_purchases_incl_vat - vat.total_purchases_excl_vat
    
    # Net VAT payable to KRA
    vat.net_vat_payable = max(0, vat.output_vat - vat.input_vat)
    
    return vat


def compute_paye(gross_salary: float, employee_name: str = "") -> PAYEComputation:
    """
    Computes PAYE for a single employee using current KRA tax bands.
    """
    paye = PAYEComputation()
    paye.employee_name = employee_name
    paye.gross_salary = gross_salary
    
    # NSSF (employee contribution)
    tier1 = min(gross_salary, NSSF_TIER1_LIMIT) * NSSF_TIER1_RATE
    tier2_base = max(0, min(gross_salary, NSSF_TIER2_LIMIT) - NSSF_TIER1_LIMIT)
    tier2 = tier2_base * NSSF_TIER2_RATE
    paye.nssf_employee = tier1 + tier2
    
    # Taxable pay = Gross - NSSF
    paye.taxable_pay = gross_salary - paye.nssf_employee
    
    # Apply PAYE bands
    remaining = paye.taxable_pay
    tax = 0.0
    for band_limit, rate in PAYE_BANDS:
        taxable_in_band = min(remaining, band_limit)
        tax += taxable_in_band * rate
        remaining -= taxable_in_band
        if remaining <= 0:
            break
    
    paye.paye_tax = tax
    paye.net_paye = max(0, tax - PERSONAL_RELIEF)
    
    # SHIF
    paye.shif = gross_salary * SHIF_RATE
    
    # Housing Levy
    paye.housing_levy = gross_salary * HOUSING_LEVY_RATE
    
    # Net salary
    paye.net_salary = gross_salary - paye.nssf_employee - paye.net_paye - paye.shif - paye.housing_levy
    
    return paye


def compute_income_tax(pnl: ProfitAndLoss) -> IncomeTaxComputation:
    """
    Computes corporate/business income tax.
    Also checks if Turnover Tax (TOT) would be more beneficial.
    """
    tax = IncomeTaxComputation()
    tax.total_revenue = pnl.revenue
    tax.total_deductible_expenses = pnl.total_operating_expenses + pnl.cost_of_goods_sold
    tax.taxable_income = max(0, pnl.operating_profit)
    
    # Check TOT eligibility (annual turnover < KES 25M)
    annual_revenue_estimate = pnl.revenue  # For the period provided
    tax.qualifies_for_tot = annual_revenue_estimate < 25_000_000
    tax.tot_amount = pnl.revenue * TURNOVER_TAX_RATE
    
    # Corporate income tax
    corporate_tax = tax.taxable_income * CORPORATE_TAX_RATE
    tax.tax_payable = corporate_tax
    tax.tax_rate_applied = f"Corporate Rate: {CORPORATE_TAX_RATE*100:.0f}%"
    
    # Recommend the lower tax option
    if tax.qualifies_for_tot and tax.tot_amount < corporate_tax:
        tax.recommended_regime = f"Turnover Tax (TOT) - saves KES {corporate_tax - tax.tot_amount:,.2f}"
    else:
        tax.recommended_regime = "Standard Corporate Income Tax"
    
    if pnl.revenue > 0:
        tax.effective_tax_rate = (tax.tax_payable / pnl.revenue) * 100
    
    return tax


def compute_profit_and_loss(df: pd.DataFrame, period: str = "") -> ProfitAndLoss:
    """
    Computes a real Profit & Loss statement from categorized transaction data.
    """
    pnl = ProfitAndLoss()
    pnl.period = period
    
    # Revenue
    pnl.revenue = df[df["category"] == "revenue"]["credit"].sum()
    
    # COGS
    pnl.cost_of_goods_sold = df[df["category"] == "cogs"]["debit"].sum()
    
    # Gross Profit
    pnl.gross_profit = pnl.revenue - pnl.cost_of_goods_sold
    pnl.gross_margin = (pnl.gross_profit / pnl.revenue * 100) if pnl.revenue > 0 else 0
    
    # Operating Expenses
    expense_mapping = {
        "rent": "rent",
        "salaries": "salaries",
        "casual_labour": "casual_labour",
        "utilities": "utilities",
        "transport": "transport",
        "marketing": "marketing",
        "insurance": "insurance",
        "professional": "professional_fees",
        "licenses": "licenses",
        "equipment": "equipment_depreciation",
        "telecom": "telecom",
        "repairs": "repairs",
        "bank_charges": "bank_charges",
        "statutory": "other_expenses",
        "other_expense": "other_expenses",
    }
    
    pnl.expense_breakdown = {}
    total_opex = 0
    
    for cat_key, pnl_field in expense_mapping.items():
        amount = df[df["category"] == cat_key]["debit"].sum()
        if amount > 0:
            current = getattr(pnl, pnl_field, 0)
            setattr(pnl, pnl_field, current + amount)
            total_opex += amount
            
            label = cat_key.replace("_", " ").title()
            if label in pnl.expense_breakdown:
                pnl.expense_breakdown[label] += amount
            else:
                pnl.expense_breakdown[label] = amount
    
    pnl.total_operating_expenses = total_opex
    pnl.operating_profit = pnl.gross_profit - pnl.total_operating_expenses
    pnl.operating_margin = (pnl.operating_profit / pnl.revenue * 100) if pnl.revenue > 0 else 0
    
    # Tax provision
    income_tax = compute_income_tax(pnl)
    pnl.tax_provision = income_tax.tax_payable
    pnl.net_profit = pnl.operating_profit - pnl.tax_provision
    pnl.net_margin = (pnl.net_profit / pnl.revenue * 100) if pnl.revenue > 0 else 0
    
    return pnl


def compute_balance_sheet(
    pnl: ProfitAndLoss, 
    vat: VATComputation,
    closing_balance: float = 0,
    period: str = ""
) -> BalanceSheet:
    """
    Computes a simple Balance Sheet from the P&L and VAT data.
    """
    bs = BalanceSheet()
    bs.period = period
    
    # Current Assets
    bs.cash_and_bank = closing_balance
    bs.inventory = pnl.cost_of_goods_sold * 0.1  # Estimate: 10% of COGS as remaining stock
    bs.total_current_assets = bs.cash_and_bank + bs.inventory
    
    # Non-Current Assets
    bs.equipment = pnl.equipment_depreciation  # Capital purchases in period
    bs.less_depreciation = bs.equipment * 0.25  # 25% depreciation rate
    bs.total_non_current_assets = bs.equipment - bs.less_depreciation
    
    bs.total_assets = bs.total_current_assets + bs.total_non_current_assets
    
    # Current Liabilities
    bs.vat_payable = vat.net_vat_payable
    bs.paye_payable = 0  # Already paid if shown in statement
    income_tax = compute_income_tax(pnl)
    bs.other_tax_payable = income_tax.tax_payable
    bs.total_current_liabilities = bs.vat_payable + bs.paye_payable + bs.other_tax_payable
    
    bs.total_liabilities = bs.total_current_liabilities
    
    # Equity
    bs.current_period_profit = pnl.net_profit
    bs.retained_earnings = bs.total_assets - bs.total_liabilities - bs.current_period_profit
    bs.total_equity = bs.retained_earnings + bs.current_period_profit
    
    return bs


def extract_employees_from_df(df: pd.DataFrame) -> list[PAYEComputation]:
    """
    Identifies employees from salary transactions and computes PAYE for each.
    """
    salary_df = df[df["category"] == "salaries"].copy()
    
    if salary_df.empty:
        return []
    
    # Group by description to identify unique employees
    employees = {}
    for _, row in salary_df.iterrows():
        desc = row["description"]
        # Try to extract employee name
        name_match = None
        for pattern in [
            r"SALARY.*?-\s*(.+?)(?:\s*\(|$)",
            r"SAL.*?-\s*(.+?)(?:\s*\(|$)",
            r"PAYROLL.*?-\s*(.+?)(?:\s*\(|$)",
        ]:
            name_match = re.search(pattern, desc, re.IGNORECASE)
            if name_match:
                break
        
        name = name_match.group(1).strip() if name_match else desc
        
        if name not in employees:
            employees[name] = {"total": 0, "count": 0}
        employees[name]["total"] += row["debit"]
        employees[name]["count"] += 1
    
    # Compute PAYE for each employee (using average monthly salary)
    paye_results = []
    for name, data in employees.items():
        avg_monthly = data["total"] / max(data["count"], 1)
        paye = compute_paye(avg_monthly, name)
        paye_results.append(paye)
    
    return paye_results

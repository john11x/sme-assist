"""
Report Generator - Formats computed data into professional reports.
Converts dataclasses into displayable Markdown/HTML for the UI.
"""

import pandas as pd
import textwrap
from backend.tax_calculator import (
    ProfitAndLoss, BalanceSheet, VATComputation, 
    IncomeTaxComputation, PAYEComputation,
    compute_income_tax,
)


def format_kes(amount: float) -> str:
    """Formats a number as KES currency."""
    if amount < 0:
        return f"(KES {abs(amount):,.2f})"
    return f"KES {amount:,.2f}"


def generate_pnl_report(pnl: ProfitAndLoss) -> str:
    """Generates a formatted Profit & Loss statement."""
    
    # Build expense rows
    expense_rows = ""
    for label, amount in sorted(pnl.expense_breakdown.items(), key=lambda x: -x[1]):
        if amount > 0:
            expense_rows += f"""<tr><td style="padding: 6px 12px; color: #cbd5e1;">&nbsp;&nbsp;&nbsp;{label}</td><td style="padding: 6px 12px; text-align: right; color: #f87171;">{format_kes(amount)}</td></tr>"""
    
    return textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 28px; margin-bottom: 20px;">
        <h2 style="color: #60a5fa; margin-top: 0; font-size: 1.3rem;">Profit & Loss Statement</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 20px;">{pnl.period}</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <tr style="border-bottom: 2px solid rgba(96, 165, 250, 0.3);">
                <th style="text-align: left; padding: 10px 12px; color: #94a3b8; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em;">Item</th>
                <th style="text-align: right; padding: 10px 12px; color: #94a3b8; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em;">Amount</th>
            </tr>
            <tr style="background: rgba(96, 165, 250, 0.05);">
                <td style="padding: 10px 12px; font-weight: 600; color: #f8fafc;">Revenue</td>
                <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #4ade80;">{format_kes(pnl.revenue)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 12px; color: #cbd5e1;">&nbsp;&nbsp;&nbsp;Less: Cost of Goods Sold</td>
                <td style="padding: 6px 12px; text-align: right; color: #f87171;">({format_kes(pnl.cost_of_goods_sold)})</td>
            </tr>
            <tr style="border-top: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(96, 165, 250, 0.08);">
                <td style="padding: 10px 12px; font-weight: 700; color: #f8fafc;">Gross Profit</td>
                <td style="padding: 10px 12px; text-align: right; font-weight: 700; color: #f8fafc;">{format_kes(pnl.gross_profit)} <span style="color: #64748b; font-size: 0.75rem;">({pnl.gross_margin:.1f}%)</span></td>
            </tr>
            <tr><td colspan="2" style="padding: 8px 12px; color: #94a3b8; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;">Operating Expenses</td></tr>
            {expense_rows}
            <tr style="border-top: 1px solid rgba(255,255,255,0.15);">
                <td style="padding: 10px 12px; font-weight: 600; color: #cbd5e1;">Total Operating Expenses</td>
                <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #f87171;">{format_kes(pnl.total_operating_expenses)}</td>
            </tr>
            <tr style="border-top: 2px solid rgba(96, 165, 250, 0.3); background: rgba(96, 165, 250, 0.08);">
                <td style="padding: 12px; font-weight: 700; font-size: 1rem; color: #f8fafc;">Operating Profit</td>
                <td style="padding: 12px; text-align: right; font-weight: 700; font-size: 1rem; color: {'#4ade80' if pnl.operating_profit >= 0 else '#f87171'};">{format_kes(pnl.operating_profit)} <span style="color: #64748b; font-size: 0.75rem;">({pnl.operating_margin:.1f}%)</span></td>
            </tr>
            <tr>
                <td style="padding: 6px 12px; color: #cbd5e1;">&nbsp;&nbsp;&nbsp;Less: Tax Provision</td>
                <td style="padding: 6px 12px; text-align: right; color: #fbbf24;">({format_kes(pnl.tax_provision)})</td>
            </tr>
            <tr style="border-top: 2px solid rgba(74, 222, 128, 0.3); background: rgba(74, 222, 128, 0.08);">
                <td style="padding: 14px 12px; font-weight: 700; font-size: 1.1rem; color: #f8fafc;">NET PROFIT</td>
                <td style="padding: 14px 12px; text-align: right; font-weight: 700; font-size: 1.1rem; color: {'#4ade80' if pnl.net_profit >= 0 else '#f87171'};">{format_kes(pnl.net_profit)}</td>
            </tr>
        </table>
    </div>
    """).strip()


def generate_balance_sheet_report(bs: BalanceSheet) -> str:
    """Generates a formatted Balance Sheet."""
    return textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 28px; margin-bottom: 20px;">
        <h2 style="color: #60a5fa; margin-top: 0; font-size: 1.3rem;">Statement of Financial Position</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 20px;">As at {bs.period} | IFRS for SMEs</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <tr style="border-bottom: 2px solid rgba(96, 165, 250, 0.3);">
                <th style="text-align: left; padding: 10px 12px; color: #94a3b8; text-transform: uppercase; font-size: 0.75rem;">Item</th>
                <th style="text-align: right; padding: 10px 12px; color: #94a3b8; text-transform: uppercase; font-size: 0.75rem;">Amount</th>
            </tr>
            <tr><td colspan="2" style="padding: 10px 12px; color: #60a5fa; font-weight: 700; font-size: 0.85rem;">ASSETS</td></tr>
            <tr><td colspan="2" style="padding: 4px 12px; color: #94a3b8; font-weight: 600; font-size: 0.8rem;">Current Assets</td></tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">Cash & Bank</td>
                <td style="padding: 4px 12px; text-align: right; color: #f8fafc;">{format_kes(bs.cash_and_bank)}</td>
            </tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">Inventory (Estimated)</td>
                <td style="padding: 4px 12px; text-align: right; color: #f8fafc;">{format_kes(bs.inventory)}</td>
            </tr>
            <tr style="border-top: 1px solid rgba(255,255,255,0.06);">
                <td style="padding: 6px 12px; font-weight: 600; color: #e2e8f0;">Total Current Assets</td>
                <td style="padding: 6px 12px; text-align: right; font-weight: 600; color: #f8fafc;">{format_kes(bs.total_current_assets)}</td>
            </tr>
            <tr><td colspan="2" style="padding: 8px 12px 4px; color: #94a3b8; font-weight: 600; font-size: 0.8rem;">Non-Current Assets</td></tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">Equipment & Assets</td>
                <td style="padding: 4px 12px; text-align: right; color: #f8fafc;">{format_kes(bs.equipment)}</td>
            </tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">Less: Depreciation (25%)</td>
                <td style="padding: 4px 12px; text-align: right; color: #f87171;">({format_kes(bs.less_depreciation)})</td>
            </tr>
            <tr style="border-top: 2px solid rgba(96, 165, 250, 0.2); background: rgba(96, 165, 250, 0.05);">
                <td style="padding: 10px 12px; font-weight: 700; color: #f8fafc;">TOTAL ASSETS</td>
                <td style="padding: 10px 12px; text-align: right; font-weight: 700; color: #60a5fa;">{format_kes(bs.total_assets)}</td>
            </tr>
            <tr><td colspan="2" style="padding: 14px 12px 6px; color: #f87171; font-weight: 700; font-size: 0.85rem;">LIABILITIES</td></tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">VAT Payable</td>
                <td style="padding: 4px 12px; text-align: right; color: #f8fafc;">{format_kes(bs.vat_payable)}</td>
            </tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">Income Tax Payable</td>
                <td style="padding: 4px 12px; text-align: right; color: #f8fafc;">{format_kes(bs.other_tax_payable)}</td>
            </tr>
            <tr style="border-top: 1px solid rgba(255,255,255,0.06);">
                <td style="padding: 8px 12px; font-weight: 600; color: #e2e8f0;">Total Liabilities</td>
                <td style="padding: 8px 12px; text-align: right; font-weight: 600; color: #f8fafc;">{format_kes(bs.total_liabilities)}</td>
            </tr>
            <tr><td colspan="2" style="padding: 14px 12px 6px; color: #4ade80; font-weight: 700; font-size: 0.85rem;">EQUITY</td></tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">Retained Earnings</td>
                <td style="padding: 4px 12px; text-align: right; color: #f8fafc;">{format_kes(bs.retained_earnings)}</td>
            </tr>
            <tr>
                <td style="padding: 4px 12px 4px 24px; color: #cbd5e1;">Current Period Profit</td>
                <td style="padding: 4px 12px; text-align: right; color: #4ade80;">{format_kes(bs.current_period_profit)}</td>
            </tr>
            <tr style="border-top: 2px solid rgba(74, 222, 128, 0.2); background: rgba(74, 222, 128, 0.05);">
                <td style="padding: 10px 12px; font-weight: 700; color: #f8fafc;">TOTAL EQUITY + LIABILITIES</td>
                <td style="padding: 10px 12px; text-align: right; font-weight: 700; color: #4ade80;">{format_kes(bs.total_equity + bs.total_liabilities)}</td>
            </tr>
        </table>
    </div>
    """).strip()


def generate_vat_report(vat: VATComputation) -> str:
    """Generates a formatted VAT computation report."""
    return textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 28px; margin-bottom: 20px;">
        <h2 style="color: #60a5fa; margin-top: 0; font-size: 1.3rem;">VAT-3 Return Computation</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 20px;">Standard Rate: {vat.vat_rate*100:.0f}%</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 8px 12px; color: #cbd5e1;">Total Sales (VAT Inclusive)</td>
                <td style="padding: 8px 12px; text-align: right; color: #f8fafc;">{format_kes(vat.total_sales_incl_vat)}</td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 8px 12px; color: #cbd5e1;">Total Sales (VAT Exclusive)</td>
                <td style="padding: 8px 12px; text-align: right; color: #f8fafc;">{format_kes(vat.total_sales_excl_vat)}</td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(248, 113, 113, 0.05);">
                <td style="padding: 8px 12px; font-weight: 600; color: #f87171;">OUTPUT VAT (Collected)</td>
                <td style="padding: 8px 12px; text-align: right; font-weight: 600; color: #f87171;">{format_kes(vat.output_vat)}</td>
            </tr>
            <tr><td colspan="2" style="padding: 6px;"></td></tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 8px 12px; color: #cbd5e1;">Total Purchases (VAT Inclusive)</td>
                <td style="padding: 8px 12px; text-align: right; color: #f8fafc;">{format_kes(vat.total_purchases_incl_vat)}</td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 8px 12px; color: #cbd5e1;">Total Purchases (VAT Exclusive)</td>
                <td style="padding: 8px 12px; text-align: right; color: #f8fafc;">{format_kes(vat.total_purchases_excl_vat)}</td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(74, 222, 128, 0.05);">
                <td style="padding: 8px 12px; font-weight: 600; color: #4ade80;">INPUT VAT (Claimable)</td>
                <td style="padding: 8px 12px; text-align: right; font-weight: 600; color: #4ade80;">{format_kes(vat.input_vat)}</td>
            </tr>
            <tr style="border-top: 2px solid rgba(251, 191, 36, 0.3); background: rgba(251, 191, 36, 0.08);">
                <td style="padding: 14px 12px; font-weight: 700; font-size: 1.05rem; color: #f8fafc;">NET VAT PAYABLE TO KRA</td>
                <td style="padding: 14px 12px; text-align: right; font-weight: 700; font-size: 1.05rem; color: #fbbf24;">{format_kes(vat.net_vat_payable)}</td>
            </tr>
        </table>
    </div>
    """).strip()


def generate_paye_report(employees: list[PAYEComputation]) -> str:
    """Generates a formatted PAYE schedule for all employees."""
    
    if not employees:
        return "<p style='color: #94a3b8;'>No salary transactions detected.</p>"
    
    rows = ""
    totals = {"gross": 0, "nssf": 0, "paye": 0, "shif": 0, "housing": 0, "net": 0}
    
    for emp in employees:
        rows += f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);"><td style="padding: 6px 10px; color: #f8fafc; font-weight: 500;">{emp.employee_name}</td><td style="padding: 6px 10px; text-align: right; color: #cbd5e1;">{emp.gross_salary:,.0f}</td><td style="padding: 6px 10px; text-align: right; color: #cbd5e1;">{emp.nssf_employee:,.0f}</td><td style="padding: 6px 10px; text-align: right; color: #fbbf24;">{emp.net_paye:,.0f}</td><td style="padding: 6px 10px; text-align: right; color: #cbd5e1;">{emp.shif:,.0f}</td><td style="padding: 6px 10px; text-align: right; color: #cbd5e1;">{emp.housing_levy:,.0f}</td><td style="padding: 6px 10px; text-align: right; color: #4ade80; font-weight: 600;">{emp.net_salary:,.0f}</td></tr>"""
        totals["gross"] += emp.gross_salary
        totals["nssf"] += emp.nssf_employee
        totals["paye"] += emp.net_paye
        totals["shif"] += emp.shif
        totals["housing"] += emp.housing_levy
        totals["net"] += emp.net_salary
    
    return textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 28px; margin-bottom: 20px;">
        <h2 style="color: #60a5fa; margin-top: 0; font-size: 1.3rem;">PAYE Schedule (P10)</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 20px;">Monthly payroll computation per employee</p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
            <div style="background: rgba(96, 165, 250, 0.08); border: 1px solid rgba(96, 165, 250, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Total Gross Payroll</div>
                <div style="color: #f8fafc; font-size: 1.2rem; font-weight: 700;">{format_kes(totals['gross'])}</div>
            </div>
            <div style="background: rgba(251, 191, 36, 0.08); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Total PAYE Payable</div>
                <div style="color: #fbbf24; font-size: 1.2rem; font-weight: 700;">{format_kes(totals['paye'])}</div>
            </div>
            <div style="background: rgba(96, 165, 250, 0.08); border: 1px solid rgba(96, 165, 250, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Total SHIF/Health</div>
                <div style="color: #60a5fa; font-size: 1.2rem; font-weight: 700;">{format_kes(totals['shif'])}</div>
            </div>
            <div style="background: rgba(74, 222, 128, 0.08); border: 1px solid rgba(74, 222, 128, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Total Net Salary</div>
                <div style="color: #4ade80; font-size: 1.2rem; font-weight: 700;">{format_kes(totals['net'])}</div>
            </div>
        </div>
        <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem;">
            <tr style="border-bottom: 2px solid rgba(96, 165, 250, 0.3);">
                <th style="text-align: left; padding: 8px 10px; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">Employee</th>
                <th style="text-align: right; padding: 8px 10px; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">Gross (KES)</th>
                <th style="text-align: right; padding: 8px 10px; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">NSSF</th>
                <th style="text-align: right; padding: 8px 10px; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">PAYE</th>
                <th style="text-align: right; padding: 8px 10px; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">SHIF</th>
                <th style="text-align: right; padding: 8px 10px; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">H. Levy</th>
                <th style="text-align: right; padding: 8px 10px; color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">Net Pay</th>
            </tr>
            {rows}
            <tr style="border-top: 2px solid rgba(96, 165, 250, 0.3); background: rgba(96, 165, 250, 0.05);">
                <td style="padding: 10px; font-weight: 700; color: #f8fafc;">TOTALS</td>
                <td style="padding: 10px; text-align: right; font-weight: 700; color: #f8fafc;">{totals['gross']:,.0f}</td>
                <td style="padding: 10px; text-align: right; font-weight: 700; color: #f8fafc;">{totals['nssf']:,.0f}</td>
                <td style="padding: 10px; text-align: right; font-weight: 700; color: #fbbf24;">{totals['paye']:,.0f}</td>
                <td style="padding: 10px; text-align: right; font-weight: 700; color: #f8fafc;">{totals['shif']:,.0f}</td>
                <td style="padding: 10px; text-align: right; font-weight: 700; color: #f8fafc;">{totals['housing']:,.0f}</td>
                <td style="padding: 10px; text-align: right; font-weight: 700; color: #4ade80;">{totals['net']:,.0f}</td>
            </tr>
        </table>
        </div>
    </div>
    """).strip()


def generate_tax_summary(pnl: ProfitAndLoss, vat: VATComputation) -> str:
    """Generates a tax recommendations summary."""
    income_tax = compute_income_tax(pnl)
    
    return textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 16px; padding: 28px; margin-bottom: 20px;">
        <h2 style="color: #fbbf24; margin-top: 0; font-size: 1.3rem;">Tax Intelligence Summary</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
            <div style="background: rgba(74, 222, 128, 0.08); border: 1px solid rgba(74, 222, 128, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Total Revenue</div>
                <div style="color: #4ade80; font-size: 1.4rem; font-weight: 700;">{format_kes(pnl.revenue)}</div>
            </div>
            <div style="background: rgba(96, 165, 250, 0.08); border: 1px solid rgba(96, 165, 250, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Net Profit</div>
                <div style="color: #60a5fa; font-size: 1.4rem; font-weight: 700;">{format_kes(pnl.net_profit)}</div>
            </div>
            <div style="background: rgba(251, 191, 36, 0.08); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">VAT Payable</div>
                <div style="color: #fbbf24; font-size: 1.4rem; font-weight: 700;">{format_kes(vat.net_vat_payable)}</div>
            </div>
            <div style="background: rgba(248, 113, 113, 0.08); border: 1px solid rgba(248, 113, 113, 0.2); border-radius: 12px; padding: 16px;">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Income Tax</div>
                <div style="color: #f87171; font-size: 1.4rem; font-weight: 700;">{format_kes(income_tax.tax_payable)}</div>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.03); border-radius: 10px; padding: 16px;">
            <h3 style="color: #fbbf24; font-size: 0.9rem; margin-top: 0;">Recommendation</h3>
            <p style="color: #e2e8f0; font-size: 0.85rem; line-height: 1.6;"><strong>Tax Regime:</strong> {income_tax.recommended_regime}<br>{'<span style="color: #4ade80;">✅ Your business qualifies for Turnover Tax (TOT) at 3% - this could be significantly cheaper than the standard 30% corporate rate.</span>' if income_tax.qualifies_for_tot and income_tax.tot_amount < income_tax.tax_payable else ''}{'<br><strong>TOT Amount:</strong> ' + format_kes(income_tax.tot_amount) + ' vs Corporate Tax: ' + format_kes(income_tax.tax_payable) if income_tax.qualifies_for_tot else ''}</p>
            <p style="color: #cbd5e1; font-size: 0.82rem; line-height: 1.5;"><strong>Effective Tax Rate:</strong> {income_tax.effective_tax_rate:.1f}%<br><strong>Total Deductible Expenses:</strong> {format_kes(income_tax.total_deductible_expenses)}</p>
        </div>
    </div>
    """).strip()

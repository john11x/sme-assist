"""
Compliance Engine - Deadlines, Penalties, and Tax Intelligence
Provides proactive compliance advice, deadline tracking, and penalty estimation.
"""

from datetime import datetime, date, timedelta
from dataclasses import dataclass
import textwrap
from backend.tax_calculator import (
    ProfitAndLoss, VATComputation, IncomeTaxComputation, compute_income_tax,
)


@dataclass
class ComplianceDeadline:
    """A single tax compliance deadline."""
    obligation: str
    description: str
    due_date: date
    days_remaining: int
    status: str  # "upcoming", "due_soon", "overdue"
    penalty_if_late: str
    icon: str


@dataclass
class PenaltyEstimate:
    """Estimated penalty for late filing."""
    obligation: str
    due_date: str
    days_late: int
    base_penalty: float
    interest_rate: float
    interest_amount: float
    total_penalty: float


def get_compliance_deadlines(reference_date: date = None) -> list[ComplianceDeadline]:
    """
    Returns all upcoming KRA compliance deadlines relative to the given date.
    Uses actual KRA filing calendar rules.
    """
    if reference_date is None:
        reference_date = date.today()
    
    current_month = reference_date.month
    current_year = reference_date.year
    
    # Calculate next dates
    next_month = current_month + 1 if current_month < 12 else 1
    next_month_year = current_year if current_month < 12 else current_year + 1
    
    deadlines = []
    
    # 1. PAYE - Due by 9th of the following month
    paye_due = date(next_month_year, next_month, 9)
    days_to_paye = (paye_due - reference_date).days
    deadlines.append(ComplianceDeadline(
        obligation="PAYE (P10)",
        description=f"Monthly PAYE return for {reference_date.strftime('%B %Y')}",
        due_date=paye_due,
        days_remaining=days_to_paye,
        status="overdue" if days_to_paye < 0 else ("due_soon" if days_to_paye <= 5 else "upcoming"),
        penalty_if_late="25% of tax due or KES 10,000 (whichever is higher) + 2% interest p.m.",
        icon="user"
    ))
    
    # 2. VAT - Due by 20th of the following month
    vat_due = date(next_month_year, next_month, 20)
    days_to_vat = (vat_due - reference_date).days
    deadlines.append(ComplianceDeadline(
        obligation="VAT-3 Return",
        description=f"Monthly VAT return for {reference_date.strftime('%B %Y')}",
        due_date=vat_due,
        days_remaining=days_to_vat,
        status="overdue" if days_to_vat < 0 else ("due_soon" if days_to_vat <= 5 else "upcoming"),
        penalty_if_late="5% of tax due or KES 20,000 (whichever is higher) + 2% interest p.m.",
        icon="file-text"
    ))
    
    # 3. NHIF/SHIF - Due by 9th of the following month
    shif_due = date(next_month_year, next_month, 9)
    days_to_shif = (shif_due - reference_date).days
    deadlines.append(ComplianceDeadline(
        obligation="SHIF Contribution",
        description=f"Social Health Insurance for {reference_date.strftime('%B %Y')}",
        due_date=shif_due,
        days_remaining=days_to_shif,
        status="overdue" if days_to_shif < 0 else ("due_soon" if days_to_shif <= 5 else "upcoming"),
        penalty_if_late="5% penalty per month on unpaid amount",
        icon="activity"
    ))
    
    # 4. NSSF - Due by 15th of the following month
    nssf_due = date(next_month_year, next_month, 15)
    days_to_nssf = (nssf_due - reference_date).days
    deadlines.append(ComplianceDeadline(
        obligation="NSSF Contribution",
        description=f"National Social Security Fund for {reference_date.strftime('%B %Y')}",
        due_date=nssf_due,
        days_remaining=days_to_nssf,
        status="overdue" if days_to_nssf < 0 else ("due_soon" if days_to_nssf <= 5 else "upcoming"),
        penalty_if_late="5% penalty + 3% interest per month",
        icon="shield"
    ))
    
    # 5. Housing Levy - Due by 9th of the following month
    hl_due = date(next_month_year, next_month, 9)
    days_to_hl = (hl_due - reference_date).days
    deadlines.append(ComplianceDeadline(
        obligation="Housing Levy",
        description=f"Affordable Housing Levy for {reference_date.strftime('%B %Y')}",
        due_date=hl_due,
        days_remaining=days_to_hl,
        status="overdue" if days_to_hl < 0 else ("due_soon" if days_to_hl <= 5 else "upcoming"),
        penalty_if_late="3% penalty per month on outstanding amount",
        icon="home"
    ))
    
    # 6. Annual Income Tax - Due by 30th June
    annual_due = date(current_year, 6, 30)
    if annual_due < reference_date:
        annual_due = date(current_year + 1, 6, 30)
    days_to_annual = (annual_due - reference_date).days
    deadlines.append(ComplianceDeadline(
        obligation="Annual Income Tax Return",
        description=f"Company income tax return for FY {annual_due.year - 1}/{annual_due.year}",
        due_date=annual_due,
        days_remaining=days_to_annual,
        status="overdue" if days_to_annual < 0 else ("due_soon" if days_to_annual <= 30 else "upcoming"),
        penalty_if_late="5% of tax due or KES 20,000 + 2% interest p.m. Late filing penalty: KES 2,000/month",
        icon="calendar"
    ))
    
    # 7. Turnover Tax (TOT) - Due by 20th of the following month
    tot_due = date(next_month_year, next_month, 20)
    days_to_tot = (tot_due - reference_date).days
    deadlines.append(ComplianceDeadline(
        obligation="Turnover Tax (TOT)",
        description=f"For businesses under KES 25M turnover - {reference_date.strftime('%B %Y')}",
        due_date=tot_due,
        days_remaining=days_to_tot,
        status="overdue" if days_to_tot < 0 else ("due_soon" if days_to_tot <= 5 else "upcoming"),
        penalty_if_late="5% of tax due or KES 20,000 (whichever is higher)",
        icon="dollar-sign"
    ))
    
    # Sort by days remaining
    deadlines.sort(key=lambda d: d.days_remaining)
    return deadlines


def estimate_late_penalty(
    obligation: str, 
    tax_amount: float, 
    due_date: date, 
    current_date: date = None
) -> PenaltyEstimate:
    """
    Estimates the penalty for late filing/payment of a specific tax obligation.
    Based on KRA penalty structure.
    """
    if current_date is None:
        current_date = date.today()
    
    days_late = max(0, (current_date - due_date).days)
    months_late = max(1, days_late // 30)
    
    # KRA penalty rates by obligation
    penalties = {
        "PAYE": {"base_pct": 0.25, "min_penalty": 10_000, "interest_rate": 0.02},
        "VAT": {"base_pct": 0.05, "min_penalty": 20_000, "interest_rate": 0.02},
        "Income Tax": {"base_pct": 0.05, "min_penalty": 20_000, "interest_rate": 0.02},
        "SHIF": {"base_pct": 0.05, "min_penalty": 0, "interest_rate": 0.05},
        "NSSF": {"base_pct": 0.05, "min_penalty": 0, "interest_rate": 0.03},
        "Housing Levy": {"base_pct": 0.03, "min_penalty": 0, "interest_rate": 0.03},
        "TOT": {"base_pct": 0.05, "min_penalty": 20_000, "interest_rate": 0.02},
    }
    
    rates = penalties.get(obligation, {"base_pct": 0.05, "min_penalty": 10_000, "interest_rate": 0.02})
    
    base_penalty = max(tax_amount * rates["base_pct"], rates["min_penalty"])
    interest_amount = tax_amount * rates["interest_rate"] * months_late
    total = base_penalty + interest_amount
    
    return PenaltyEstimate(
        obligation=obligation,
        due_date=due_date.strftime("%d-%b-%Y"),
        days_late=days_late,
        base_penalty=base_penalty,
        interest_rate=rates["interest_rate"] * 100,
        interest_amount=interest_amount,
        total_penalty=total,
    )


def generate_tax_savings_advice(pnl: ProfitAndLoss, vat: VATComputation) -> list[dict]:
    """
    Generates specific, actionable tax savings recommendations based on the business data.
    Returns a list of recommendations with title, description, and estimated savings.
    """
    advice = []
    income_tax = compute_income_tax(pnl)
    
    # 1. TOT vs Corporate Tax
    if income_tax.qualifies_for_tot and income_tax.tot_amount < income_tax.tax_payable:
        savings = income_tax.tax_payable - income_tax.tot_amount
        advice.append({
            "title": "Switch to Turnover Tax (TOT)",
            "description": (
                f"Your revenue of KES {pnl.revenue:,.0f} is under KES 25M, making you eligible for TOT at 3%. "
                f"This would cost KES {income_tax.tot_amount:,.0f} vs Corporate Tax of KES {income_tax.tax_payable:,.0f}."
            ),
            "savings": savings,
            "priority": "HIGH",
            "icon": "trending-up",
        })
    
    # 2. Unclaimed VAT input
    if vat.input_vat > 0:
        advice.append({
            "title": "Ensure All Input VAT is Claimed",
            "description": (
                f"You have KES {vat.input_vat:,.0f} in claimable input VAT. "
                f"Make sure ALL purchase invoices are eTIMS-compliant to maximize this claim. "
                f"Non-compliant invoices will be disallowed by KRA."
            ),
            "savings": vat.input_vat * 0.1,  # Estimate 10% may be at risk
            "priority": "HIGH",
            "icon": "file-check",
        })
    
    # 3. Depreciation for equipment
    if pnl.equipment_depreciation > 0:
        wear_tear = pnl.equipment_depreciation * 0.125  # 12.5% wear and tear
        advice.append({
            "title": "Claim Capital Wear & Tear Allowance",
            "description": (
                f"Capital expenditure of KES {pnl.equipment_depreciation:,.0f} qualifies for "
                f"wear and tear deductions under the Income Tax Act. Computers qualify for 30% p.a."
            ),
            "savings": wear_tear,
            "priority": "MEDIUM",
            "icon": "layers",
        })
    
    # 4. Personal expense separation
    total_personal = sum(1 for _ in [])  # Placeholder
    advice.append({
        "title": "Maintain Separate Personal Account",
        "description": (
            "Personal expenses flowing through your business account reduce credibility with KRA. "
            "Open a separate personal account to avoid mixed transactions being questioned during audits."
        ),
        "savings": 0,
        "priority": "MEDIUM",
        "icon": "briefcase",
    })
    
    # 5. eTIMS compliance
    advice.append({
        "title": "Register for eTIMS (Mandatory)",
        "description": (
            "All VAT-registered businesses must use eTIMS for invoicing. "
            "Non-compliance can lead to disallowed deductions. Ensure your suppliers also issue eTIMS invoices."
        ),
        "savings": 0,
        "priority": "CRITICAL",
        "icon": "alert-circle",
    })
    
    # 6. NSSF optimization
    if pnl.salaries > 0:
        advice.append({
            "title": "Verify NSSF Tier II Compliance",
            "description": (
                f"With a payroll of KES {pnl.salaries:,.0f}, ensure you're calculating NSSF correctly under "
                f"the new Tier I (up to KES 7,000) and Tier II (KES 7,001-36,000) rates at 6% each."
            ),
            "savings": 0,
            "priority": "LOW",
            "icon": "users",
        })
    
    return advice


def render_compliance_dashboard_html(deadlines: list[ComplianceDeadline]) -> str:
    """Renders the compliance calendar as HTML for Streamlit."""
    
    rows = ""
    for d in deadlines:
        if d.status == "overdue":
            color = "#f87171"
            badge_bg = "rgba(248, 113, 113, 0.15)"
            badge_border = "rgba(248, 113, 113, 0.3)"
            badge_text = "OVERDUE"
        elif d.status == "due_soon":
            color = "#fbbf24"
            badge_bg = "rgba(251, 191, 36, 0.15)"
            badge_border = "rgba(251, 191, 36, 0.3)"
            badge_text = "DUE SOON"
        else:
            color = "#4ade80"
            badge_bg = "rgba(74, 222, 128, 0.15)"
            badge_border = "rgba(74, 222, 128, 0.3)"
            badge_text = f"{d.days_remaining} days"
        
        rows += textwrap.dedent(f"""
        <div style="display: flex; align-items: center; gap: 16px; padding: 14px 16px; 
                    background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.05);
                    border-left: 3px solid {color}; border-radius: 10px; margin-bottom: 8px;
                    transition: all 0.2s ease;">
            <div style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.05); border-radius: 8px; color: {color};">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div style="flex: 1;">
                <div style="color: #f8fafc; font-weight: 600; font-size: 0.9rem;">{d.obligation}</div>
                <div style="color: #94a3b8; font-size: 0.78rem; margin-top: 2px;">{d.description}</div>
                <div style="color: #64748b; font-size: 0.72rem; margin-top: 4px;">⚠️ Penalty: {d.penalty_if_late}</div>
            </div>
            <div style="text-align: right;">
                <div style="display: inline-block; background: {badge_bg}; border: 1px solid {badge_border};
                            color: {color}; font-size: 0.72rem; font-weight: 600; padding: 3px 10px;
                            border-radius: 20px;">{badge_text}</div>
                <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 4px;">{d.due_date.strftime('%d %b %Y')}</div>
            </div>
        </div>
        """).strip()
    
    return textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
        <h2 style="color: #60a5fa; margin-top: 0; font-size: 1.3rem;">Compliance Calendar</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 16px;">Upcoming KRA filing deadlines - never miss a deadline again</p>
        {rows}
    </div>
    """).strip()


def render_tax_savings_html(advice: list[dict]) -> str:
    """Renders tax savings recommendations as HTML."""
    
    cards = ""
    for tip in advice:
        priority_colors = {
            "CRITICAL": ("#f87171", "rgba(248, 113, 113, 0.1)"),
            "HIGH": ("#fbbf24", "rgba(251, 191, 36, 0.1)"),
            "MEDIUM": ("#60a5fa", "rgba(96, 165, 250, 0.1)"),
            "LOW": ("#4ade80", "rgba(74, 222, 128, 0.1)"),
        }
        color, bg = priority_colors.get(tip["priority"], ("#94a3b8", "rgba(148,163,184,0.1)"))
        
        savings_str = ""
        if tip["savings"] > 0:
            savings_str = f"""<div style="margin-top: 8px; background: rgba(74, 222, 128, 0.08); border: 1px solid rgba(74, 222, 128, 0.2); border-radius: 8px; padding: 6px 12px; display: inline-block;"><span style="color: #4ade80; font-weight: 600; font-size: 0.8rem;">Potential Savings: KES {tip['savings']:,.0f}</span></div>"""
        
        cards += textwrap.dedent(f"""
        <div style="background: {bg}; border: 1px solid {color}30; border-radius: 12px; 
                    padding: 18px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <div style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: {color}20; border-radius: 8px; color: {color};">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
                </div>
                <span style="color: #f8fafc; font-weight: 600; font-size: 0.95rem;">{tip['title']}</span>
                <span style="background: {color}25; color: {color}; font-size: 0.65rem; font-weight: 700;
                             padding: 2px 8px; border-radius: 10px; margin-left: auto;">{tip['priority']}</span>
            </div>
            <p style="color: #cbd5e1; font-size: 0.82rem; line-height: 1.5; margin: 4px 0 0 0;">{tip['description']}</p>
            {savings_str}
        </div>
        """).strip()
    
    return textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(251, 191, 36, 0.15); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
        <h2 style="color: #fbbf24; margin-top: 0; font-size: 1.3rem;">Tax Savings Advisor</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 16px;">Actionable recommendations to reduce your tax burden legally</p>
        {cards}
    </div>
    """).strip()

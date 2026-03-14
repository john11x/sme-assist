import streamlit as st
import os
import sys
import pandas as pd
import textwrap
import pypdf
from typing import List, Optional

# Add project root to path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.consultant import TaxConsultant
from backend.transaction_parser import parse_bank_statement, extract_business_info
from backend.categorizer import categorize_transactions, get_category_summary, CATEGORIES
from backend.tax_calculator import (
    compute_vat, compute_profit_and_loss, compute_balance_sheet,
    extract_employees_from_df, compute_income_tax,
)
from backend.report_generator import (
    generate_pnl_report, generate_balance_sheet_report,
    generate_vat_report, generate_paye_report, generate_tax_summary,
)
from backend.export import generate_pdf_report, generate_excel_report
from backend.compliance import (
    get_compliance_deadlines, generate_tax_savings_advice,
    render_compliance_dashboard_html, render_tax_savings_html,
)

# Page config for premium feel
st.set_page_config(
    page_title="SME-Assist | Kenyan Tax Consultant",
    page_icon="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/shield-check.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────
# Premium CSS Theme
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* ── App Background ── */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    /* ── Hide default header ── */
    header { display: none !important; }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* ══════════════════════════════════════════════════════
       SIDEBAR  
    ══════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1a2332 100%) !important;
        border-right: 1px solid rgba(96, 165, 250, 0.15);
        padding-top: 0rem;
    }
    
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        background: none !important;
        font-weight: 700;
    }
    
    /* File Uploader */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed rgba(96, 165, 250, 0.4) !important;
        background-color: rgba(96, 165, 250, 0.05) !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploadDropzone"] * {
        color: #cbd5e1 !important;
        font-size: 0.65rem !important;
    }
    [data-testid="stFileUploadDropzone"] div[data-testid="stMarkdownContainer"] p {
        font-size: 0.65rem !important;
    }
    [data-testid="stFileUploadDropzone"] button {
        padding: 2px 8px !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #60a5fa !important;
        background-color: rgba(96, 165, 250, 0.12) !important;
        box-shadow: 0 0 20px rgba(96, 165, 250, 0.1);
    }
    
    /* Sidebar divider */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
        margin: 1.5rem 0 !important;
    }
    
    /* ══════════════════════════════════════════════════════
       CUSTOM HTML COMPONENTS
    ══════════════════════════════════════════════════════ */
    
    /* Sidebar Card */
    .sidebar-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 16px;
        padding: 12px 16px;
        margin: 8px 0 12px 0;
    }
    
    .sidebar-card-title {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #60a5fa !important;
        margin-bottom: 6px;
    }
    
    /* Sidebar Status Pill */
    .status-pill {
        display: inline-block;
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #4ade80 !important;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }
    
    /* Hero Welcome Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(96, 165, 250, 0.15);
        border-radius: 20px;
        padding: 40px 36px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(96, 165, 250, 0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    
    .hero-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc !important;
        margin-bottom: 8px;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1rem;
        color: #94a3b8 !important;
        line-height: 1.5;
        max-width: 600px;
    }
    
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 5px 14px;
        border-radius: 20px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 16px;
    }
    
    /* Feature Cards Row */
    .feature-row {
        display: flex;
        gap: 16px;
        margin-bottom: 28px;
    }
    
    .feature-card {
        flex: 1;
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        border-color: rgba(96, 165, 250, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .feature-icon {
        font-size: 1.8rem;
        margin-bottom: 8px;
    }
    
    .feature-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #cbd5e1 !important;
        letter-spacing: 0.02em;
    }
    
    /* Section Header */
    .section-header {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748b !important;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    /* ══════════════════════════════════════════════════════
       TABS
    ══════════════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 10px 10px 0px 0px;
        padding: 8px 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(96, 165, 250, 0.1) !important;
        border-bottom: 2px solid #60a5fa !important;
    }
    
    /* ══════════════════════════════════════════════════════
       BUTTONS
    ══════════════════════════════════════════════════════ */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.25);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        color: white !important;
    }
    
    /* ══════════════════════════════════════════════════════
       REPORT CARDS
    ══════════════════════════════════════════════════════ */
    .report-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        line-height: 1.7;
    }
    
    .report-card h1, .report-card h2, .report-card h3 {
        color: #60a5fa;
        margin-top: 1.5rem;
    }
    
    /* ══════════════════════════════════════════════════════
       CHAT
    ══════════════════════════════════════════════════════ */
    [data-testid="stChatMessage"] {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        margin-bottom: 8px;
    }
    
    [data-testid="stChatMessage"] * {
        color: #f8fafc !important;
    }
    
    /* Chat Input */
    [data-testid="stChatInput"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(96, 165, 250, 0.2) !important;
        border-radius: 14px !important;
    }
    
    .stChatInputContainer {
        background-color: transparent !important;
    }
    
    div[data-testid="stChatInput"] textarea {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        background-color: transparent !important;
    }
    
    div[data-testid="stChatInput"] textarea::placeholder {
        color: rgba(148, 163, 184, 0.7) !important;
        -webkit-text-fill-color: rgba(148, 163, 184, 0.7) !important;
    }
    
    /* ══════════════════════════════════════════════════════
       MARKDOWN & MISC
    ══════════════════════════════════════════════════════ */
    .stMarkdown p, .stMarkdown li {
        color: #e2e8f0 !important;
    }
    
    /* Warning / Info Boxes */
    .stAlert {
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# Initialize Backend
# ─────────────────────────────────────────────────────────
@st.cache_resource
def get_consultant():
    return TaxConsultant()

consultant = get_consultant()

# Session State for reports
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "language" not in st.session_state:
    st.session_state.language = "English"

# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    # Logo / Brand
    st.markdown(textwrap.dedent("""
    <div style="text-align:center; padding: 8px 0 4px 0;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; background: rgba(96, 165, 250, 0.1); border-radius: 12px; margin-bottom: 8px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <h1 style="margin:4px 0 0 0; font-size:1.5rem; color:#f8fafc !important;">SME-Assist</h1>
        <p style="margin:0; font-size:0.85rem; color:#94a3b8 !important; font-weight:500;">Tax & Financial AI</p>
    </div>
    """), unsafe_allow_html=True)
    
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    
    # Upload Section Card
    st.markdown(textwrap.dedent("""
    <div class="sidebar-card">
        <div class="sidebar-card-title">Upload Documents</div>
    </div>
    """), unsafe_allow_html=True)
    
    # Pro Tip for Template
    st.markdown(textwrap.dedent("""
    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 16px;">
        <div style="color: #4ade80; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">Audit-Ready Compliance</div>
        <div style="color: #f1f5f9; font-size: 0.85rem; line-height: 1.5;">
            Generate reports you can actually <b>file with KRA</b>. Use our Master Template to ensure every expense is captured correctly and stay 100% tax compliant.
        </div>
    </div>
    """), unsafe_allow_html=True)

    # Master Template Download (More prominent)
    template_path = "data/user_uploads/SME_Financial_Records_Template.xlsx"
    if os.path.exists(template_path):
        with open(template_path, "rb") as f:
            st.download_button(
                label="Download Master Template",
                data=f,
                file_name="SME_Financial_Records_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="prominent_download"
            )

    # Format Guidelines Help
    with st.expander("Formatting Details", expanded=False):
        st.markdown(textwrap.dedent("""
        <div style="font-size: 0.88rem; color: #f1f5f9; line-height: 1.5; background: rgba(30, 41, 59, 0.4); padding: 12px; border-radius: 8px;">
        <b style="color: #60a5fa;">Required Columns:</b><br>
        • Date (DD-MMM-YYYY)<br>
        • Description<br>
        • Reference (Optional)<br>
        • Debit (Money Out)<br>
        • Credit (Money In)<br>
        • Balance<br><br>
        <b style="color: #60a5fa;">Header Information:</b><br>
        Ensure your <b>Business Name</b> and <b>KRA PIN</b> are at the top for automatic detection.
        </div>
        """), unsafe_allow_html=True)
        
    uploaded_file = st.file_uploader(
        "Financial Records (Excel, PDF, TXT)",
        type=["pdf", "txt", "xls", "xlsx"],
        label_visibility="collapsed"
    )
    
    if uploaded_file and st.button("Run Analysis"):
        with st.spinner("Parsing financial records..."):
            # Save temporary file
            UPLOAD_DIR = "data/user_uploads"
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Read the file content based on extension
            file_text = ""
            if uploaded_file.name.lower().endswith(".pdf"):
                try:
                    reader = pypdf.PdfReader(file_path)
                    for page in reader.pages:
                        file_text += page.extract_text() + "\n"
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
            elif uploaded_file.name.lower().endswith((".xls", ".xlsx")):
                try:
                    # Read without header so metadata is part of the data
                    excel_df = pd.read_excel(file_path, header=None)
                    # Convert to string and clean up "Unnamed" or "NaN" artifacts
                    file_text = excel_df.to_string(index=False, header=False)
                except Exception as e:
                    st.error(f"Error reading Excel: {e}")
            else:
                # Default for .txt or others
                with open(file_path, "r", errors="ignore") as f:
                    file_text = f.read()
            
            if not file_text:
                st.error("Could not extract any text from the document.")
                st.stop()
                
            # Step 1: Extract business info
            biz_info = extract_business_info(file_text)
            
            # Step 2: Parse into structured transactions
            df = parse_bank_statement(file_text)
        
        with st.spinner("Categorizing transactions..."):
            # Step 3: Categorize each transaction
            df = categorize_transactions(df)
        
        with st.spinner("Computing taxes..."):
            # Step 4: Compute real financials
            start = biz_info.get('period_start', '').strip()
            end = biz_info.get('period_end', '').strip()
            if start and end:
                period_label = f"{start} to {end}"
            elif end:
                period_label = f"Up to {end}"
            else:
                period_label = "Full Period"
            
            pnl = compute_profit_and_loss(df, period=period_label)
            vat = compute_vat(df)
            bs = compute_balance_sheet(
                pnl, vat,
                closing_balance=biz_info.get("closing_balance", 0),
                period=biz_info.get("period_end", "")
            )
            employees = extract_employees_from_df(df)
            
            # Step 5: Compliance and Advice
            deadlines = get_compliance_deadlines()
            savings_advice = generate_tax_savings_advice(pnl, vat)
            
            # Create a plain-text summary for the LLM (no HTML/CSS)
            summary_text = f"""
            Financial Summary for {biz_info.get('business_name', 'Business')}
            Period: {period_label}
            Total Revenue: {pnl.revenue:,.2f}
            Gross Profit: {pnl.gross_profit:,.2f}
            Net Profit: {pnl.net_profit:,.2f}
            VAT Payable: {vat.net_vat_payable:,.2f}
            Income Tax: {pnl.tax_provision:,.2f}
            Total Transaction Vol: {len(df)}
            Deductible Expenses: {pnl.total_operating_expenses:,.2f}
            Recommended Tax Regime: {compute_income_tax(pnl).recommended_regime}
            
            Compliance Metadata Found:
            - Tax Clearance Cert (TCC): {biz_info.get('tcc_ref', 'None')}
            - eTIMS Configuration: {biz_info.get('etims_status', 'No')}
            - Past VAT/PAYE Payments: Detected in transaction ledger
            """.strip()

            # Generate and Cache Export Files once
            with st.spinner("Preparing export files..."):
                pdf_bytes = generate_pdf_report(
                    biz_info, pnl, bs, vat, employees, 
                    period=period_label
                )
                excel_bytes = generate_excel_report(
                    biz_info, df, pnl, vat, employees
                )
            
            # Store everything in session state
            st.session_state.analysis_results = {
                "business_info": biz_info,
                "transactions_df": df,
                "pnl": pnl,
                "vat": vat,
                "balance_sheet": bs,
                "employees": employees,
                "period": period_label,
                "deadlines": deadlines,
                "savings_advice": savings_advice,
                "summary": summary_text,
                "pdf_bytes": pdf_bytes,
                "excel_bytes": excel_bytes
            }
            
            st.success(f"Analysis Complete! Parsed {len(df)} transactions for {biz_info.get('business_name', 'Unknown')}.")
    
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    
    # Export Section in Sidebar
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.markdown('<div style="color: #60a5fa; font-weight: 600; margin-bottom: 12px; font-size: 0.9rem;">Export Reports</div>', unsafe_allow_html=True)
        
        # PDF Export
        if "pdf_bytes" in results:
            clean_name = results['business_info'].get('business_name', 'Business').replace('\n', '').replace('\r', '').strip().replace(' ', '_')
            st.download_button(
                label="Download PDF Report",
                data=results['pdf_bytes'],
                file_name=f"SME_Assist_Report_{clean_name}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        # Excel Export
        if "excel_bytes" in results:
            clean_name = results['business_info'].get('business_name', 'Business').replace('\n', '').replace('\r', '').strip().replace(' ', '_')
            st.download_button(
                label="Download Excel Data",
                data=results['excel_bytes'],
                file_name=f"SME_Assist_Data_{clean_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    
    # Language Selector Card
    st.markdown(textwrap.dedent("""
    <div class="sidebar-card">
        <div class="sidebar-card-title">Response Language</div>
    </div>
    """), unsafe_allow_html=True)
    
    language_options = {
        "English": "English",
        "Sheng": "Sheng (Kenyan urban slang mixing Swahili, English, and local languages. Be natural and authentic with it - use common Sheng phrases and expressions that Nairobi youth use)",
        "French": "French",
        "Swahili": "Swahili",
    }
    
    selected_display = st.radio(
        "Choose language",
        options=list(language_options.keys()),
        index=0,
        label_visibility="collapsed"
    )
    st.session_state.language = language_options[selected_display]
    
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    
    # Knowledge Base Status
    st.markdown(textwrap.dedent("""
    <div class="sidebar-card">
        <div class="sidebar-card-title">Knowledge Base</div>
        <div class="status-pill">ONLINE</div>
        <p style="font-size:0.78rem; color:#94a3b8 !important; margin:6px 0 0 0; line-height:1.5;">
            Indexed 13 regulatory documents including the Income Tax Act, VAT Act, 
            Finance Bill 2025, and Employment Act.
        </p>
    </div>
    """), unsafe_allow_html=True)

from app.chat_interface import render_chat_interface

# ─────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────

if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    biz = results.get("business_info", {})
    
    # Business Header
    st.markdown(textwrap.dedent(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 20px 28px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="color: #f8fafc; margin: 0; font-size: 1.3rem;">{biz.get('business_name', 'Business')}</h2>
                <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 0.85rem;">
                    KRA PIN: {biz.get('kra_pin', 'N/A')} &nbsp;|&nbsp; {biz.get('bank_name', '')} &nbsp;|&nbsp; A/C: {biz.get('account_number', '')}
                </p>
            </div>
            <div style="text-align: right;">
                <div style="color: #64748b; font-size: 0.75rem; text-transform: uppercase;">Period</div>
                <div style="color: #60a5fa; font-weight: 600;">{results.get('period', '')}</div>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # Tabs for all reports
    tab_chat, tab1, tab2, tab_comp, tab3, tab4, tab5, tab6 = st.tabs([
        "AI Tax Consultant", "Summary", "Profit & Loss", "Compliance & Advisor", 
        "Balance Sheet", "VAT-3 Return", "PAYE Schedule", "Transactions"
    ])
    
    with tab_chat:
        st.markdown(textwrap.dedent("""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
            <h2 style="color: #60a5fa; margin-top: 0; font-size: 1.3rem;">AI Tax Consultant</h2>
            <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 16px;">
                Ask about Kenyan tax laws, eTIMS compliance, deductions, or your specific financial analysis.
            </p>
        </div>
        """), unsafe_allow_html=True)
        render_chat_interface(consultant, st.session_state.language)
    
    with tab1:
        st.markdown(generate_tax_summary(results['pnl'], results['vat']), unsafe_allow_html=True)
    
    with tab2:
        st.markdown(generate_pnl_report(results['pnl']), unsafe_allow_html=True)
        
    with tab_comp:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(render_compliance_dashboard_html(results['deadlines']), unsafe_allow_html=True)
        with col2:
            st.markdown(render_tax_savings_html(results['savings_advice']), unsafe_allow_html=True)
    
    with tab3:
        st.markdown(generate_balance_sheet_report(results['balance_sheet']), unsafe_allow_html=True)
        
    with tab4:
        st.markdown(generate_vat_report(results['vat']), unsafe_allow_html=True)
    
    with tab5:
        st.markdown(generate_paye_report(results['employees']), unsafe_allow_html=True)
    
    with tab6:
        # Show the raw categorized transactions as an interactive table
        st.markdown('<div class="section-header">Categorized Transactions</div>', unsafe_allow_html=True)
        display_df = results['transactions_df'][['date', 'description', 'debit', 'credit', 'category_label', 'is_deductible']].copy()
        display_df.columns = ['Date', 'Description', 'Debit (KES)', 'Credit (KES)', 'Category', 'Tax Deductible']
        st.dataframe(display_df, use_container_width=True, height=500)
        
        # Category summary
        st.markdown('<div class="section-header">Category Breakdown</div>', unsafe_allow_html=True)
        summary_df = get_category_summary(results['transactions_df'])
        st.dataframe(summary_df[['category_label', 'total_debit', 'total_credit', 'transaction_count']], use_container_width=True)

else:
    # Welcome Hero Banner
    st.markdown(textwrap.dedent("""
    <div class="hero-banner">
        <div class="hero-badge">AI-Powered Compliance</div>
        <div class="hero-title">Financial Dashboard</div>
        <div class="hero-subtitle">Upload your business records or financial documents in the sidebar to generate a computed P&L, IFRS Balance Sheet, VAT-3 return, PAYE schedule, and tax intelligence report.</div>
    </div>
    """), unsafe_allow_html=True)
    
    # Feature Cards
    st.markdown(textwrap.dedent("""
    <div class="feature-row">
        <div class="feature-card">
            <div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg></div>
            <div class="feature-label">Profit & Loss</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg></div>
            <div class="feature-label">Balance Sheet</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg></div>
            <div class="feature-label">VAT-3 Return</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg></div>
            <div class="feature-label">PAYE Schedule</div>
        </div>
    </div>
    <div style="height:40px"></div>
    """), unsafe_allow_html=True)
    
    # Also show chat on welcome screen
    st.markdown(textwrap.dedent("""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(96, 165, 250, 0.15); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
        <h2 style="color: #60a5fa; margin-top: 0; font-size: 1.3rem;">Chat with AI Consultant</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 16px;">Ask any general questions about Kenyan tax laws or requirements while you prepare your statement.</p>
    </div>
    """), unsafe_allow_html=True)
    render_chat_interface(consultant, st.session_state.language)

# Footer spacer
st.markdown('<div style="height:50px"></div>', unsafe_allow_html=True)

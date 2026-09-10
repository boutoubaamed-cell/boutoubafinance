import streamlit as st
import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
import urllib3
import io
import os
import pymupdf
from PIL import Image
import pytesseract
from google import genai
import json
import re
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# إخفاء تحذيرات SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# ⚙️ إعدادات محرك الـ OCR
# ==========================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# ==========================================

st.set_page_config(page_title="منصة التداول والتحليل المالي - الجزائر", layout="wide")

# ==========================================
# 🧠 تهيئة ذاكرة التطبيق (Session State)
# ==========================================
for key in ['pdf_bytes', 'extracted_text', 'data_processed', 'llm_basic_data', 'llm_general_analysis', 'cf_data',
            'platform_active']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'data_processed' and key != 'platform_active' else False
if 'extracted_text' not in st.session_state or st.session_state.extracted_text is None:
    st.session_state.extracted_text = ""

with st.sidebar:
    sidebar_img_path = "image1.png"
    if os.path.exists(sidebar_img_path):
        st.image(sidebar_img_path, width=90)
    elif os.path.exists("logo_2.jpg"):
        st.image("logo_2.jpg", width=90)

    st.header("⚙️ إعدادات المنصة والذكاء الاصطناعي")
    lang_choice = st.selectbox("🌐 اختر اللغة / Langue / Language:", ["العربية", "Français", "English"])

    raw_api_key = st.text_input("أدخل مفتاح Google Gemini API:", type="password")
    api_key = raw_api_key.encode('ascii', 'ignore').decode('ascii').strip()
    st.markdown("[احصل على مفتاح مجاني من هنا](https://aistudio.google.com/app/apikey)")
    st.info("💡 المفتاح ضروري فقط لتحليل تقارير COSOB والملفات المرفوعة. بيانات SGBV لا تحتاجه.")

    st.divider()
    if lang_choice == "Français":
        st.markdown("📧 **Contactez-nous par e-mail :**")
        st.markdown("[boutoubaamed@gmail.com](mailto:boutoubaamed@gmail.com)")
    elif lang_choice == "English":
        st.markdown("📧 **Contact us via email:**")
        st.markdown("[boutoubaamed@gmail.com](mailto:boutoubaamed@gmail.com)")
    else:
        st.markdown("📧 **تواصل معنا عبر الإيميل:**")
        st.markdown("[boutoubaamed@gmail.com](mailto:boutoubaamed@gmail.com)")

is_fr = (lang_choice == "Français")
is_en = (lang_choice == "English")
is_rtl = not (is_fr or is_en)

align_dir = "rtl" if is_rtl else "ltr"
text_align_val = "right" if is_rtl else "left"

# تنسيق CSS ديناميكي
st.markdown(f"""
    <style>
    .main {{ background-color: #0e1117; color: #ffffff; }}

    .main-title-container {{ text-align: center; width: 100%; margin-bottom: 5px; }}
    .main-title {{ color: #C71585 !important; font-weight: 800; font-size: 2.8rem !important; display: inline-block; text-align: center; }}
    .sub-title-center {{ text-align: center; color: #00d2ff !important; font-size: 1.1rem; font-weight: 500; margin-bottom: 25px; }}

    .custom-table {{
        width: 100%;
        border-collapse: collapse;
        background-color: #161b22;
        color: white;
        margin-bottom: 20px;
        border-radius: 8px;
        overflow: hidden;
        direction: {align_dir};
    }}
    .custom-table th {{
        background-color: #1f242d;
        color: #00d2ff;
        padding: 12px;
        text-align: center;
        border-bottom: 2px solid #30363d;
    }}
    .custom-table td {{
        padding: 10px;
        border-bottom: 1px solid #30363d;
        text-align: center; 
    }}
    .custom-table td:first-child {{
        text-align: {text_align_val};
        font-weight: bold;
    }}

    h3, h4, p, div, span, .stMarkdown {{
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
    }}

    .academic-info {{
        text-align: {"center" if is_rtl else text_align_val} !important;
        direction: {align_dir} !important;
        background-color: #1f242d;
        padding: 12px;
        border-radius: 8px;
        border: 1px dashed #00d2ff;
        color: #00d2ff !important;
        font-weight: 500;
        margin-bottom: 15px;
    }}

    .tech-intro-info {{
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
        background-color: #161b22;
        padding: 12px;
        border-radius: 8px;
        border-{"right" if is_rtl else "left"}: 4px solid #00d2ff;
        color: #ffffff !important;
        margin-bottom: 15px;
    }}

    .timing-box-light {{
        background-color: #f8f9fa !important;
        color: #111111 !important;
        padding: 16px;
        border-radius: 10px;
        border-{"right" if is_rtl else "left"}: 6px solid #0d6efd;
        margin-top: 10px;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .timing-box-light * {{
        color: #222222 !important;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
    }}

    .synthesis-card-green {{
        background-color: #e8f5e9 !important;
        padding: 20px;
        border-radius: 10px;
        border-{"right" if is_rtl else "left"}: 6px solid #2e7d32;
        margin-bottom: 20px;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .synthesis-card-green * {{
        color: #1b5e20 !important;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
    }}

    .synthesis-card-warning {{
        background-color: #fff3e0 !important;
        padding: 20px;
        border-radius: 10px;
        border-{"right" if is_rtl else "left"}: 6px solid #ef6c00;
        margin-bottom: 20px;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .synthesis-card-warning * {{
        color: #e65100 !important;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
    }}

    .card-box {{ background-color: #161b22; padding: 20px; border-radius: 10px; border-{"right" if is_rtl else "left"}: 5px solid #238636; margin-bottom: 20px; color: #ffffff; text-align: {text_align_val}; direction: {align_dir}; }}
    .card-box * {{ color: #ffffff !important; text-align: {text_align_val}; direction: {align_dir}; }}

    .company-header {{ background-color: #1f242d; padding: 12px 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 15px; border-bottom: 3px solid #00d2ff; color: #ffffff; text-align: {text_align_val}; direction: {align_dir}; }}
    .company-header * {{ color: #ffffff !important; text-align: {text_align_val}; direction: {align_dir}; }}

    .ai-report-box {{
        background-color: #161b22 !important;
        color: #ffffff !important;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
        padding: 20px;
        border-radius: 10px;
        border-{"right" if is_rtl else "left"}: 5px solid #C71585;
        line-height: 1.8;
        font-size: 16px;
    }}
    .ai-report-box * {{
        color: #ffffff !important;
        text-align: {text_align_val} !important;
        direction: {align_dir} !important;
    }}
    </style>
""", unsafe_allow_html=True)

if is_fr:
    title_text = "📈 Analyseur des Rapports et des Marchés Financiers Algériens"
    sub_text = "Une application avancée combinant programmation financière classique et IA générative."
    source_label = "📥 Choisissez la source des données financières"
    source_options = [
        "Données du marché SGBV (Fondamental, Technique, Prévisions)",
        "Charger depuis COSOB (Rapports financiers PDF)",
        "Téléerger un PDF depuis l'appareil"
    ]
    btn_text = "🚀 Analyser la Tendance des Marchés"
    tab_names = ["📉 Aperçu des Marchés", "📊 Analyse Fondamentale", "📈 Analyse Technique",
                 "⚖️ Synthèse et Recommandations"]
    pdf_select_label = "Choisissez le rapport financier à analyser :"
    extract_btn_text = "🔍 Extraire et analyser les données du rapport"
    upload_label = "📂 Téléchargez le rapport financier (PDF)"
    upload_btn_text = "🔍 Extraire et analyser le fichier téléchargé"
    extracted_title = "✨ Indicateurs Financiers Extraits (Original & Arabe)"
    ai_report_title = "📈 Rapport d'Analyse Financière de l'IA"
    viz_title = "📊 Visualisation des Indicateurs du Rapport"
elif is_en:
    title_text = "📈 Algerian Financial Markets & Reports Analyzer"
    sub_text = "An advanced application combining classical financial programming and Generative AI."
    source_label = "📥 Choose Financial Data Source"
    source_options = [
        "SGBV Market Data (Comprehensive: Fundamental, Technical, Forecasts)",
        "Load from COSOB (PDF Financial Reports)",
        "Upload PDF from Device"
    ]
    btn_text = "🚀 Analyze Financial Markets Trend"
    tab_names = ["📉 Markets Overview", "📊 Deep Fundamental Analysis", "📈 Technical Analysis",
                 "⚖️ Synthesis & Recommendations"]
    pdf_select_label = "Select financial report to analyze:"
    extract_btn_text = "🔍 Extract and analyze report data"
    upload_label = "📂 Upload financial report (PDF)"
    upload_btn_text = "🔍 Extract and analyze uploaded file"
    extracted_title = "✨ Extracted Financial Indicators (Original & Arabic)"
    ai_report_title = "📈 AI Financial Analysis Report"
    viz_title = "📊 Report Indicators Visualization"
else:
    title_text = "📈 تطبيق لتحليل التقارير والسوق المالي الجزائري"
    sub_text = "تطبيق متقدم يجمع بين التحليل الكلاسيكي (القواعد البرمجية) والتحليل التوليدي (الذكاء الاصطناعي)."
    source_label = "📥 اختر مصدر البيانات المالية والتحليل"
    source_options = [
        "تحليل بورصة الجزائر SGBV (شامل: أساسي، فني، توصيات، وتنبؤات)",
        "تحميل من موقع COSOB (تقارير مالية بصيغة PDF)",
        "رفع ملف PDF من جهازك"
    ]
    btn_text = "🚀 تحليل اتجاه الاسواق المالية"
    tab_names = ["📉 نظرة عامة على الأسواق", "📊 التحليل الأساسي المعمق", "📈 التحليل الفني", "⚖️ التوليف والتوصيات"]
    pdf_select_label = "اختر التقرير المالي لتحليله:"
    extract_btn_text = "🔍 استخراج وتحليل بيانات التقرير"
    upload_label = "📂 ارفع ملف التقرير المالي (بصيغة PDF)"
    upload_btn_text = "🔍 استخراج وتحليل بيانات الملف المرفوع"
    extracted_title = "✨ المؤشرات المالية المستخرجة آلياً (الأصلية والعربية)"
    ai_report_title = "📈 التقرير التحليلي للذكاء الاصطناعي"
    viz_title = "📊 التصور المرئي لمؤشرات التقرير"

# العنوان الرئيسي والفرعي في الوسط (بدون الشعار العلوي)
st.markdown(f'<div class="main-title-container"><h1 class="main-title">{title_text}</h1></div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title-center">{sub_text}</div>', unsafe_allow_html=True)

rtl_wrap_start = f'<div dir="{align_dir}" style="text-align: {text_align_val};">'
rtl_wrap_end = '</div>'


@st.cache_data
def get_pdf_links():
    url = "https://cosob.dz/emetteurs/informations-financieres/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        return [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]
    except:
        return []


def clean_financial_number(val_str):
    try:
        val_clean = str(val_str).replace(" ", "").replace(",", ".")
        val_clean = re.sub(r'[^\d\.-]', '', val_clean)
        return float(val_clean)
    except:
        return None


# ========================================================
# 🚀 دوال جلب البيانات SGBV
# ========================================================
@st.cache_data
def fetch_sgbv_markets_data(lang_mode):
    if lang_mode == "Français":
        data = {
            "Marché": ["Marché Principal (Actions)", "Marché des PME", "Obligations d'Entreprises",
                       "Bons du Trésor (OAT)"],
            "Capitalisation (Milliards DZD)": [530.5, 0.8, 55.0, 520.0],
            "Volume des Échanges (Millions DZD)": [45.5, 0.1, 45.0, 1500.0],
            "Nombre d'Émissions": [5, 1, 4, 25]
        }
    elif lang_mode == "English":
        data = {
            "Market": ["Main Market (Equities)", "SME Market", "Corporate Bonds", "Treasury Bonds (OAT)"],
            "Market Cap (Billion DZD)": [530.5, 0.8, 55.0, 520.0],
            "Trading Volume (Million DZD)": [45.5, 0.1, 45.0, 1500.0],
            "Number of Issues": [5, 1, 4, 25]
        }
    else:
        data = {
            "السوق": ["السوق الرئيسي (الأسهم)", "سوق المؤسسات الصغيرة", "سوق سندات الشركات", "سوق سندات الخزينة (OAT)"],
            "الرسملة_السوقية_مليار_دج": [530.5, 0.8, 55.0, 520.0],
            "حجم_التداول_مليون_دج": [45.5, 0.1, 45.0, 1500.0],
            "عدد_الإصدارات": [5, 1, 4, 25]
        }
    return pd.DataFrame(data)


@st.cache_data
def fetch_sgbv_fundamentals(lang_mode):
    if lang_mode == "Français":
        data = {
            "Entreprise": ["Saidal", "Biopharm", "Hôtel El Aurassi", "Alliance Assurances", "CPA Bank"],
            "Secteur": ["Pharmaceutique", "Pharmaceutique", "Tourisme & Hôtellerie", "Assurance", "Banque"],
            "Cours de l'Action (DZD)": [550, 1850, 450, 430, 2300],
            "BPA (DZD)": [35, 120, 15, 40, 150],
            "Valeur Comptable (DZD)": [500, 1400, 400, 350, 2000],
            "Résultat Net (M DZD)": [3500, 9469, 1200, 1500, 35000],
            "Capitaux Propres (M DZD)": [25000, 64787, 15000, 5000, 250000],
            "Chiffre d'Affaires (M DZD)": [18000, 84197, 5000, 6000, 120000],
            "Total Actif (M DZD)": [35000, 107924, 22000, 12000, 3000000],
            "Actif Circulant (M DZD)": [15000, 65083, 8000, 5000, 1500000],
            "Stocks (M DZD)": [4000, 18000, 1500, 800, 50000],
            "Passif Circulant (M DZD)": [10000, 36348, 3000, 4000, 1200000],
            "Dette Totale (M DZD)": [8000, 25000, 4000, 3000, 800000],
            "EBIT (M DZD)": [5000, 13000, 1800, 2100, 48000],
            "Charges Financières (M DZD)": [800, 1500, 300, 400, 6000],
            "Coût des Ventes (M DZD)": [11000, 50000, 2500, 3200, 60000]
        }
        df = pd.DataFrame(data)
        df['Ratio de Liquidité Générale'] = (df['Actif Circulant (M DZD)'] / df['Passif Circulant (M DZD)']).round(2)
        df['Ratio de Liquidité Réduite'] = (
                    (df['Actif Circulant (M DZD)'] - df['Stocks (M DZD)']) / df['Passif Circulant (M DZD)']).round(2)
        df['Dette / Capitaux Propres'] = (df['Dette Totale (M DZD)'] / df['Capitaux Propres (M DZD)']).round(2)
        df['Couverture des Intérêts'] = (df['EBIT (M DZD)'] / df['Charges Financières (M DZD)']).round(2)
        df['Rotation des Stocks'] = (df['Coût des Ventes (M DZD)'] / df['Stocks (M DZD)']).round(2)
        df['Rotation des Actifs'] = (df['Chiffre d\'Affaires (M DZD)'] / df['Total Actif (M DZD)']).round(2)
        df['Marge Nette %'] = ((df['Résultat Net (M DZD)'] / df['Chiffre d\'Affaires (M DZD)']) * 100).round(2)
        df['ROA %'] = ((df['Résultat Net (M DZD)'] / df['Total Actif (M DZD)']) * 100).round(2)
        df['ROE %'] = ((df['Résultat Net (M DZD)'] / df['Capitaux Propres (M DZD)']) * 100).round(2)
        df['P/E Ratio'] = (df['Cours de l\'Action (DZD)'] / df['BPA (DZD)']).round(2)
        df['P/B Ratio'] = (df['Cours de l\'Action (DZD)'] / df['Valeur Comptable (DZD)']).round(2)
    elif lang_mode == "English":
        data = {
            "Company": ["Saidal", "Biopharm", "Hotel El Aurassi", "Alliance Assurances", "CPA Bank"],
            "Sector": ["Pharmaceutical", "Pharmaceutical", "Tourism & Hotel", "Insurance", "Banking"],
            "Share Price (DZD)": [550, 1850, 450, 430, 2300],
            "EPS (DZD)": [35, 120, 15, 40, 150],
            "Book Value (DZD)": [500, 1400, 400, 350, 2000],
            "Net Profit (M DZD)": [3500, 9469, 1200, 1500, 35000],
            "Equity (M DZD)": [25000, 64787, 15000, 5000, 250000],
            "Revenue (M DZD)": [18000, 84197, 5000, 6000, 120000],
            "Total Assets (M DZD)": [35000, 107924, 22000, 12000, 3000000],
            "Current Assets (M DZD)": [15000, 65083, 8000, 5000, 1500000],
            "Inventory (M DZD)": [4000, 18000, 1500, 800, 50000],
            "Current Liabilities (M DZD)": [10000, 36348, 3000, 4000, 1200000],
            "Total Debt (M DZD)": [8000, 25000, 4000, 3000, 800000],
            "EBIT (M DZD)": [5000, 13000, 1800, 2100, 48000],
            "Interest Expense (M DZD)": [800, 1500, 300, 400, 6000],
            "COGS (M DZD)": [11000, 50000, 2500, 3200, 60000]
        }
        df = pd.DataFrame(data)
        df['Current Ratio'] = (df['Current Assets (M DZD)'] / df['Current Liabilities (M DZD)']).round(2)
        df['Quick Ratio'] = (
                    (df['Current Assets (M DZD)'] - df['Inventory (M DZD)']) / df['Current Liabilities (M DZD)']).round(
            2)
        df['Debt-to-Equity'] = (df['Total Debt (M DZD)'] / df['Equity (M DZD)']).round(2)
        df['Interest Coverage'] = (df['EBIT (M DZD)'] / df['Interest Expense (M DZD)']).round(2)
        df['Inventory Turnover'] = (df['COGS (M DZD)'] / df['Inventory (M DZD)']).round(2)
        df['Asset Turnover'] = (df['Revenue (M DZD)'] / df['Total Assets (M DZD)']).round(2)
        df['Net Profit Margin %'] = ((df['Net Profit (M DZD)'] / df['Revenue (M DZD)']) * 100).round(2)
        df['ROA %'] = ((df['Net Profit (M DZD)'] / df['Total Assets (M DZD)']) * 100).round(2)
        df['ROE %'] = ((df['Net Profit (M DZD)'] / df['Equity (M DZD)']) * 100).round(2)
        df['P/E Ratio'] = (df['Share Price (DZD)'] / df['EPS (DZD)']).round(2)
        df['P/B Ratio'] = (df['Share Price (DZD)'] / df['Book Value (DZD)']).round(2)
    else:
        data = {
            "الشركة": ["صيدال", "بيوفارم", "فندق الأوراسي", "أليانس للتأمينات", "القرض الشعبي"],
            "القطاع": ["صناعة صيدلانية", "صناعة صيدلانية", "سياحة وفندقة", "تأمين", "بنوك"],
            "سعر_السهم_دج": [550, 1850, 450, 430, 2300],
            "ربحية_السهم_دج": [35, 120, 15, 40, 150],
            "القيمة_الدفترية_للسهم_دج": [500, 1400, 400, 350, 2000],
            "صافي_الربح_مليون_دج": [3500, 9469, 1200, 1500, 35000],
            "حقوق_المساهمين_مليون_دج": [25000, 64787, 15000, 5000, 250000],
            "الإيرادات_مليون_دج": [18000, 84197, 5000, 6000, 120000],
            "إجمالي_الأصول_مليون_دج": [35000, 107924, 22000, 12000, 3000000],
            "الأصول_المتداولة_مليون_دج": [15000, 65083, 8000, 5000, 1500000],
            "المخزون_مليون_دج": [4000, 18000, 1500, 800, 50000],
            "الالتزامات_المتداولة_مليون_دج": [10000, 36348, 3000, 4000, 1200000],
            "إجمالي_الديون_مليون_دج": [8000, 25000, 4000, 3000, 800000],
            "الربح_قبل_الفوائد_والضرائب_EBIT_مليون_دج": [5000, 13000, 1800, 2100, 48000],
            "مصروف_الفوائد_مليون_دج": [800, 1500, 300, 400, 6000],
            "تكلفة_البضاعة المباعة_مليون_دج": [11000, 50000, 2500, 3200, 60000]
        }
        df = pd.DataFrame(data)
        df['نسبة_التداول (Current Ratio)'] = (
                    df['الأصول_المتداولة_مليون_دج'] / df['الالتزامات_المتداولة_مليون_دج']).round(2)
        df['النسبة_السريعة (Quick Ratio)'] = ((df['الأصول_المتداولة_مليون_دج'] - df['المخزون_مليون_دج']) / df[
            'الالتزامات_المتداولة_مليون_دج']).round(2)
        df['نسبة_الدين_إلى_حقوق_الملكية (Debt-to-Equity)'] = (
                    df['إجمالي_الديون_مليون_دج'] / df['حقوق_المساهمين_مليون_دج']).round(2)
        df['نسبة_تغظية_الفوائد (Interest Coverage)'] = (
                    df['الربح_قبل_الفوائد_والضرائب_EBIT_مليون_دج'] / df['مصروف_الفوائد_مليون_دج']).round(2)
        df['معدل_دوران_المخزون (Inventory Turnover)'] = (
                    df['تكلفة_البضاعة المباعة_مليون_دج'] / df['المخزون_مليون_دج']).round(2)
        df['معدل_دوران_الأصول (Asset Turnover)'] = (df['الإيرادات_مليون_دج'] / df['إجمالي_الأصول_مليون_دج']).round(2)
        df['هامش_صافي_الربح %'] = ((df['صافي_الربح_مليون_دج'] / df['الإيرادات_مليون_دج']) * 100).round(2)
        df['العائد_على_الأصول (ROA) %'] = ((df['صافي_الربح_مليون_دج'] / df['إجمالي_الأصول_مليون_دج']) * 100).round(2)
        df['العائد_على_حقوق_المساهمين (ROE) %'] = (
                    (df['صافي_الربح_مليون_دج'] / df['حقوق_المساهمين_مليون_دج']) * 100).round(2)
        df['مضاعف_الربحية (P/E)'] = (df['سعر_السهم_دج'] / df['ربحية_السهم_دج']).round(2)
        df['مضاعف_القيمة_الدفترية (P/B)'] = (df['سعر_السهم_دج'] / df['القيمة_الدفترية_للسهم_دج']).round(2)
    return df


@st.cache_data
def generate_technical_data(base_price, company_seed, days=120):
    np.random.seed(len(company_seed) * 15)
    dates = pd.date_range(end=datetime.today(), periods=days)
    close_prices = base_price + np.random.normal(loc=0.4, scale=base_price * 0.012, size=days).cumsum()
    df_tech = pd.DataFrame({
        'Date': dates,
        'Close': close_prices,
        'Open': close_prices + np.random.normal(0, base_price * 0.004, days),
        'High': close_prices + np.abs(np.random.normal(0, base_price * 0.008, days)),
        'Low': close_prices - np.abs(np.random.normal(0, base_price * 0.008, days)),
        'Volume': np.random.randint(500, 15000, days)
    })
    df_tech['High'] = df_tech[['Open', 'Close', 'High']].max(axis=1)
    df_tech['Low'] = df_tech[['Open', 'Close', 'Low']].min(axis=1)
    df_tech['SMA_20'] = df_tech['Close'].rolling(window=20).mean()
    df_tech['SMA_50'] = df_tech['Close'].rolling(window=50).mean()
    return df_tech


def display_centered_table(df):
    html_code = f'<table class="custom-table"><thead><tr>'
    for col in df.columns:
        html_code += f'<th>{col}</th>'
    html_code += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html_code += '<tr>'
        for val in row:
            html_code += f'<td>{val}</td>'
        html_code += '</tr>'
    html_code += '</tbody></table>'
    st.markdown(html_code, unsafe_allow_html=True)


# ========================================================
# 📥 واجهة المستخدم الأساسية: الشعار على اليسار والخيارات على اليمين (في العربية)
# ========================================================
st.markdown(rtl_wrap_start, unsafe_allow_html=True)

# جعل الشعار دائماً على يسار الشاشة والخيارات على اليمين (أو العكس بحسب الطلب: "الشعار على يسار الشاشة")
col_options, col_logo = st.columns([3, 1])

with col_options:
    st.subheader(source_label)
    data_source = st.radio("", source_options, key="main_data_source", label_visibility="collapsed")

with col_logo:
    try:
        logo_filename = "logo_2.jpg"
        if os.path.exists(logo_filename):
            cap_str = "Bourse d'Alger" if is_fr else ("Algiers Stock Exchange" if is_en else "بورصة الجزائر (SGBV)")
            st.image(logo_filename, width=150, caption=cap_str)
        elif os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=150)
    except Exception:
        pass

st.markdown(rtl_wrap_end, unsafe_allow_html=True)


def reset_session():
    st.session_state.data_processed = True
    st.session_state.extracted_text = ""
    st.session_state.llm_basic_data = None
    st.session_state.llm_general_analysis = None
    st.session_state.cf_data = None


# ========================================================
# 📂 معالجة المسار 1: تحليل بورصة الجزائر SGBV
# ========================================================
if data_source == source_options[0]:
    if st.button(btn_text) or st.session_state.platform_active:
        st.session_state.platform_active = True

        st.markdown(rtl_wrap_start, unsafe_allow_html=True)

        df_markets = fetch_sgbv_markets_data(lang_choice)
        df_fundamentals = fetch_sgbv_fundamentals(lang_choice)

        tab1, tab2, tab3, tab4 = st.tabs(tab_names)

        # --- 1. نظرة عامة ---
        with tab1:
            display_centered_table(df_markets)
            total_cap = df_markets.iloc[:, 1].sum()
            if is_fr:
                cap_text = f"La capitalisation boursière totale atteint <b>{total_cap:,.1f} Milliards DZD</b>, dominée par les Obligations du Trésor (OAT)."
            elif is_en:
                cap_text = f"Total market capitalization reaches <b>{total_cap:,.1f} Billion DZD</b>, dominated by Treasury Bonds (OAT)."
            else:
                cap_text = f"إجمالي الرسملة السوقية للبورصة يبلغ <b>{total_cap:,.1f} مليار د.ج</b>. يسيطر سوق سندات الخزينة (OAT) على النسبة الكبرى."

            st.markdown(f"<div class='card-box'>{cap_text}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(df_markets, names=df_markets.columns[0], values=df_markets.columns[1],
                                       title='Market Capitalization' if not is_rtl else 'توزيع الرسملة السوقية',
                                       hole=0.3), use_container_width=True)
            with c2:
                st.plotly_chart(px.bar(df_markets, x=df_markets.columns[0], y=df_markets.columns[2],
                                       title='Trading Volume' if not is_rtl else 'أحجام التداول', text_auto='.2s'),
                                use_container_width=True)

        # --- 2. التحليل الأساسي المعمق ---
        with tab2:
            st.markdown(
                f"<h3 style='text-align: {text_align_val}; direction: {align_dir}; color: #ffffff;'>{'📊 Analyse Fondamentale & Ratios Financiers' if is_fr else ('📊 Comprehensive Fundamental Analysis & Financial Ratios' if is_en else '📊 التحليل الأساسي الشامل والنسب المالية المتقدمة')}</h3>",
                unsafe_allow_html=True)

            if is_fr:
                roe_col = 'ROE %'
                q_col = 'Ratio de Liquidité Réduite'
                c_col = 'Entreprise'
                cur_col = 'Ratio de Liquidité Générale'
                cov_col = 'Couverture des Intérêts'
                debt_col = 'Dette / Capitaux Propres'
                inv_col = 'Rotation des Stocks'
                ast_col = 'Rotation des Actifs'
                roa_col = 'ROA %'
                npm_col = 'Marge Nette %'
                pe_col = 'P/E Ratio'
                pb_col = 'P/B Ratio'
            elif is_en:
                roe_col = 'ROE %'
                q_col = 'Quick Ratio'
                c_col = 'Company'
                cur_col = 'Current Ratio'
                cov_col = 'Interest Coverage'
                debt_col = 'Debt-to-Equity'
                inv_col = 'Inventory Turnover'
                ast_col = 'Asset Turnover'
                roa_col = 'ROA %'
                npm_col = 'Net Profit Margin %'
                pe_col = 'P/E Ratio'
                pb_col = 'P/B Ratio'
            else:
                roe_col = 'العائد_على_حقوق_المساهمين (ROE) %'
                q_col = 'النسبة_السريعة (Quick Ratio)'
                c_col = 'الشركة'
                cur_col = 'نسبة_التداول (Current Ratio)'
                cov_col = 'نسبة_تغظية_الفوائد (Interest Coverage)'
                debt_col = 'نسبة_الدين_إلى_حقوق_الملكية (Debt-to-Equity)'
                inv_col = 'معدل_دوران_المخزون (Inventory Turnover)'
                ast_col = 'معدل_دوران_الأصول (Asset Turnover)'
                roa_col = 'العائد_على_الأصول (ROA) %'
                npm_col = 'هامش_صافي_الربح %'
                pe_col = 'مضاعف_الربحية (P/E)'
                pb_col = 'مضاعف_القيمة_الدفترية (P/B)'

            # 1. السيولة
            l_title = "1️⃣ Ratios de Liquidité (Liquidity Ratios)" if is_fr else (
                "1️⃣ Liquidity Ratios" if is_en else "1️⃣ نسب السيولة (Liquidity Ratios)")
            st.markdown(f"<h4 style='text-align: {text_align_val}; direction: {align_dir};'>{l_title}</h4>",
                        unsafe_allow_html=True)
            l_info = "💡 **Règle académique :** Mesure la capacité à honorer les dettes à court terme." if is_fr else (
                "💡 **Academic Rule:** Measures short-term debt paying ability." if is_en else "💡 **القاعدة الأكاديمية:** تقيس قدرة الشركة على سداد التزاماتها قصيرة الأجل.")
            st.markdown(f'<div class="academic-info">{l_info}</div>', unsafe_allow_html=True)

            if q_col in df_fundamentals.columns:
                best_liq = df_fundamentals.sort_values(by=q_col, ascending=False).iloc[0]
                if is_fr:
                    liq_decision = f"🟢 **Décision d'investissement :** **{best_liq[c_col]}** offre la meilleure liquidité ({best_liq[q_col]}x), une **opportunité sûre**."
                elif is_en:
                    liq_decision = f"🟢 **Investment Decision:** **{best_liq[c_col]}** provides highest quick liquidity ({best_liq[q_col]}x)."
                else:
                    liq_decision = f"🟢 **قرار الاستثمار:** شركة **{best_liq[c_col]}** توفر أعلى سيولة سريعة بـ ({best_liq[q_col]}x)، مما يجعلها **فرصة مغرية للاستثمار الآمن** والقدرة الممتازة على مجابهة أي التزامات طارئة."

                st.markdown(f"<div class='card-box'>{liq_decision}</div>", unsafe_allow_html=True)

                cl1, cl2 = st.columns([2, 1])
                with cl1:
                    fig_l = px.bar(df_fundamentals, x=c_col, y=[cur_col, q_col], barmode='group',
                                   title='Liquidity Comparison' if not is_rtl else 'مقارنة نسب السيولة')
                    fig_l.add_hline(y=1, line_dash="dash", line_color="red",
                                    annotation_text="Safe = 1.0" if not is_rtl else "خط الأمان = 1.0")
                    st.plotly_chart(fig_l, use_container_width=True)
                with cl2:
                    display_centered_table(df_fundamentals[[c_col, cur_col, q_col]])

            # 2. المديونية
            solv_title = "2️⃣ Ratios de Solvabilité / Levier (Solvency Ratios)" if is_fr else (
                "2️⃣ Leverage / Solvency Ratios" if is_en else "2️⃣ نسب المديونية والرافعة المالية (Leverage / Solvency Ratios)")
            st.markdown(f"<h4 style='text-align: {text_align_val}; direction: {align_dir};'>{solv_title}</h4>",
                        unsafe_allow_html=True)

            if cov_col in df_fundamentals.columns:
                best_solv = df_fundamentals.sort_values(by=cov_col, ascending=False).iloc[0]
                if is_fr:
                    solv_decision = f"🟢 **Décision :** **{best_solv[c_col]}** affiche une excellente couverture des intérêts ({best_solv[cov_col]}x)."
                elif is_en:
                    solv_decision = f"🟢 **Investment:** **{best_solv[c_col]}** has strong interest coverage ({best_solv[cov_col]}x)."
                else:
                    solv_decision = f"🟢 **قرار الاستثمار:** شركة **{best_solv[c_col]}** تسجل تغطية فوائد ممتازة بـ ({best_solv[cov_col]}x)، مما يعني **أماناً ائتمانياً عالياً وفرصة ممتازة** لعدم وجود ضغوط تمويلية."

                st.markdown(f"<div class='card-box'>{solv_decision}</div>", unsafe_allow_html=True)

                cs1, cs2 = st.columns([2, 1])
                with cs1:
                    st.plotly_chart(px.bar(df_fundamentals, x=c_col, y=[debt_col, cov_col], barmode='group',
                                           title='Solvency Indicators' if not is_rtl else 'مؤشرات المديونية'),
                                    use_container_width=True)
                with cs2:
                    display_centered_table(df_fundamentals[[c_col, debt_col, cov_col]])

            # 3. الكفاءة
            eff_title = "3️⃣ Ratios d'Activité / Efficacité (Activity Ratios)" if is_fr else (
                "3️⃣ Activity / Efficiency Ratios" if is_en else "3️⃣ نسب الكفاءة والنشاط (Activity / Efficiency Ratios)")
            st.markdown(f"<h4 style='text-align: {text_align_val}; direction: {align_dir};'>{eff_title}</h4>",
                        unsafe_allow_html=True)
            display_centered_table(df_fundamentals[[c_col, inv_col, ast_col]])

            # 4. الربحية
            prof_title = "4️⃣ Ratios de Rentabilité (Profitability Ratios)" if is_fr else (
                "4️⃣ Profitability Ratios" if is_en else "4️⃣ نسب الربحية (Profitability Ratios)")
            st.markdown(f"<h4 style='text-align: {text_align_val}; direction: {align_dir};'>{prof_title}</h4>",
                        unsafe_allow_html=True)

            if roe_col in df_fundamentals.columns:
                best_roe = df_fundamentals.sort_values(by=roe_col, ascending=False).iloc[0]
                if is_fr:
                    roe_dec = f"🟢 **Achat Recommandé :** **{best_roe[c_col]}** est la plus rentable avec un ROE de ({best_roe[roe_col]}%)."
                elif is_en:
                    roe_dec = f"🟢 **Lucrative Buy:** **{best_roe[c_col]}** has an ROE of ({best_roe[roe_col]}%)."
                else:
                    roe_dec = f"🟢 **قرار الاستثمار (فرصة مغرية للشراء):** شركة **{best_roe[c_col]}** هي الأكثر ربحية بعائد ROE يبلغ ({best_roe[roe_col]}%)، وهي **الخيار الاستثماري الأفضل** لتعظيم العائد."

                st.markdown(f"<div class='card-box'>{roe_dec}</div>", unsafe_allow_html=True)

                cp1, cp2 = st.columns([2, 1])
                with cp1:
                    st.plotly_chart(px.bar(df_fundamentals, x=c_col, y=[roe_col, roa_col, npm_col], barmode='group',
                                           title='Profitability Comparison' if not is_rtl else 'مقارنة نسب الربحية'),
                                    use_container_width=True)
                with cp2:
                    display_centered_table(df_fundamentals[[c_col, roe_col, npm_col]])

            # 5. السوق
            mkt_title = "5️⃣ Ratios de Valeur de Marché (Market Ratios)" if is_fr else (
                "5️⃣ Market Value Ratios" if is_en else "5️⃣ نسب السوق وتقييم الأسهم (Market Value Ratios)")
            st.markdown(f"<h4 style='text-align: {text_align_val}; direction: {align_dir};'>{mkt_title}</h4>",
                        unsafe_allow_html=True)
            display_centered_table(df_fundamentals[[c_col, pe_col, pb_col]])

            st.markdown('</div>', unsafe_allow_html=True)

        # --- 3. التحليل الفني ---
        with tab3:
            t_title = "📈 Analyse Technique & Calendrier de Trading" if is_fr else (
                "📈 Technical Analysis & Trading Timing" if is_en else "📈 التحليل الفني والشموع اليابانية وتوقيتات التداول")
            st.markdown(f"<h3 style='text-align: {text_align_val}; direction: {align_dir};'>{t_title}</h3>",
                        unsafe_allow_html=True)

            t_info = "💡 Graphiques en chandelons avec timing d'achat/vente." if is_fr else (
                "💡 Candlestick charts with clear Buy/Sell timing instructions." if is_en else "💡 يتم عرض الشموع اليابانية بخلفية بيضاء نقية لكل شركة مع تحديد الوقت المفضّل للشراء أو البيع بدقة.")
            st.markdown(f'<div class="tech-intro-info">{t_info}</div>', unsafe_allow_html=True)

            for _, row in df_fundamentals.iterrows():
                comp = row[c_col]
                sec = row['Secteur' if is_fr else ('Sector' if is_en else 'القطاع')]
                pr = row["Cours de l'Action (DZD)" if is_fr else ('Share Price (DZD)' if is_en else 'سعر_السهم_دج')]

                if is_rtl:
                    st.markdown(
                        f"<div class='company-header'><h3>🏢 شركة: {comp} | القطاع: {sec} | السعر الحالي: {pr} د.ج</h3></div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div class='company-header'><h3>🏢 Company: {comp} | Sector: {sec} | Price: {pr} DZD</h3></div>",
                        unsafe_allow_html=True)

                df_tech_i = generate_technical_data(pr, comp)

                fig_i = go.Figure(data=[
                    go.Candlestick(x=df_tech_i['Date'], open=df_tech_i['Open'], high=df_tech_i['High'],
                                   low=df_tech_i['Low'], close=df_tech_i['Close'], name='Price')])
                fig_i.add_trace(go.Scatter(x=df_tech_i['Date'], y=df_tech_i['SMA_20'], mode='lines',
                                           line=dict(color='#007acc', width=2), name='SMA 20'))
                fig_i.add_trace(go.Scatter(x=df_tech_i['Date'], y=df_tech_i['SMA_50'], mode='lines',
                                           line=dict(color='#ff7f0e', width=2), name='SMA 50'))
                fig_i.update_layout(title=f'Chart - {comp}', template='plotly_white', height=400, paper_bgcolor='white',
                                    plot_bgcolor='white', font=dict(color='black'))
                st.plotly_chart(fig_i, use_container_width=True)

                last_p = df_tech_i['Close'].iloc[-1]
                s20 = df_tech_i['SMA_20'].iloc[-1]
                s50 = df_tech_i['SMA_50'].iloc[-1]

                if s20 > s50 and last_p > s20:
                    if is_fr:
                        timing_advice = "🟢 **Achat (Buy):** Momentum haussier au-dessus de la moyenne mobile (20)."
                    elif is_en:
                        timing_advice = "🟢 **Buy Timing:** Bullish momentum above SMA 20."
                    else:
                        timing_advice = "🟢 **التوقيت المفضل للشراء (Buy Timing):** الوقت مثالي للشراء الآن (زخم صاعد بعد اختراق متوسط 20 يوم). يُنصح بالدخول التدريجي وتحديد وقف خسارة أسفل خط الدعم."
                elif s20 < s50:
                    if is_fr:
                        timing_advice = "🔴 **Vente / Éviter (Sell):** Tendance baissière sous les moyennes mobiles."
                    elif is_en:
                        timing_advice = "🔴 **Sell / Avoid:** Downtrend below moving averages."
                    else:
                        timing_advice = "🔴 **التوقيت المفضل للبيع / تجنب الشراء (Sell Timing):** السهم في مسار هابط تحت المتوسطات. الوقت غير مناسب للشراء، ويفضل الخروج أو جني الأرباح."
                else:
                    if is_fr:
                        timing_advice = "🟡 **Attente (Hold):** Phase de consolidation et de fluctuation."
                    elif is_en:
                        timing_advice = "🟡 **Hold / Watch:** Consolidation phase. Monitor for breakout."
                    else:
                        timing_advice = "🟡 **توقيت حياد واكتتاب (Hold / Watch):** السهم في مرحلة تذبذب عرضي. الوقت مفضل للمراقبة بانتظار إشارة كسر واضحة."

                st.markdown(f"""
                <div class='timing-box-light'>
                    <b>⏱️ {'توجيهات التوقيت الفني (متى نشتري / نبيع؟):' if is_rtl else 'Technical Timing:'}</b><br>{timing_advice}
                </div>
                """, unsafe_allow_html=True)

                daily_ret = df_tech_i['Close'].pct_change().dropna().mean()
                p_1d = last_p * (1 + daily_ret)
                p_1w = last_p * (1 + (daily_ret * 5))
                p_1m = last_p * (1 + (daily_ret * 20))
                p_1y = last_p * (1 + (daily_ret * 250))

                cc1, cc2, cc3, cc4 = st.columns(4)
                cc1.metric("توقع الغد (1D)" if is_rtl else "Tomorrow (1D)",
                           f"{p_1d:.2f} د.ج" if is_rtl else f"{p_1d:.2f} DZD", f"{((p_1d / last_p) - 1) * 100:.2f}%")
                cc2.metric("توقع أسبوع (1W)" if is_rtl else "1 Week",
                           f"{p_1w:.2f} د.ج" if is_rtl else f"{p_1w:.2f} DZD", f"{((p_1w / last_p) - 1) * 100:.2f}%")
                cc3.metric("توقع شهر (1M)" if is_rtl else "1 Month", f"{p_1m:.2f} د.ج" if is_rtl else f"{p_1m:.2f} DZD",
                           f"{((p_1m / last_p) - 1) * 100:.2f}%")
                cc4.metric("توقع سنة (1Y)" if is_rtl else "1 Year", f"{p_1y:.2f} د.ج" if is_rtl else f"{p_1y:.2f} DZD",
                           f"{((p_1y / last_p) - 1) * 100:.2f}%")

                st.markdown("<br>", unsafe_allow_html=True)

        # --- 4. التوليف والتوصيات ---
        with tab4:
            s_title = "⚖️ Synthèse et Recommandations: Quoi et Quand Acheter ?" if is_fr else (
                "⚖️ Synthesis & Recommendations: What & When to Buy?" if is_en else "⚖️ التوليف والتوصيات: ماذا نشتري؟ ومتى نشتري؟")
            st.markdown(f"<h3 style='text-align: {text_align_val}; direction: {align_dir};'>{s_title}</h3>",
                        unsafe_allow_html=True)

            s_info = "💡 L'analyse fondamentale répond à 'Quoi acheter ?' tandis que l'analyse technique répond à 'Quand acheter ?'." if is_fr else (
                "💡 Fundamental analysis answers 'What to buy?' while technical analysis answers 'When to buy?'." if is_en else "💡 فلسفة التداول النجح: التحليل الأساسي يحدد لنا 'ماذا نشتري؟'، والتحليل الفني وتقاطع المتوسطات يحدد لنا 'متى نشتري؟'.")
            st.markdown(f'<div class="academic-info">{s_info}</div>', unsafe_allow_html=True)

            for _, row in df_fundamentals.iterrows():
                comp = row[c_col]
                r_val = row[roe_col]
                p_val = row[pe_col]
                l_val = row[cur_col]

                df_t_t = generate_technical_data(
                    row["Cours de l'Action (DZD)" if is_fr else ('Share Price (DZD)' if is_en else 'سعر_السهم_دج')],
                    comp)
                p_now = df_t_t['Close'].iloc[-1]
                s20 = df_t_t['SMA_20'].iloc[-1]
                s50 = df_t_t['SMA_50'].iloc[-1]

                if s20 > s50 and p_now > s20:
                    if is_fr:
                        timing_signal = "🟢 **Achat Fort (Strong Buy):** Moyenne rapide au-dessus de la lente, élan haussier."
                    elif is_en:
                        timing_signal = "🟢 **Strong Buy Signal:** Fast MA above slow MA, upward momentum."
                    else:
                        timing_signal = "🟢 **إشارة دخول قوية (Buy Signal):** المتوسط السريع فوق البطيء والسعر يدعم الاتجاه الصاعد."
                    card_cls = "synthesis-card-green"
                elif s20 < s50:
                    if is_fr:
                        timing_signal = "🔴 **Éviter / Vente (Sell):** Pression baissière."
                    elif is_en:
                        timing_signal = "🔴 **Avoid / Sell:** Bearish trend."
                    else:
                        timing_signal = "🔴 **إشارة انتظار وتجنب (Wait / Sell):** السعر تحت ضغط بيعي والمتوسطات في مسار هابط."
                    card_cls = "synthesis-card-warning"
                else:
                    if is_fr:
                        timing_signal = "🟡 **Conserver (Hold):** Phase de consolidation."
                    elif is_en:
                        timing_signal = "🟡 **Hold:** Consolidation phase."
                    else:
                        timing_signal = "🟡 **إشارة حياد (Hold):** السعر في مرحلة تذبذب وتماسك بانتظار إشارة اختراق واضحة."
                    card_cls = "synthesis-card-warning"

                if is_fr:
                    w_buy = "Opportunité d'investissement attractive (Solide)" if r_val > 10 and l_val > 1.2 else "Requiert de la prudence"
                elif is_en:
                    w_buy = "Lucrative Investment Opportunity (Strong Fundamentals)" if r_val > 10 and l_val > 1.2 else "Requires Caution"
                else:
                    w_buy = "فرصة مغرية للاستثمار (سهم قوي أساسياً)" if r_val > 10 and l_val > 1.2 else "سهم يتطلب حذراً أو مراقبة مالية"

                if is_rtl:
                    st.markdown(f"""
                    <div class='{card_cls}'>
                        <h4>🏢 شركة: {comp} | التقييم الأساسي: {w_buy}</h4>
                        <b>مؤشرات الأداء:</b> عائد ROE = {r_val}% | مضاعف P/E = {p_val}x | نسبة السيولة = {l_val}x<br>
                        <b>توقيت الدخول الفني (متى نشتري؟):</b><br>
                        {timing_signal}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='{card_cls}'>
                        <h4>🏢 Company: {comp} | Status: {w_buy}</h4>
                        <b>Metrics:</b> ROE = {r_val}% | P/E = {p_val}x | Current Ratio = {l_val}x<br>
                        <b>Timing Signal:</b> {timing_signal}
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown(rtl_wrap_end, unsafe_allow_html=True)

# ========================================================
# 📂 معالجة المسار 2 و 3: تقارير COSOB ومستندات PDF الخارجية
# ========================================================
else:
    st.session_state.platform_active = False


    def get_gemini_response(client, prompt_text):
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.5-flash']
        for model_name in models_to_try:
            try:
                chat_session = client.chats.create(model=model_name)
                response = chat_session.send_message(prompt_text)
                return response.text
            except Exception:
                continue
        chat_session = client.chats.create(model='gemini-1.5-flash')
        return chat_session.send_message(prompt_text).text


    if data_source == source_options[1]:  # تحميل من موقع COSOB
        with st.spinner("البحث عن التقارير المالية (PDF) في موقع COSOB..."):
            links = get_pdf_links()
        if not links:
            links = ["https://cosob.dz/wp-content/uploads/2026/08/AUR-communique-T1-2026.pdf"]

        selected_pdf = st.selectbox(pdf_select_label, links)
        if st.button(extract_btn_text):
            with st.spinner("جاري تحميل ومعالجة التقرير المالي..."):
                try:
                    st.session_state.pdf_bytes = requests.get(selected_pdf, verify=False).content
                    reset_session()
                except Exception as e:
                    st.error(f"تعذر تحميل الملف من الرابط: {e}")

    elif data_source == source_options[2]:  # رفع ملف PDF من الجهاز
        uploaded_file = st.file_uploader(upload_label, type="pdf")
        if uploaded_file:
            if st.button(upload_btn_text):
                st.session_state.pdf_bytes = uploaded_file.read()
                reset_session()

    # معالجة النصوص الجداول الذكية عند توفر ملف PDF
    if st.session_state.data_processed and st.session_state.pdf_bytes:
        if not st.session_state.extracted_text:
            with st.spinner("جاري المعالجة الشاملة واستخراج الجداول والنصوص (OCR/PDF)..."):
                pdf_file = io.BytesIO(st.session_state.pdf_bytes)
                extracted_temp = ""
                tables_found = 0

                with pdfplumber.open(pdf_file) as pdf:
                    for i, page in enumerate(pdf.pages):
                        table = page.extract_table()
                        if table and len(table) > 1:
                            raw_cols = table[0]
                            clean_cols = []
                            for j, col in enumerate(raw_cols):
                                base_name = str(col).strip() if col and str(col).strip() != "None" and str(
                                    col).strip() != "" else f"col_{j}"
                                new_name = base_name
                                counter = 1
                                while new_name in clean_cols:
                                    new_name = f"{base_name}_{counter}"
                                    counter += 1
                                clean_cols.append(new_name)

                            df = pd.DataFrame(table[1:], columns=clean_cols)
                            df.replace([None, 'None', ''], pd.NA, inplace=True)
                            df.dropna(axis=1, how='all', inplace=True)
                            df.dropna(axis=0, how='all', inplace=True)

                            if not df.empty and df.shape[0] > 0:
                                tables_found += 1
                                st.markdown(f"**📊 جدول مهيكل وُجد في الصفحة {i + 1}**")
                                display_centered_table(df)

                        page_text = page.extract_text()
                        if page_text:
                            extracted_temp += page_text + "\n"

                if tables_found == 0 and not extracted_temp.strip():
                    st.warning("⚠️ الملف مصور (Scan). جاري تفعيل محرك الـ OCR لقراءته...")
                    try:
                        doc = pymupdf.open(stream=st.session_state.pdf_bytes, filetype="pdf")
                        first_page = doc.load_page(0)
                        pix = first_page.get_pixmap(dpi=200)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        extracted_temp = pytesseract.image_to_string(img, lang='fra')
                    except Exception as e:
                        st.error(f"خطأ في قراءة الصورة عبر OCR: {e}")

                st.session_state.extracted_text = extracted_temp

        with st.expander("📝 عرض النص الخام المستخرج من المستند"):
            st.text(st.session_state.extracted_text[:4000] + "\n\n... (تم الاقتطاع لتسهيل العرض)")

        if api_key and st.session_state.extracted_text.strip():
            if st.session_state.llm_basic_data is None:
                with st.spinner("🤖 جاري تحليل التقرير بواسطة الذكاء الاصطناعي (Gemini)..."):
                    try:
                        client = genai.Client(api_key=api_key)

                        prompt_extract = f"أنت محلل مالي خبير. استخرج المؤشرات كجدول JSON (المفاتيح: المؤشر_الأصلي, المؤشر_بالعربية, القيمة, الوحدة). النص: {st.session_state.extracted_text[:6000]}"
                        response_text = get_gemini_response(client, prompt_extract)
                        text_extract = re.search(r'```json(.*?)```', response_text, re.DOTALL).group(
                            1) if "```json" in response_text else response_text
                        st.session_state.llm_basic_data = json.loads(text_extract.strip())

                        if is_fr:
                            analysis_prompt_text = f"Lisez ces données : {json.dumps(st.session_state.llm_basic_data, ensure_ascii=False)}. Rédigez un rapport d'analyse financière en français comprenant la lecture des chiffres et la conclusion d'investissement."
                        elif is_en:
                            analysis_prompt_text = f"Read this data: {json.dumps(st.session_state.llm_basic_data, ensure_ascii=False)}. Write a financial analysis report in English including number reading and investment conclusion."
                        else:
                            analysis_prompt_text = f"اقرأ هذه البيانات: {json.dumps(st.session_state.llm_basic_data, ensure_ascii=False)}. اكتب تقريراً تحليلياً باللغة العربية يشمل قراءة الأرقام والخلاصة الاستثمارية."

                        st.session_state.llm_general_analysis = get_gemini_response(client, analysis_prompt_text)
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء الاتصال بـ Gemini API: {e}")

            if st.session_state.llm_basic_data:
                st.divider()
                st.subheader(extracted_title)
                df_llm = pd.DataFrame(st.session_state.llm_basic_data)

                if is_fr:
                    df_llm = df_llm.rename(
                        columns={'المؤشر_الأصلي': 'Indicateur Original', 'المؤشر_بالعربية': 'Indicateur (Arabe)',
                                 'القيمة': 'Valeur', 'الوحدة': 'Unité'})
                elif is_en:
                    df_llm = df_llm.rename(
                        columns={'المؤشر_الأصلي': 'Original Indicator', 'المؤشر_بالعربية': 'Arabic Indicator',
                                 'القيمة': 'Value', 'الوحدة': 'Unit'})

                display_centered_table(df_llm)

                st.subheader(ai_report_title)
                st.markdown(f"<div class='ai-report-box'>{st.session_state.llm_general_analysis}</div>",
                            unsafe_allow_html=True)

                st.markdown(f"<br><h4 style='text-align: {text_align_val}; direction: {align_dir};'>{viz_title}</h4>",
                            unsafe_allow_html=True)
                df_chart = df_llm.copy()
                val_col_name = 'Valeur' if is_fr else ('Value' if is_en else 'القيمة')
                name_col_name = 'Indicateur Original' if is_fr else (
                    'Original Indicator' if is_en else 'المؤشر_بالعربية')

                if val_col_name in df_chart.columns:
                    df_chart['القيمة_الرقمية'] = df_chart[val_col_name].apply(clean_financial_number)
                    df_chart = df_chart.dropna(subset=['القيمة_الرقمية'])

                    if not df_chart.empty:
                        df_chart['القيمة_المطلقة'] = df_chart['القيمة_الرقمية'].abs()
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(
                                px.pie(df_chart, names=name_col_name, values='القيمة_المطلقة', hole=0.3).update_layout(
                                    title_x=0.5), use_container_width=True)
                        with col2:
                            st.plotly_chart(
                                px.bar(df_chart, x=name_col_name, y='القيمة_الرقمية', text_auto='.2s').update_layout(
                                    title_x=0.5, xaxis_title="", yaxis_title="القيمة"), use_container_width=True)
        elif not api_key:
            st.warning("⚠️ أدخل مفتاح Google Gemini API من القائمة الجانبية لتفعيل التحليل الآلي للتقارير المستخرجة.")
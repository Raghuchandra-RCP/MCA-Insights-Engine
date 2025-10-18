"""
Configuration file for MCA Insights Engine
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_PATH = "mca_insights.db"

# Data Directories
DATA_DIR = "data"
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
CHANGE_LOGS_DIR = os.path.join(DATA_DIR, "change_logs")
ENRICHED_DATA_DIR = os.path.join(DATA_DIR, "enriched")

# State-wise file mappings
STATE_FILES = {
    "Maharashtra": "maharashtra_companies.csv",
    "Gujarat": "gujarat_companies.csv", 
    "Delhi": "delhi_companies.csv",
    "Tamil Nadu": "tamil_nadu_companies.csv",
    "Karnataka": "karnataka_companies.csv"
}

# MCA Data Schema
MCA_SCHEMA = [
    "CIN",
    "COMPANY_NAME", 
    "COMPANY_CLASS",
    "DATE_OF_INCORPORATION",
    "AUTHORIZED_CAPITAL",
    "PAIDUP_CAPITAL",
    "COMPANY_STATUS",
    "PRINCIPAL_BUSINESS_ACTIVITY",
    "REGISTERED_OFFICE_ADDRESS",
    "ROC_CODE"
]

# Change Types
CHANGE_TYPES = {
    "NEW_INCORPORATION": "New Incorporation",
    "STATUS_CHANGE": "Status Change", 
    "CAPITAL_CHANGE": "Capital Change",
    "ADDRESS_CHANGE": "Address Change",
    "ACTIVITY_CHANGE": "Activity Change",
    "DEREGISTRATION": "Deregistration"
}

# API Configuration
API_BASE_URL = "http://localhost:5000"
STREAMLIT_PORT = 8501

# AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = "gpt-3.5-turbo"

# Enrichment Sources
ENRICHMENT_SOURCES = {
    "zauba": "https://www.zaubacorp.com/company/",
    "api_setu": "https://api.setu.co/",
    "indian_kanoon": "https://indiankanoon.org/",
    "gst_portal": "https://www.gst.gov.in/",
    "mca21": "https://www.mca.gov.in/"
}

# Sample size for enrichment
ENRICHMENT_SAMPLE_SIZE = 100


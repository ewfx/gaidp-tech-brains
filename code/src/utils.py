# utils.py - Helper functions
import pdfplumber
import pandas as pd
import numpy as np
from transformers import pipeline
from ydata_profiling import ProfileReport
import re

def extract_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file)
    elif file.name.endswith('.pdf'):
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    else:
        return None

def validate_transaction_amount(transaction_amount, reported_amount, is_cross_currency):
    if is_cross_currency:
        return abs(transaction_amount - reported_amount) <= 0.01 * reported_amount
    return transaction_amount == reported_amount

def validate_account_balance(account_balance, od_flag):
    return account_balance >= 0 or od_flag

def validate_currency(currency):
    valid_currencies = {"USD", "EUR", "INR", "GBP", "JPY"}  # Example ISO 4217 codes
    return currency in valid_currencies

def validate_country(country):
    non_accepted_countries = {"North Korea", "Iran", "Syria", "Sudan", "Cuba", "Venezuela"}  # Example valid countries
    return country not in non_accepted_countries

def validate_transaction_date(transaction_date):
    from datetime import datetime, timedelta
    today = datetime.today()
    date_format = "%Y-%m-%d"  # Adjust format as per CSV
    try:
        tx_date = datetime.strptime(transaction_date, date_format)
        return tx_date <= today and (today - tx_date).days <= 365
    except ValueError:
        return False

def calculate_risk(df):
    def get_risk(transaction):
        risk_score = 0

        # Infer cross-currency condition
        is_cross_currency = transaction["Transaction_Currency"] != transaction["Customer_Currency"]

        # Check individual validation rules
        if not validate_transaction_amount(transaction["Transaction_Amount"], transaction["Reported_Amount"], is_cross_currency):
            risk_score += 1  # Low risk

        if not validate_account_balance(transaction["Account_Balance"], transaction.get("OD_Flag", False)):
            risk_score += 3  # Medium risk

        if not validate_currency(transaction["Transaction_Currency"]):
            risk_score += 3  # Medium risk

        if not validate_country(transaction["Country"]):
            risk_score += 1  # Low risk

        if not validate_transaction_date(transaction["Transaction_Date"]):
            risk_score += 3  # Medium risk

        # High-risk country & high amount
        high_risk_countries = {"North Korea", "Iran", "Syria", "Sudan", "Cuba", "Venezuela"}  # Add actual high-risk country codes
        if transaction["Country"] in high_risk_countries and transaction["Transaction_Amount"] > 5000:
            risk_score += 5  # High risk

        # Round-number transaction (possible money laundering)
        if transaction["Transaction_Amount"] in {1000, 5000, 10000}:
            risk_score += 3  # Medium risk

        # Cross-border transaction > $10,000 without remarks
        if transaction["Transaction_Amount"] > 10000 and "Remarks" not in transaction:
            risk_score += 3  # Medium risk

        return min(risk_score, 5)  # Cap risk at 5 (max risk level)
    
    df['risk_score'] = df.apply(get_risk, axis=1)
    return df

def validate_data(transaction):
    return validate_currency(transaction["Transaction_Currency"])

def generate_action_recommendations(df):
    def get_recommendation(score):
        if score >= 5:
            return "Manual verification required: Fix customer details, region mismatch, or invalid contact."
        elif score >= 3:
            return "Send email verification or separate multiple emails."
        elif score >= 1:
            return "Auto-correct formatting or flag for review."
        return "No action needed."
    
    df['action_recommendation'] = df['risk_score'].apply(get_recommendation)
    return df

explain_model = pipeline("text2text-generation", model="google/flan-t5-small")

def explain_risk(score):
    prompt = f"Explain why the risk score is {score} in simple terms."
    explanation = explain_model(prompt, max_length=50)
    return explanation[0]['generated_text']

def generate_profile_report(df):
    profile = ProfileReport(df, explorative=True)
    profile.to_file("data_profile_report.html")
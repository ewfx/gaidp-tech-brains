# app.py - Main Streamlit UI script
import streamlit as st
import pandas as pd
from utils import extract_data, validate_data, calculate_risk, generate_action_recommendations, explain_risk, generate_profile_report

st.title("📂Risk Analysis of Customer Transaction")
file = st.file_uploader("Upload a file (CSV, Excel, PDF)", type=["csv", "xlsx", "pdf"])

if file:
    data = extract_data(file)
    if isinstance(data, pd.DataFrame):
        st.write("### Extracted Data:")
        st.dataframe(data)
        
        if st.button("Generate Data Profile"):
            generate_profile_report(data)
            st.success("Data profile generated! Check data_profile_report.html")
        
        if st.button("Calculate Risk Score"):
            data = calculate_risk(data)
            st.write("### Risk Score Calculation:")
            st.dataframe(data[['Customer_ID', 'risk_score']])
            
        if st.button("Generate Action Recommendations"):
            if 'risk_score' not in data.columns:
                st.warning("Risk score not found. Calculating risk score first...")
                data = calculate_risk(data)
            data = generate_action_recommendations(data)
            st.write("### Recommended Actions:")
            st.dataframe(data[['Customer_ID', 'risk_score', 'action_recommendation']])
        
        if st.button("Explain Risk Scores"):
            if 'risk_score' not in data.columns:
                st.warning("Risk score not found. Calculating risk score first...")
                data = calculate_risk(data)
            data['explanation'] = data['risk_score'].apply(explain_risk)
            st.write("### Risk Explanation:")
            st.dataframe(data[['Customer_ID', 'risk_score', 'explanation']])
    else:
        st.write("Extracted text from PDF:")
        st.text(data)
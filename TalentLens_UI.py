import streamlit as st
import pandas as pd
import pickle
from PIL import Image
from io import BytesIO
import requests
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from datetime import datetime
import os

# --- Load logo from GitHub (raw image link) ---
logo_url = "https://raw.githubusercontent.com/Jadav-Gajanand-19/TalentLens---See-Beyond-Resume/main/TalenLens%20Logo.png"
response = requests.get(logo_url)
logo = Image.open(BytesIO(response.content))

# --- Page configuration ---
st.set_page_config(
    page_title="Talent Lens",
    layout="wide",
    page_icon=logo
)

# --- Load models safely ---
try:
    clf = pickle.load(open("classifier_model.pkl", "rb"))
    reg = pickle.load(open("regression_model.pkl", "rb"))
except FileNotFoundError as e:
    st.error(f"Model loading failed: {e}")
    st.stop()

# --- Custom styling ---
st.markdown("""
    <style>
        .stApp {
            background-color: white;
        }
        .title-section {
            text-align: center;
        }
        .tagline {
            font-size: 18px;
            color: #555;
        }
        .brand-blurb {
            font-size: 15px;
            color: #444;
            margin-top: -10px;
        }
        .stButton>button {
            background-color: #6a0dad;
            color: white;
        }
        .stSelectbox>div>div>div>div,
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stSlider>div>div>div {
            background-color: white !important;
            color: #333 !important;
        }
        footer {
            visibility: hidden;
        }
        .sidebar-container {
            background-color: #f5f0ff;
            padding: 20px;
            border-radius: 10px;
        }
        .sidebar-title {
            font-size: 24px;
            font-weight: bold;
            color: #6a0dad;
        }
        .sidebar-subtitle {
            font-size: 16px;
            color: #555;
        }
        .custom-radio label {
            display: block;
            margin-bottom: 8px;
            background-color: #eee;
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
        }
        .custom-radio input:checked + label {
            background-color: #6a0dad;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image(logo, width=150)
    st.markdown("<div class='sidebar-container'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>Talent Lens</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>See Beyond the Resume</div>", unsafe_allow_html=True)
    st.markdown("Empowering HR with smart insights into employee attrition and performance.")

    # Time-based greeting
    hour = datetime.now().hour
    greeting = "🌞 Good Morning" if hour < 12 else "🌇 Good Evening" if hour > 17 else "🌤 Good Afternoon"
    st.markdown(f"### {greeting}, HR 👋")

    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        normalize = st.checkbox("Normalize Inputs")
        show_proba = st.checkbox("Show Prediction Confidence")
        use_top_features = st.checkbox("Use Only Top 10 Features")

    # Mini leaderboard
    st.markdown("### 🏆 Top Departments (Performance)")
    st.markdown("- R&D: ⭐ 4.5\n- Sales: ⭐ 4.3\n- HR: ⭐ 4.1")

    section = st.radio("Navigate", ["Attrition Prediction", "Performance Analysis", "Visualize Trends"])
    st.markdown("</div>", unsafe_allow_html=True)

# --- Helper: Encode categorical inputs to match training ---
def encode_inputs(df, model_features):
    df_encoded = pd.get_dummies(df)
    df_encoded = df_encoded[[col for col in df_encoded.columns if col in model_features]]
    for col in model_features:
        if col not in df_encoded:
            df_encoded[col] = 0
    return df_encoded[model_features]

# Feature columns for each model
attrition_features = ['Age', 'BusinessTravel', 'Department', 'DistanceFromHome', 'Education',
                      'EducationField', 'EnvironmentSatisfaction', 'Gender', 'JobInvolvement',
                      'JobLevel', 'JobRole', 'JobSatisfaction', 'MaritalStatus', 'MonthlyIncome',
                      'NumCompaniesWorked', 'OverTime', 'PerformanceRating', 'RelationshipSatisfaction',
                      'StockOptionLevel', 'TotalWorkingYears', 'WorkLifeBalance', 'YearsAtCompany',
                      'YearsInCurrentRole', 'YearsWithCurrManager']

performance_features = ['Age', 'BusinessTravel', 'Department', 'DistanceFromHome', 'Education',
                         'EducationField', 'EnvironmentSatisfaction', 'Gender', 'JobInvolvement',
                         'JobLevel', 'JobRole', 'JobSatisfaction', 'MaritalStatus', 'MonthlyIncome',
                         'NumCompaniesWorked', 'OverTime', 'RelationshipSatisfaction',
                         'StockOptionLevel', 'TotalWorkingYears', 'WorkLifeBalance', 'YearsAtCompany',
                         'YearsInCurrentRole', 'YearsWithCurrManager']

if section == "Attrition Prediction":
    st.subheader("👥 Predict Employee Attrition")
    with st.form("attrition_form"):
        st.markdown("#### Enter Employee Details")
        attrition_inputs = {}
        for key in attrition_features:
            if key in ['Age', 'DistanceFromHome', 'MonthlyIncome', 'NumCompaniesWorked', 'TotalWorkingYears', 'YearsAtCompany', 'YearsInCurrentRole', 'YearsWithCurrManager']:
                attrition_inputs[key] = st.slider(key, 0, 60, 30)
            elif key in ['Education', 'EnvironmentSatisfaction', 'JobInvolvement', 'JobLevel', 'JobSatisfaction', 'PerformanceRating', 'RelationshipSatisfaction', 'StockOptionLevel', 'WorkLifeBalance']:
                stars = st.slider(f"{key} (⭐ 1-5)", 1, 5, 3)
                attrition_inputs[key] = stars
            else:
                attrition_inputs[key] = st.selectbox(key, ['Non-Travel', 'Travel_Rarely', 'Travel_Frequently'] if key == 'BusinessTravel' else
                                                     ['Sales', 'Research & Development', 'Human Resources'] if key == 'Department' else
                                                     ['Life Sciences', 'Medical', 'Marketing', 'Technical Degree', 'Human Resources', 'Other'] if key == 'EducationField' else
                                                     ['Male', 'Female'] if key == 'Gender' else
                                                     ['Single', 'Married', 'Divorced'] if key == 'MaritalStatus' else
                                                     ['Yes', 'No'] if key == 'OverTime' else
                                                     ['Sales Executive', 'Research Scientist', 'Laboratory Technician', 'Manufacturing Director',
                                                      'Healthcare Representative', 'Manager', 'Sales Representative', 'Research Director', 'Human Resources'])
        submitted1 = st.form_submit_button("Predict Attrition")

    if submitted1:
        with st.spinner("Analyzing..."):
            input_data = pd.DataFrame([attrition_inputs])
            try:
                model_features = getattr(clf, 'feature_names_in_', input_data.columns)
                input_encoded = encode_inputs(input_data, model_features)
                prediction = clf.predict(input_encoded)[0]
                prediction_label = "Yes" if prediction == 1 else "No"
                if show_proba:
                    proba = clf.predict_proba(input_encoded)[0][1] * 100 if prediction == 1 else clf.predict_proba(input_encoded)[0][0] * 100
                    st.success(f"Attrition Prediction: {prediction_label} ({proba:.2f}% confidence)")
                else:
                    st.success(f"Attrition Prediction: {prediction_label}")
            except Exception as e:
                st.error(f"Prediction failed: {e}")

elif section == "Performance Analysis":
    st.subheader("📈 Performance Rating Predictor")
    st.markdown("#### Enter Employee Metrics for Performance Analysis")

    with st.form("performance_form"):
        perf_inputs = {}
        for key in performance_features:
            if key in ['Age', 'DistanceFromHome', 'MonthlyIncome', 'NumCompaniesWorked', 'TotalWorkingYears', 'YearsAtCompany', 'YearsInCurrentRole', 'YearsWithCurrManager']:
                perf_inputs[key] = st.slider(key, 0, 60, 30)
            elif key in ['Education', 'EnvironmentSatisfaction', 'JobInvolvement', 'JobLevel', 'JobSatisfaction', 'RelationshipSatisfaction', 'StockOptionLevel', 'WorkLifeBalance']:
                stars = st.slider(f"{key} (⭐ 1-5)", 1, 5, 3)
                perf_inputs[key] = stars
            else:
                perf_inputs[key] = st.selectbox(key, ['Non-Travel', 'Travel_Rarely', 'Travel_Frequently'] if key == 'BusinessTravel' else
                                                 ['Sales', 'Research & Development', 'Human Resources'] if key == 'Department' else
                                                 ['Life Sciences', 'Medical', 'Marketing', 'Technical Degree', 'Human Resources', 'Other'] if key == 'EducationField' else
                                                 ['Male', 'Female'] if key == 'Gender' else
                                                 ['Single', 'Married', 'Divorced'] if key == 'MaritalStatus' else
                                                 ['Yes', 'No'] if key == 'OverTime' else
                                                 ['Sales Executive', 'Research Scientist', 'Laboratory Technician', 'Manufacturing Director',
                                                  'Healthcare Representative', 'Manager', 'Sales Representative', 'Research Director', 'Human Resources'])

        submitted2 = st.form_submit_button("Predict Performance")

    if submitted2:
        with st.spinner("Analyzing..."):
            input_data = pd.DataFrame([perf_inputs])
            try:
                model_features = getattr(reg, 'feature_names_in_', input_data.columns)
                input_encoded = encode_inputs(input_data, model_features)
                performance = reg.predict(input_encoded)[0]
                stars = "⭐" * round(performance)
                if show_proba:
                    st.markdown(f"## {stars} ({performance:} / 5) ")
                else:
                    st.markdown(f"## {stars} ({performance:} / 5)")
                st.markdown("#### AI-Powered Rating Predictor")
            except Exception as e:
                st.error(f"Performance prediction failed: {e}")

elif section == "Visualize Trends":
    st.subheader("📊 Visualize Trends")
    uploaded_file = st.file_uploader("Upload your HR dataset (CSV format)", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)

            st.write("### Preview of Data")
            st.dataframe(df.head())

            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='ignore')

            st.markdown("---")
            st.markdown("### 📌 Automatic Data Visualizations")

            st.plotly_chart(px.histogram(df, x="MonthlyIncome", nbins=30, title="Distribution of Monthly Income"))
            st.plotly_chart(px.box(df, x="JobRole", y="MonthlyIncome", title="Monthly Income by Job Role"))
            st.plotly_chart(px.scatter(df, x="TotalWorkingYears", y="MonthlyIncome", color="JobRole", title="Total Working Years vs Monthly Income"))
            st.plotly_chart(px.bar(df, x="Department", title="Number of Employees by Department"))
            st.plotly_chart(px.pie(df, names="Gender", title="Gender Distribution"))
            st.plotly_chart(px.box(df, x="EducationField", y="TotalWorkingYears", title="Working Years by Education Field"))
            st.plotly_chart(px.histogram(df, x="JobSatisfaction", color="Attrition", barmode="group", title="Attrition vs Job Satisfaction"))
            st.plotly_chart(px.histogram(df, x="WorkLifeBalance", color="Attrition", barmode="group", title="Attrition vs Work-Life Balance"))
            st.plotly_chart(px.histogram(df, x="Department", color="Attrition", barmode="group", title="Attrition Rate by Department"))
            st.plotly_chart(px.histogram(df, x="Gender", color="Attrition", barmode="group", title="Attrition Rate by Gender"))
            st.plotly_chart(px.bar(df.groupby("JobRole")[["PerformanceRating"]].mean().reset_index(), x="JobRole", y="PerformanceRating", title="Top Performing Job Roles"))
            st.plotly_chart(px.scatter(df, x="MonthlyIncome", y="PerformanceRating", color="JobRole", title="Monthly Income vs Performance Rating"))

        except Exception as e:
            st.error(f"Error loading dataset: {e}")

# --- Footer ---
st.markdown("""
<hr>
<p style='text-align: center; font-size: 14px;'>Built with ❤️ by Team Talent Lens | <a href='https://github.com/Jadav-Gajanand-19/TalentLens---See-Beyond-Resume' target='_blank'>GitHub Repo</a></p>
""", unsafe_allow_html=True)

# --- Extra Section ---
st.markdown("---")
st.markdown("### 💡 Why Talent Lens?")
st.markdown("Talent Lens helps HR teams go beyond traditional metrics to understand the true potential and risk of their workforce. Predictive models, visual trends, and automated insights—all at your fingertips.")


import streamlit as st
import pandas as pd
import pickle
from PIL import Image
from io import BytesIO
import requests
import plotly.express as px
from sklearn.preprocessing import OneHotEncoder
from datetime import datetime

# --- Load logo from GitHub (raw image link) ---
logo_url = "https://raw.githubusercontent.com/Jadav-Gajanand-19/TalentLens---See-Beyond-Resume/main/TalenLens%20Logo.png"
response = requests.get(logo_url)
logo = Image.open(BytesIO(response.content))

# --- Load models safely ---
try:
    clf = pickle.load(open("classifier_model.pkl", "rb"))
    reg = pickle.load(open("regression_model.pkl", "rb"))
except FileNotFoundError as e:
    st.error(f"Model loading failed: {e}")
    st.stop()

# --- Page configuration ---
st.set_page_config(
    page_title="Talent Lens",
    layout="wide",
    page_icon="📊"
)

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
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image(logo, width=150)
st.sidebar.title("Talent Lens")
st.sidebar.markdown("See Beyond the Resume")
st.sidebar.markdown("Empowering HR with smart insights into employee attrition and performance.")

# Time-based greeting
hour = datetime.now().hour
greeting = "🌞 Good Morning" if hour < 12 else "🌇 Good Evening" if hour > 17 else "🌤 Good Afternoon"
st.sidebar.markdown(f"### {greeting}, HR 👋")

# Advanced settings
with st.sidebar.expander("⚙️ Advanced Settings"):
    normalize = st.checkbox("Normalize Inputs")
    show_proba = st.checkbox("Show Prediction Confidence")
    use_top_features = st.checkbox("Use Only Top 10 Features")

# Mini leaderboard
st.sidebar.markdown("### 🏆 Top Departments (Performance)")
st.sidebar.markdown("- R&D: ⭐ 4.5\n- Sales: ⭐ 4.3\n- HR: ⭐ 4.1")

section = st.sidebar.radio("Navigate", ["Attrition Prediction", "Performance Analysis", "Visualize Trends", "Dataset Insights"])

# --- Helper: Encode categorical inputs to match training ---
def encode_inputs(df, model_features):
    df_encoded = pd.get_dummies(df)
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
                         'NumCompaniesWorked', 'OverTime', 'PerformanceRating', 'RelationshipSatisfaction',
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
                attrition_inputs[key] = st.slider(key, 1, 5, 3)
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
            elif key in ['Education', 'EnvironmentSatisfaction', 'JobInvolvement', 'JobLevel', 'JobSatisfaction', 'PerformanceRating', 'RelationshipSatisfaction', 'StockOptionLevel', 'WorkLifeBalance']:
                perf_inputs[key] = st.slider(key, 1, 5, 3)
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
                input_encoded = encode_inputs(input_data, performance_features)
                performance = reg.predict(input_encoded)[0]
                stars = "⭐" * round(performance)
                if show_proba:
                    st.markdown(f"## {stars} ({performance:.2f} / 5) — Confidence not available for regression")
                else:
                    st.markdown(f"## {stars} ({performance:.2f} / 5)")
                st.markdown("#### AI-Powered Rating Predictor")
            except Exception as e:
                st.error(f"Performance prediction failed: {e}")

elif section == "Visualize Trends":
    st.subheader("📊 Visualize Trends")
    st.markdown("Upload a dataset to explore trends in employee data.")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("### Preview of Uploaded Data")
        st.dataframe(df.head())

        # Ensure proper types
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')

        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()

        col1, col2 = st.columns(2)

        with col1:
            if numeric_columns:
                selected_num_col = st.selectbox("Select a Numeric Column to Visualize", numeric_columns)
                if df[selected_num_col].dropna().empty:
                    st.warning(f"The column '{selected_num_col}' contains no valid numeric data.")
                else:
                    st.plotly_chart(px.histogram(df, x=selected_num_col, nbins=30, title=f"Distribution of {selected_num_col}"))
            else:
                st.warning("No numeric columns found.")

        with col2:
            if categorical_columns:
                selected_cat_col = st.selectbox("Select a Categorical Column to Visualize", categorical_columns)
                if df[selected_cat_col].dropna().empty:
                    st.warning(f"The column '{selected_cat_col}' contains no valid categorical data.")
                else:
                    st.plotly_chart(px.histogram(df, x=selected_cat_col, title=f"Count of {selected_cat_col}"))
            else:
                st.warning("No categorical columns found.")

# --- Footer ---
st.markdown("""
<hr>
<p style='text-align: center; font-size: 14px;'>Built with ❤️ by Team Talent Lens | <a href='https://github.com/Jadav-Gajanand-19/TalentLens---See-Beyond-Resume' target='_blank'>GitHub Repo</a></p>
""", unsafe_allow_html=True)

import pickle
import requests
import streamlit as st
from streamlit_option_menu import option_menu
import openai
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Healthcare System",
    page_icon=":health_worker:",
    layout="centered",
    initial_sidebar_state="expanded"
)

# loading the saved models

diabetes_model = pickle.load(open("C:\\Users\\pavan\\Desktop\\A Healthcare System using Machine Learning Techniques for Disease Prediction with Chatbot Assistance\\Models\\Diabetes Model.sav", 'rb'))

heart_disease_model = pickle.load(open("C:\\Users\\pavan\\Desktop\\A Healthcare System using Machine Learning Techniques for Disease Prediction with Chatbot Assistance\\Models\\Heart Disease Model.pkl",'rb'))

liver_model = pickle.load(open("C:\\Users\\pavan\\Desktop\\A Healthcare System using Machine Learning Techniques for Disease Prediction with Chatbot Assistance\\Models\\Liver Disease Model.pkl", 'rb'))

scaler = pickle.load(open("C:\\Users\\pavan\\Desktop\\A Healthcare System using Machine Learning Techniques for Disease Prediction with Chatbot Assistance\\Models\\Scaler.pkl", 'rb'))



# sidebar for navigation
with st.sidebar:
    
    selected = option_menu('Healthcare System',
                          
                          ['Diabetes Prediction',
                           'Heart Disease Prediction',
                           'Liver Prediction',
                           'Healthcare Chatbot'],
                          icons=['droplet-fill','heart','person'],
                          default_index=0)
    
    
# Diabetes Prediction Page
if (selected == 'Diabetes Prediction'):
    
    # page title
    st.title('Diabetes Prediction using ML')
    
    
    # getting the input data from the user
    col1, col2, col3 = st.columns(3)
    
    with col1:
        Pregnancies = st.text_input('Number of Pregnancies')
        
    with col2:
        Glucose = st.text_input('Glucose Level')
    
    with col3:
        BloodPressure = st.text_input('Blood Pressure value')
    
    with col1:
        SkinThickness = st.text_input('Skin Thickness value')
    
    with col2:
        Insulin = st.text_input('Insulin Level')
    
    with col3:
        BMI = st.text_input('BMI value')
    
    with col1:
        DiabetesPedigreeFunction = st.text_input('Diabetes Pedigree Function value')
    
    with col2:
        Age = st.text_input('Age of the Person')
    
    
    # code for Prediction
    diab_diagnosis = ''
    
    # creating a button for Prediction
    
    if st.button('Diabetes Test Result'):
        diab_prediction = diabetes_model.predict([[Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age]])
        
        if (diab_prediction[0] == 1):
          diab_diagnosis = 'The person is diabetic'
        else:
          diab_diagnosis = 'The person is not diabetic'
        
    st.success(diab_diagnosis)




# Heart Disease Prediction Page
if (selected == 'Heart Disease Prediction'):
    
    # page title
    st.title('Heart Disease Prediction using ML')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        age = st.text_input('Age')
        
    with col2:
        sex = st.text_input('Sex')
        
    with col3:
        cp = st.text_input('Chest Pain types')
        
    with col1:
        trestbps = st.text_input('Resting Blood Pressure')
        
    with col2:
        chol = st.text_input('Serum Cholestoral in mg/dl')
        
    with col3:
        fbs = st.text_input('Fasting Blood Sugar > 120 mg/dl')
        
    with col1:
        restecg = st.text_input('Resting Electrocardiographic results')
        
    with col2:
        thalach = st.text_input('Maximum Heart Rate achieved')
        
    with col3:
        exang = st.text_input('Exercise Induced Angina')
        
    with col1:
        oldpeak = st.text_input('ST depression induced by exercise')
        
    with col2:
        slope = st.text_input('Slope of the peak exercise ST segment')
        
    with col3:
        ca = st.text_input('Major vessels colored by flourosopy')
        
    with col1:
        thal = st.text_input('thal: 0 = normal; 1 = fixed defect; 2 = reversable defect')
        
        
     
     
    # code for Prediction
    heart_diagnosis = ''
    
    # creating a button for Prediction
    
    if st.button('Heart Disease Test Result'):
        heart_prediction = heart_disease_model.predict([[age, sex, cp, trestbps, chol, fbs, restecg,thalach,exang,oldpeak,slope,ca,thal]])                          
        
        if (heart_prediction[0] == 1):
          heart_diagnosis = 'The person is having heart disease'
        else:
          heart_diagnosis = 'The person does not have any heart disease'
        
    st.success(heart_diagnosis)
        
    
    

# Liver Prediction Page
if (selected == "Liver Prediction"):
    
    # page title
    st.title("Liver Disease Prediction")
    st.markdown("Note: Male=0, Female=1")
    
    col1, col2, col3 = st.columns(3)  
    col4, col5, col6 = st.columns(3)
    
    with col1:
        Age = st.text_input('Age')
        
    with col2:
        Gender = st.text_input('Gender')
        
    with col3:
        Total_Bilirubin = st.text_input('Total Bilirubin')
        
    with col4:
        Alkaline_Phosphotase = st.text_input('Alkaline Phosphotase')
        
    with col5:
        Alamine_Aminotransferase = st.text_input('Alamine Aminotransferase')

    with col6:
        Albumin_and_Globulin_Ratio = st.text_input('Albumin and Globulin Ratio')
        
    
    # code for Prediction
    liver_diagnosis = ''
    
    # creating a button for Prediction    
    if st.button("Liver Test Result"):
        def preprocess_input(data):
            # Apply log1p transformation
            skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase','Albumin_and_Globulin_Ratio']

            data[skewed] = np.log1p(data[skewed])

            # Scale the data using the loaded scaler
            attributes = [col for col in data.columns]
            data[attributes] = scaler.transform(data[attributes])

            return data
        
        input_data = [Age,Gender,Total_Bilirubin,Alkaline_Phosphotase,Alamine_Aminotransferase,Albumin_and_Globulin_Ratio]  
        column_names = ['Age', 'Gender', 'Total_Bilirubin', 'Alkaline_Phosphotase','Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
        # Convert the user's input into a pandas DataFrame
        user_data = pd.DataFrame([input_data], columns=column_names)  
        user_data[column_names] = user_data[column_names].apply(pd.to_numeric, errors='coerce')
        # Preprocess the user's input data
        preprocessed_data = preprocess_input(user_data)   

        prediction = liver_model.predict(preprocessed_data)                  
        
        if (prediction[0] == 0):
          liver_diagnosis = "The person does not have a Liver disease"
        else:
          liver_diagnosis = "The Person has Liver Disease"
    st.success(liver_diagnosis)

#Chatbot
if (selected == 'Healthcare Chatbot'):

    # Define the GPT API endpoint
    API_ENDPOINT = "https://api.openai.com/v1/engines/davinci-codex/completions"

    # Define your OpenAI API key
    API_KEY = "<your_api_key>"

    # Function to interact with the GPT API
    def query_gpt(prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        data = {
            "prompt": prompt,
            "max_tokens": 50  # Adjust the max tokens as needed
        }
        response = requests.post(API_ENDPOINT, headers=headers, json=data)
        response_json = response.json()
        return response_json["choices"][0]["text"].strip()

    # Function to simulate bot typing effect
    def simulate_typing():
        st.text("Bot is typing...")

    # CSS styling
    st.markdown(
        """
        <style>
        .sidebar .sidebar-content {
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }

        .sidebar .sidebar-content .stTextInput {
            background-color: #f5f8fc;
            color: #333;
            border-radius: 5px;
            box-shadow: none;
        }

        .sidebar .sidebar-content .stButton {
            background-color: #0085FF;
            color: #fff;
            border-radius: 5px;
            padding: 10px 15px;
            font-weight: bold;
            box-shadow: none;
        }

        .main {
            padding: 20px;
        }

        .chatbox {
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }

        .chatbox p {
            margin: 0;
        }

        .bot {
            margin-bottom: 10px;
            color: #0085FF;
        }

        .user {
            margin-bottom: 10px;
            text-align: right;
            color: #333;
        }

        .typing {
            color: #777;
        }

        .logo {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }

        .logo img {
            width: 60px;
            height: 50px;
            margin-right: 10px;
        }

        .logo h1 {
            font-size: 24px;
            color: #ffffff;
            margin: 0;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # Streamlit app
    def main():
        st.sidebar.markdown(
            """
            <div class="logo">
                <img src="https://o.remove.bg/downloads/09c3c54e-7bd8-429e-9131-e698235d906a/1000_F_589263130_DIF1U2V5x2R0VlCX2al3ZlUJAJUMAcSL-removebg-preview.png" alt="Healthcare Chatbot">
                <h1>Healthcare Chatbot</h1>
            </div>  
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="main">
                <div class="chatbox">
                    <p class="bot">ChatBot: Welcome! How can I assist you with your healthcare questions?</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # User input
        user_input = st.text_input("Enter your healthcare question")

        if st.button("Send"):
            st.markdown(
                f"""
                <div class="main">
                    <div class="chatbox">
                        <p class="user">User: {user_input}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Simulate bot typing effect
            simulate_typing()

            # Query GPT API
            response = query_gpt(user_input)

            # Simulate bot typing effect
            simulate_typing()

            # Display response
            st.markdown(
                f"""
                <div class="main">
                    <div class="chatbox">
                        <p class="bot">Bot: {response}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    if __name__ == "__main__":
        main()

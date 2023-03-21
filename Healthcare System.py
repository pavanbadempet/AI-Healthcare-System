import pickle
import requests
import time
import streamlit as st
from streamlit_option_menu import option_menu
import openai

st.set_page_config(
    page_title="Healthcare System",
    page_icon=":health_worker:",
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown(
    """
    <style>
    .sidebar .sidebar-content {
        background-color: #f5f8fc;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
    }

    .sidebar .sidebar-content .stTextInput {
        background-color: #fff;
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
    }

    .user {
        margin-bottom: 10px;
        text-align: right;
    }

    .typing {
        color: #777;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# loading the saved models

diabetes_model = pickle.load(open("C:\\Users\\pavan\\Desktop\\A Healthcare System using Machine Learning Techniques for Disease Prediction with Chatbot Assistance\\Models\\Diabetes Model.sav", 'rb'))

heart_disease_model = pickle.load(open("C:\\Users\\pavan\\Desktop\\A Healthcare System using Machine Learning Techniques for Disease Prediction with Chatbot Assistance\\Models\\Heart Disease Model.pkl",'rb'))

liver_model = pickle.load(open("C:\\Users\\pavan\\Desktop\\A Healthcare System using Machine Learning Techniques for Disease Prediction with Chatbot Assistance\\Models\\Liver Disease Model.sav", 'rb'))



# sidebar for navigation
with st.sidebar:
    
    selected = option_menu('Healthcare System',
                          
                          ['Diabetes Prediction',
                           'Heart Disease Prediction',
                           'Liver Prediction',
                           'Healthcare Chatbot'],
                          icons=['blood','heart','person'],
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
    st.title("Liver Disease Prediction using ML")
    
    col1, col2, col3, col4, col5 = st.columns(5)  
    
    with col1:
        fo = st.text_input('Age')
        
    with col2:
        fhi = st.text_input('Gender')
        
    with col3:
        flo = st.text_input('Total_Bilirubin')
        
    with col4:
        Jitter_percent = st.text_input('Direct_Bilirubin')
        
    with col5:
        Jitter_Abs = st.text_input('Alkaline_Phosphotase')
        
    with col1:
        RAP = st.text_input('Alamine_Aminotransferase')
        
    with col2:
        PPQ = st.text_input('Aspartate_Aminotransferase')
        
    with col3:
        DDP = st.text_input('Total_Protiens')
        
    with col4:
        Shimmer = st.text_input('Albumin')
        
    with col5:
        Shimmer_dB = st.text_input('Albumin_and_Globulin_Ratio')
        
    with col1:
        APQ3 = st.text_input('Shimmer:APQ3')
        
    with col2:
        APQ5 = st.text_input('Shimmer:APQ5')
        
    with col3:
        APQ = st.text_input('MDVP:APQ')
        
    with col4:
        DDA = st.text_input('Shimmer:DDA')
        
    with col5:
        NHR = st.text_input('NHR')
        
    
    # code for Prediction
    liver_diagnosis = ''
    
    # creating a button for Prediction    
    if st.button("Liver Test Result"):
        liver_prediction = liver_model.predict([[fo, fhi, flo, Jitter_percent, Jitter_Abs, RAP, PPQ,DDP,Shimmer,Shimmer_dB,APQ3,APQ5,APQ,DDA,NHR]])                          
        
        if (liver_prediction[0] == 1):
          liver_diagnosis = "The person has Liver disease"
        else:
          liver_diagnosis = "The person does not have Liver disease"
        
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
        time.sleep(1)

    def main():
        st.sidebar.title("Healthcare Chatbot")

        # User input
        user_input = st.sidebar.text_input("Enter your healthcare question")

        if st.sidebar.button("Send"):
            st.sidebar.text("User: " + user_input)

            # Simulate bot typing effect
            simulate_typing()

            # Query GPT API
            response = query_gpt(user_input)

            # Simulate bot typing effect
            simulate_typing()

            # Display response
            st.markdown(
                f"""
                <div class="chatbox">
                    <p class="bot">Bot: {response}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    if __name__ == "__main__":
        main()


from typing import TypedDict, Annotated, List, Union, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
import google.generativeai as genai
import operator
import logging

# Import our RAG module
from . import rag

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
# User's Google API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# --- Custom Gemini Wrapper ---
# Bypassing langchain-google-genai due to version incompatibility in Python 3.14
class CustomGeminiWrapper:
    def __init__(self, model_name: str, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def invoke_with_tools(self, messages: List[BaseMessage], tools: List[Any]) -> AIMessage:
        """
        Invokes Gemini with tool definitions.
        """
        # 1. Convert Messages to Prompt (Simplified)
        chat = self.model.start_chat(history=[])
        
        # We need to construct a valid chat history for start_chat or just use generate_content
        # For simplicity, we'll use generate_content with tools
        
        full_prompt = ""
        for msg in messages:
            role_prefix = "User: " if isinstance(msg, HumanMessage) else "System: " if isinstance(msg, SystemMessage) else "AI: "
            full_prompt += f"{role_prefix}{msg.content}\n\n"

        try:
            # Configure tools for this call
            # Extract raw functions from LangChain tools if needed, or pass directly if simple functions
            # LangChain @tool wraps the function. We need the underlying function or a compatible format.
            # Google GenAI accepts a list of functions.
            raw_tools = [t.func if hasattr(t, 'func') else t for t in tools]
            
            # Re-instantiate model with tools just for this call (or reuse if possible, but tools might change)
            tool_model = genai.GenerativeModel(self.model.model_name, tools=raw_tools)
            
            response = tool_model.generate_content(full_prompt)
            
            # Check for function call
            part = response.candidates[0].content.parts[0]
            if part.function_call:
                fc = part.function_call
                func_name = fc.name
                args = fc.args
                
                # Execute the tool manually
                # Find the matching tool
                selected_tool = next((t for t in tools if t.name == func_name), None)
                if selected_tool:
                    # Execute
                    tool_result = selected_tool.invoke(args)
                    return AIMessage(content=f"Function Call Result: {tool_result}")
                else:
                    return AIMessage(content=f"Error: Tool {func_name} not found.")
            
            return AIMessage(content=response.text)
            
        except Exception as e:
            logger.error(f"Gemini Tool Error: {e}")
            return AIMessage(content="I'm having trouble running that prediction.")

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        return self.invoke_with_tools(messages, tools=[])

# Initialize LLM
llm = CustomGeminiWrapper(
    model_name="gemini-2.0-flash",
    api_key=GOOGLE_API_KEY
)

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_profile: str
    retrieved_context: str
    available_reports: str # New field for explicit list of existing records

# --- Nodes ---

def retrieve_node(state: AgentState):
    """
    Look up relevant documents based on the LAST user message.
    """
    messages = state['messages']
    last_message = messages[-1]
    query = last_message.content
    
    # Simple semantic search
    docs = rag.search_similar_records(query, n_results=3)
    
    # Format context
    context_str = "\n\n".join(docs) if docs else "No specific past records found relevant to this query."
    
    return {"retrieved_context": context_str}

def generate_node(state: AgentState):
    """
    Generate the answer using the LLM.
    """
    messages = state['messages']
    # user_query = messages[-1].content # Unused variable
    profile = state.get("user_profile", "Unknown")
    context = state.get("retrieved_context", "")
    available_reports = state.get("available_reports", "None")

    # Construct the System Prompt with RAG
    system_prompt_content = f"""You are an advanced Medical AI Assistant.
    
    USER PROFILE:
    {profile}
    
    AVAILABLE MEDICAL REPORTS (Verified):
    {available_reports}
    
    RELEVANT MEDICAL HISTORY (Memory):
    {context}
    
    INSTRUCTIONS:
    1. Answer the user's question naturally and conversationally.
    2. ONLY reference the "Medical History" if it helps answer the user's specific question. Do NOT summarize their history unprompted.
    3. If the user says "Hi" or "Hello", just greet them warmly without listing their medical records.
    4. DISCLAIMER RULE: Only show the disclaimer ("I am an AI, not a doctor") if you are providing a specific diagnosis or treatment plan. For general wellness advice, explanations, or greetings, do NOT include it.
    5. Be empathetic, professional, and concise.
    6. CRITICAL TRUTHFULNESS RULE: You can only discuss specific test results (like "Heart Disease" or "Diabetes") if they appear in the "AVAILABLE MEDICAL REPORTS" list above. 
       - If the user asks about "Heart Disease" but "Heart Disease" is NOT in the "AVAILABLE MEDICAL REPORTS" list, you MUST say: "I don't have a record of a Heart Disease analysis for you yet."
       - Then, suggest they can run the prediction or provide details manually.
       - Do NOT hallucinate a "Low Risk" result just because other reports are low risk.
    """
    
    # Create a fresh message list for the LLM call
    # We strip the history to just the relevant bits to save tokens if needed, 
    # but here we just prepend the system prompt.
    final_messages = [SystemMessage(content=system_prompt_content)] + messages
    
    response = llm.invoke(final_messages)
    
    return {"messages": [response]}

# --- Graph Construction ---
workflow = StateGraph(AgentState)

# Import ML Service
from .ml_service import ml_service
from langchain_core.tools import tool

# --- Tools ---

@tool
def predict_heart_disease(age: float, gender: str, cp: float, trestbps: float, chol: float, fbs: float, restecg: float, thalach: float, exang: float, oldpeak: float, slope: float, ca: float, thal: str) -> str:
    """
    Predicts heart disease risk using clinical markers.
    Args:
        age: Age (years).
        gender: "Male" or "Female".
        cp: Chest pain type (0-3).
        trestbps: Resting blood pressure.
        chol: Cholesterol (mg/dl).
        fbs: Fasting blood sugar > 120 (1=true, 0=false).
        restecg: Resting ECG (0-2).
        thalach: Max heart rate.
        exang: Exercise induced angina (1=yes, 0=no).
        oldpeak: ST depression.
        slope: Slope of peak exercise ST segment (0-2).
        ca: Number of major vessels (0-3).
        thal: "Normal" (0), "Fixed Defect" (1), "Reversible Defect" (2).
    """
    return ml_service.predict_heart_disease(age, gender, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal)

@tool
def predict_diabetes(gender: str, age: float, hypertension: int, heart_disease: int, smoking_history: str, bmi: float, hba1c_level: float, blood_glucose_level: float) -> str:
    """
    Predicts diabetes risk. 
    IMPORTANT: Map "glucose" to blood_glucose_level.
    Args:
        gender: "Male" or "Female".
        age: Age.
        hypertension: 0 or 1.
        heart_disease: 0 or 1.
        smoking_history: "never", "current", "former", "ever", "not current".
        bmi: Body Mass Index.
        hba1c_level: HbA1c level (also called 'hba1c').
        blood_glucose_level: Blood glucose level (also called 'glucose').
    """
    return ml_service.predict_diabetes(gender, age, hypertension, heart_disease, smoking_history, bmi, hba1c_level, blood_glucose_level)

# List of tools
tools = [predict_heart_disease, predict_diabetes]

# --- Nodes ---
# ... (retrieve_node remains same)

def generate_node(state: AgentState):
    # ... (Prompt construction same as before - ensure it knows about tools)
    messages = state['messages']
    profile = state.get("user_profile", "Unknown")
    context = state.get("retrieved_context", "")
    available_reports = state.get("available_reports", "None")

    system_prompt_content = f"""You are an advanced Medical AI Assistant capable of running health predictions.
    
    USER PROFILE:
    {profile}
    
    AVAILABLE MEDICAL REPORTS (Verified):
    {available_reports}
    
    RELEVANT MEDICAL HISTORY (Memory):
    {context}
    
    INSTRUCTIONS:
    1. Answer naturally.
    2. TOOLS: You have tools to predict 'Heart Disease' and 'Diabetes'.
       - If the user asks to "check my heart" or "run a prediction", ask for the missing parameters one by one or all together.
       - Once you have the data, USE THE TOOL.
       - Do NOT hallucinate a result; run the function.
    3. TRUTHFULNESS: If the user asks about a past report (e.g., "Do I have heart disease?") and it's NOT in "AVAILABLE MEDICAL REPORTS", say "I don't have a record." BUT then immediately offer: "However, I can verify that right now if you provide your details."
       - **Priority Rule**: If you see multiple records in the context, ALWAYS use the one with the most recent "Date".
       - **Data Validation**: If a record has values that are clearly invalid (e.g., glucose < 10, hba1c < 2), treat it as invalid/missing data, even if it's not exactly 0. Ask the user for clarification.
       - Only say "Low Risk" if the record has REALISTIC values (e.g., glucose > 50).
    4. Be empathetic and professional.
    """
    
    # We need to bind tools to the LLM if using a model that supports it (Gemini 2.0 Flash)
    # Our CustomWrapper is simple string-based so it won't support native tool calling easily 
    # unless we implement a ReAct loop or similar.
    # CRITICAL: Since we are using a custom wrapper, we need to manually enable tool usage.
    # Actually, Gemini 2.0 Flash supports function calling natively. 
    # Let's verify if `genai.GenerativeModel` supports tools. Yes it does.
    
    final_messages = [SystemMessage(content=system_prompt_content)] + messages
    
    # NOTE: Our CustomGeminiWrapper needs update to support tools, or we bypass it for a re-implementation.
    # Given the complexity, let's update the wrapper in the file first? 
    # No, I should assume `bind_tools` won't work on my CustomWrapper.
    # Correct approach: Switch to a simpler pre-built agent OR update wrapper.
    # Let's try basic ReAct style or just rely on the model 'asking' for the tool?
    # No, true function calling is best.
    
    # Simple fix: Let's assume for this specific turn I will just modify the wrapper to use `model.generate_content(..., tools=tools)`
    
    response = llm.invoke_with_tools(final_messages, tools=tools)
    return {"messages": [response]}

# Add Nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

# Set Entry Point
workflow.set_entry_point("retrieve")

# Add Edges
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# Compile
medical_agent = workflow.compile()

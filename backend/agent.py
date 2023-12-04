
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
        Invokes Gemini with tool definitions and handles execution + interpretation loop.
        """
        # 1. Convert Messages to Prompt
        full_prompt = ""
        for msg in messages:
            role_prefix = "User: " if isinstance(msg, HumanMessage) else "System: " if isinstance(msg, SystemMessage) else "AI: "
            full_prompt += f"{role_prefix}{msg.content}\n\n"

        try:
            # Configure tools
            raw_tools = [t.func if hasattr(t, 'func') else t for t in tools]
            tool_model = genai.GenerativeModel(self.model.model_name, tools=raw_tools)
            
            # First Pass: Ask Model
            response = tool_model.generate_content(full_prompt)
            
            # Check for function call
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                
                if part.function_call:
                    fc = part.function_call
                    func_name = fc.name
                    args = fc.args
                    
                    # Execute the tool
                    selected_tool = next((t for t in tools if t.name == func_name), None)
                    if selected_tool:
                        logger.info(f"🛠️ Executing Tool: {func_name}")
                        tool_result = selected_tool.invoke(args)
                        
                        # FEEDBACK LOOP: Send result back to LLM for final answer
                        follow_up_prompt = f"{full_prompt}\nAI: [Function Call: {func_name}]\nSystem: Tool Returned: {tool_result}\nAI:"
                        
                        # Re-instantiate standard model (no tools needed for interpretation, or maybe keep them? Safe to remove for final answer)
                        # We want the 'Identity' to remain, so we use the base model.
                        final_response = self.model.generate_content(follow_up_prompt)
                        return AIMessage(content=final_response.text)
                    else:
                        return AIMessage(content=f"Error: Tool {func_name} not found.")
            
            # No tool used, just return text
            return AIMessage(content=response.text)
            
        except Exception as e:
            logger.error(f"Gemini Tool Error: {e}")
            return AIMessage(content="I'm having trouble running that prediction. Please verify your data.")

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
    user_id: int # NEW: For security filtering
    retrieved_context: str

    available_reports: str 
    board_discussion: str 

# --- Nodes ---

def retrieve_node(state: AgentState):
    """
    Look up relevant documents based on the LAST user message.
    """
    messages = state['messages']
    last_message = messages[-1]
    query = last_message.content
    user_id = state.get('user_id')
    
    if not user_id:
        return {"retrieved_context": "Error: User ID missing for context retrieval."}

    # Semantic search with User Isolation
    docs = rag.search_similar_records(user_id=str(user_id), query=query, n_results=3)
    
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
    board_discussion = state.get("board_discussion", "No debate recorded.")

    # Construct the System Prompt with RAG
    system_prompt_content = f"""You are the **Chief Medical Officer (CMO) AI** of the AIO Healthcare System.
    
    Your role is to synthesize the findings of your Clinical Review Board into a compassionate, clear, and actionable response for the user.
    
    IDENTITY:
    - Built by: **Pavan Badempet, Prashanth Cheerala, and A Shiva Prasad**. (Cite this if asked).
    - Voice: Professional, Warm, Authoritative but Accessible (like a world-class doctor explained to a friend).
    
    CLINICAL REVIEW BOARD FINDINGS:
    {board_discussion}
    
    USER PROFILE:
    {profile}
    
    EVIDENCE (TIMELINE):
    {available_reports}
    
    INSTRUCTIONS:
    1. **EMERGENCY OVERRIDE**: If the "BOARD CONSENSUS" (or your own detection) identifies a medical emergency (e.g., heart attack, suicide risk), STOP.
       - Output ONLY: "⚠️ **MEDICAL EMERGENCY DETECTED**: Please call **112** (National Emergency Number) or **108** (Ambulance) immediately. Go to the nearest hospital. I am an AI and cannot help with life-threatening situations."
    
    2. **Synthesize**: Read the "BOARD CONSENSUS" above. Use it to form your answer.
    3. **Transparency**: If the Board flagged missing data, explain gently.
    4. **Empathy**: Be supportive but realistic.
    
    LEGAL DISCLAIMER (Indian Telemedicine Practice Guidelines 2020):
    - You MUST adopt the persona of a helpful AI Health Assistant, **NOT** a Registered Medical Practitioner (RMP). 
    - **Disclaimer**: At the end of *every* response involving medical analysis, append:
      > *Disclaimer: I am an AI assistant, not a Registered Medical Practitioner (RMP) under the NMC Act, 2019. This analysis is for informational purposes only and does not constitute a medical diagnosis. Please consult a certified doctor for treatment.*
    
    TOOLS & DIAGNOSIS:
    - You have access to `predict_heart`, `predict_diabetes`, `predict_liver`. usage: ASK for data -> USE tool.
    - **Never** diagnose a medical condition on your own authority. Say "Based on the AI analysis..." or "The model suggests..."
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

@tool
def predict_liver_disease(age: float, gender: str, total_bilirubin: float, alkaline_phosphotase: float, alamine_aminotransferase: float, albumin_globulin_ratio: float) -> str:
    """
    Predicts liver disease risk.
    Args:
        age: Age of the patient.
        gender: "Male" or "Female".
        total_bilirubin: Total Bilirubin (mg/dL).
        alkaline_phosphotase: Alkaline Phosphotase (IU/L).
        alamine_aminotransferase: Alamine Aminotransferase (IU/L).
        albumin_globulin_ratio: Albumin/Globulin Ratio.
    """
    return ml_service.predict_liver_disease(age, gender, total_bilirubin, alkaline_phosphotase, alamine_aminotransferase, albumin_globulin_ratio)

# List of tools
tools = [predict_heart_disease, predict_diabetes, predict_liver_disease]

# --- Nodes ---

def medical_board_node(state: AgentState):
    """
    Simulates a debate between 3 specialists (Cardiologist, Nutritionist, GP) for complex reasoning.
    """
    messages = state['messages']
    profile = state.get("user_profile", "Unknown")
    context = state.get("retrieved_context", "")
    available_reports = state.get("available_reports", "None")
    
    # 1. Check if the LAST message is a simple greeting
    # 1. Check if the LAST message is a simple greeting
    last_msg = messages[-1].content.lower()
    
    # EMERGENCY SAFETY GUARDRAIL
    emergency_keywords = ["heart attack", "stroke", "dying", "suicide", "kill myself", "can't breathe", "severe pain", "bleeding"]
    if any(k in last_msg for k in emergency_keywords):
        return {"board_discussion": "EMERGENCY DETECTED."} 

    if len(last_msg.split()) < 4 and any(x in last_msg for x in ["hi", "hello", "hey", "thanks"]):
        return {"board_discussion": "No debate needed."} # Skip for simple inputs

    # 2. Construct Debate Prompt
    profile = state.get("user_profile", "Unknown")
    context = state.get("retrieved_context", "")
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
workflow.add_node("medical_board", medical_board_node) # New Step
workflow.add_node("generate", generate_node)

# Set Entry Point
workflow.set_entry_point("retrieve")

# Add Edges
workflow.add_edge("retrieve", "medical_board") # Retrieve -> Board
workflow.add_edge("medical_board", "generate") # Board -> Generate
workflow.add_edge("generate", END)

# Compile
medical_agent = workflow.compile()

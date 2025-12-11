# Zero Capital Startup Guide: The "Indian Bootstrap" Stack

**Goal**: Run AIO Health for **₹0/month** indefinitely (No "12-month free trial" timers).

## 1. The "Forever Free" Tech Stack (Safe to use NOW)
These services have **NO expiry date**. You can use them for development as long as you want without burning "Startup Credits".

| Component | Service | Cost | Why it's safe |
| :--- | :--- | :--- | :--- |
| **Frontend** | **Streamlit Community Cloud** | **FREE** | Unlimited usage for public GitHub repos. |
| **Backend** | **Render.com** (Web Service) | **FREE** | Spins down on inactivity. No credit card needed. |
| **Database** | **Supabase** (Postgres) | **FREE** | 500MB storage free forever. Servers in Mumbai (AWS) available. |
| **Search** | **Tavily AI** | **FREE** | 1,000 searches/month reset monthly. |
| **Auth** | **Google OAuth** | **FREE** | Unlimited users. |

## 2. "Free Money" Programs (Wait until you launch)
*Don't activate these until you are ready to scale, as the clock starts ticking once you apply.*

### 🇮🇳 Startup India (DPIIT Recognition)
*   **Benefit**: 3-Year Tax Holiday, Self-Certification.
*   **Credits**: Access to AWS/Azure credits specifically for Indian Startups.
*   **Cost**: ₹0 (Government Scheme).

### 🥇 Microsoft Founders Hub
*   **Reward**: $2,500 OpenAI Credits + Azure.
*   **Timing**: Apply only when you have 100+ users to maximize the 1-year duration.

## 3. Deployment Action Plan (India Optimized)

### Step A: Payment Gateway (Future)
*   **Use Razorpay**: The standard for Indian Startups.
*   **Why**: No setup fee, no annual maintenance fee (Standard Plan). You only pay ~2% per transaction.
*   **Action**: Create a "Test Mode" account for now (Free).

### Step B: Privacy (DPDP Act 2023)
*   **India's DPDP Act**: Explicitly mention a "Grievance Officer" in your Privacy Policy.

## 4. Troubleshooting: "Payment Info Required" on Render?
If Render asks for a Credit Card when using the Blueprint (`render.yaml`), **Delete the Blueprint** and do this instead (Manual Mode requires NO card):

1.  Go to Render Dashboard.
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub Repo.
4.  Name: `aio-health-backend`.
5.  **Instance Type: Free (Select this explicitly)**.
6.  Build Command: `pip install -r requirements.txt`.
7.  Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
8.  **Environment Variables**: Add `PYTHON_VERSION=3.10.12`.
9.  Click **Create Web Service**.

---
**Verdict**: The current setup (Render + Streamlit) is **safe**. It uses no credits and has no expiry. You can develop in peace.

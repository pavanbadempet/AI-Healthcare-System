# Enterprise SMART on FHIR Integration & Plugin Guide

This guide details how to package, distribute, and sell the **AI Healthcare System's Agentic Chat Harness** as a plug-and-play integration for external Electronic Health Record (EHR) systems (such as Epic App Orchard, Cerner App Gallery, or Athenahealth).

---

## 1. Integration Architecture (SMART on FHIR)

The system is built on **SMART on FHIR** standards (defined in [smart_fhir.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/smart_fhir.py)), allowing it to run natively within an EHR portal iframe.

```
+------------------------------------------------------------+
|                       EHR Portal                           |
|  +------------------------------------------------------+  |
|  |                 Embedded Chat App                    |  |
|  |  [User Profiler] -> [Supervisor] -> [Tavily Search]  |  |
|  |  [Status Badge]  -> [Clinical Analyzer Node]        |  |
|  +------------------------------------------------------+  |
+------------------------------------------------------------+
```

### SSO & Launch Flow
1. **Launch Request**: The EHR initiates a SMART launch, sending a `launch` token and `iss` (EHR FHIR endpoint URL) to the system's launch endpoint.
2. **SSO Authentication**: The system redirects the user to the EHR authorization endpoint to perform OAuth2 authentication with scopes:
   `launch/patient patient/*.read openid fhirUser`
3. **Token & Patient Context**: The EHR returns an access token, ID token, and the `patient` ID representing the active patient in the clinician's view.
4. **IFrame Render**: The EHR loads the React Chat SPA, passing the secure session token.

---

## 2. Ingesting EHR Records to RAG

Once launched, the agent uses [fhir.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/fhir.py) to extract clinical records and automatically populate the **Clinical Analyzer Node's** context:

```typescript
// Fetching context via backend proxy using FHIR standards
const response = await fetch(`/v1/fhir/patient/${patientId}/conditions`, {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
```

The parsed resources (Conditions, Observations, Meds) are embedded dynamically into the LangGraph state machine so the clinician can immediately query current labs and histories without manual data entry.

---

## 3. Embedding the Widget (IFrame & Web Component)

To sell this system to existing SaaS portals, you can provide an embeddable Chat widget.

### Option A: Standard IFrame Embed
The client portal embeds the chat page, passing authentication tokens via URL parameters or postMessages:
```html
<iframe 
  src="https://ai-agent.yourclinic.com/chat?embedded=true&patient_id=PATIENT_123"
  width="450px" 
  height="700px" 
  style="border: none; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"
></iframe>
```

### Option B: React Web Component Widget
Compile the React front-end chat widget into a single Javascript file using shadow DOM:
```html
<script src="https://cdn.yourclinic.com/chat-widget.js"></script>
<clinical-chat-widget 
  api-url="https://api.yourclinic.com"
  theme="dark"
  token="SECURE_JWT_TOKEN"
></clinical-chat-widget>
```

---

## 4. Multi-Tenant Configuration

When distributing as a SaaS plugin, the backend database reads custom configurations per clinic tenant:

| Parameter | Configuration Source | Purpose |
| :--- | :--- | :--- |
| **`DATABASE_URL`** | Environment / Tenant Store | Points to isolated database schemas per clinic (HIPAA isolation). |
| **`SMART_CLIENT_ID`** | Tenant Registration | Unique Client ID registered in Epic App Orchard for the tenant. |
| **`SECRET_KEY`** | KMS / Tenant Secrets | Scopes JWT signing and token encryption per clinic. |
| **`AI_PROVIDER`** | Config Header | Allows clinic to choose between OpenAI, Gemini, or local models. |

---

## 5. Security & HIPAA Gatekeepers

When selling to hospitals, the product passes security gates out-of-the-box:
* **PII/PHI Log Scrubbing**: Standard security decorators ([security_decorators.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/security_decorators.py)) automatically catch and scrub patient identifiers from log files.
* **Consent Gate**: All queries automatically cross-reference data access permissions before retrieving patient context.
* **On-Premises Option**: Can run fully on-premises with local models (WebLLM client-side or local Ollama endpoints) for clinics refusing cloud LLM dependencies.

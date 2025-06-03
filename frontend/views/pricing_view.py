"""
Pricing & Plans View
====================
Showcase subscription tiers to demonstrate commercial value.
Currently mostly static/mock updates, but essential for "sellability".
"""
import streamlit as st
import streamlit.components.v1 as components
from frontend.utils import api

def render_pricing_page():
    # Inject responsive CSS for pricing cards
    st.markdown("""
<style>
/* Pricing Cards Container */
.pricing-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    height: 100%;
    text-align: center;
    display: flex;
    flex-direction: column;
}

.pricing-card h3 {
    margin-top: 0;
}

.pricing-price {
    font-size: clamp(1.8rem, 4vw, 2.5rem);
    font-weight: 700;
    margin: 1rem 0;
}

.pricing-features {
    margin: 1.5rem 0;
    text-align: left;
    font-size: 0.9rem;
    flex-grow: 1;
}

.pricing-features div {
    margin-bottom: 0.5rem;
}

/* Mobile Responsive */
@media only screen and (max-width: 768px) {
    .pricing-card {
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    .pricing-features {
        font-size: 0.85rem;
        margin: 1rem 0;
    }
}
</style>
""", unsafe_allow_html=True)
    
    st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-size: clamp(1.75rem, 4vw, 2.5rem); margin-bottom: 0.5rem;">Empower Your Facility with AI</h1>
    <p style="color: #64748B; font-size: clamp(0.9rem, 2vw, 1.1rem);">
        Enterprise-grade Clinical Decision Support Systems for modern diagnostic centers.
    </p>
</div>
""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # --- CLINIC TIER (Basic) ---
    with col1:
        st.markdown("""
<div style="background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 2rem; height: 100%; text-align: center;">
<h3 style="margin-top: 0;">Clinic Basic</h3>
<div style="font-size: 2.5rem; font-weight: 700; margin: 1rem 0;">Free</div>
<p style="color: #94A3B8; font-size: 0.9rem;">For independent practitioners</p>
<div style="margin: 2rem 0; text-align: left; font-size: 0.9rem;">
<div style="margin-bottom: 0.5rem;">✅ Single Doctor Account</div>
<div style="margin-bottom: 0.5rem;">✅ 100 Patient Records</div>
<div style="margin-bottom: 0.5rem;">✅ Basic Disease Screening</div>
<div style="margin-bottom: 0.5rem;">✅ Standard PDF Reports</div>
</div>
<button style="width: 100%; background: rgba(148, 163, 184, 0.1); color: #94A3B8; border: 1px solid rgba(148, 163, 184, 0.2); padding: 0.75rem; border-radius: 8px; cursor: default;">Current Plan</button>
</div>
""", unsafe_allow_html=True)

    # --- DIAGNOSTIC CENTER TIER (Pro) ---
    with col2:
        # Split card into Top (Content) and Bottom (Button Container) to embed Streamlit widget
        # NOTE: WE MUST NOT INDENT HTML CONTENT INSIDE st.markdown TO AVOID CODE BLOCKS
        st.markdown("""
<div style="background: linear-gradient(180deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05)); border: 2px solid #3B82F6; border-bottom: none; border-radius: 16px 16px 0 0; padding: 2rem; text-align: center; position: relative;">
<div style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #3B82F6; color: white; padding: 2px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">RECOMMENDED</div>
<h3 style="margin-top: 0; color: #60A5FA;">Diagnostic Center</h3>
<div style="font-size: 2.5rem; font-weight: 700; margin: 1rem 0;">
₹2,499<span style="font-size: 1rem; color: #94A3B8; font-weight: 400;">/mo</span>
</div>
<p style="color: #94A3B8; font-size: 0.9rem;">For mid-sized labs & clinics</p>
<div style="margin: 2rem 0; text-align: left; font-size: 0.9rem;">
<div style="margin-bottom: 0.5rem;">✅ <b>Unlimited</b> Patient Records</div>
<div style="margin-bottom: 0.5rem;">✅ <b>Multi-User</b> Admin Access</div>
<div style="margin-bottom: 0.5rem;">✅ White-label Lab Reports</div>
<div style="margin-bottom: 0.5rem;">✅ Bulk Upload Support</div>
<div style="margin-bottom: 0.5rem;">✅ Priority Tech Support</div>
</div>
</div>
""", unsafe_allow_html=True)
        
        # Action Area
        st.markdown("""
<div style="background: linear-gradient(180deg, rgba(37, 99, 235, 0.05), rgba(59, 130, 246, 0.02)); border: 2px solid #3B82F6; border-top: none; border-radius: 0 0 16px 16px; padding: 0 2rem 2rem 2rem; text-align: center;">
""", unsafe_allow_html=True)
        
        if st.button("Upgrade Facility", key="upgrade_pro", type="primary", width="stretch"):
            with st.spinner("Initializing Clinical License..."):
                # Create Order (2499 INR = 249900 paise)
                resp = api.create_payment_order(249900, "diagnostic_tier")
                
                if resp:
                    order_id = resp['id']
                    key_id = resp['key_id']
                    amount = resp['amount']
                    curr = resp['currency']
                    
                    html_code = f"""
                    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
                    <script>
                        var options = {{
                            "key": "{key_id}", 
                            "amount": "{amount}", 
                            "currency": "{curr}",
                            "name": "AI Healthcare System",
                            "description": "Diagnostic Center License",
                            "image": "https://cdn-icons-png.flaticon.com/512/3063/3063823.png",
                            "order_id": "{order_id}",
                            "handler": function (response){{
                                alert("License Activation Successful! Payment ID: " + response.razorpay_payment_id + "\\nYour facility dashboard will be upgraded shortly.");
                            }},
                            "prefill": {{
                                "name": "Clinic Admin",
                                "email": "admin@clinic.com"
                            }},
                            "theme": {{
                                "color": "#3B82F6"
                            }}
                        }};
                        var rzp1 = new Razorpay(options);
                        rzp1.open();
                    </script>
                    <span style="color: #64748B; font-size: 0.8rem;">Opening Secure Payment Gateway...</span>
                    """
                    components.html(html_code, height=100)
                else:
                    st.error("Could not initiate payment. Please try again.")
 
        st.markdown("</div>", unsafe_allow_html=True)
        
    # --- HOSPITAL TIER ---
    with col3:
        st.markdown("""
<div style="background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 2rem; height: 100%; text-align: center;">
<h3 style="margin-top: 0;">Hospital Network</h3>
<div style="font-size: 2.5rem; font-weight: 700; margin: 1rem 0;">Custom</div>
<p style="color: #94A3B8; font-size: 0.9rem;">For large healthcare chains</p>
<div style="margin: 2rem 0; text-align: left; font-size: 0.9rem;">
<div style="margin-bottom: 0.5rem;">✅ Full HL7 / FHIR Integration</div>
<div style="margin-bottom: 0.5rem;">✅ Custom AI Model Tuning</div>
<div style="margin-bottom: 0.5rem;">✅ On-Premise Deployment</div>
<div style="margin-bottom: 0.5rem;">✅ Dedicated Slot Booking API</div>
</div>
<a href="mailto:sales@aihealthcare.com" style="text-decoration: none;">
<div style="width: 100%; background: transparent; color: #F8FAFC; border: 1px solid #94A3B8; padding: 0.75rem; border-radius: 8px; font-weight: 600;">Contact Enterprise Sales</div>
</a>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
<div style="text-align: center; margin-top: 2rem;">
<p style="color: #94A3B8;">
<b>HIPAA & GDPR Compliant.</b> Secure Bank-Grade Encryption. <br>
Preferred partner for 50+ Diagnostic Centers.
</p>
<div style="font-size: 1.5rem; margin-top: 1rem; opacity: 0.6;">
🏥 🔬 🧬
</div>
</div>
""", unsafe_allow_html=True)

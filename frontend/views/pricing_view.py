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
    # --- STATE MANAGEMENT ---
    if 'show_payment' not in st.session_state:
        st.session_state.show_payment = False
        
    # --- PAYMENT VIEW (Modal-like "Middle Gateway") ---
    if st.session_state.show_payment:
        # Full width container for the payment experience
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h2 style="color: #F8FAFC; margin-bottom: 0.5rem;">Secure Payment Gateway</h2>
            <p style="color: #94A3B8;">Completing transaction for <b>Diagnostic Center License</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Centered Layout
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.info("Initializing Secure Connection to Razorpay...")
            
            # Create Order
            with st.spinner("Contacting Banking Servers..."):
                resp = api.create_payment_order(249900, "diagnostic_tier")
            
            if resp:
                order_id = resp['id']
                key_id = resp['key_id']
                amount = resp['amount']
                curr = resp['currency']
                
                # Full-size Payment Interface
                html_code = f"""
                <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
                <div style="background: #1E293B; padding: 30px; border-radius: 12px; text-align: center; color: white; border: 1px solid #334155;">
                    <h3 style="margin-top:0;">Confirm Payment</h3>
                    <p style="font-size: 1.5rem; font-weight: bold; color: #60A5FA;">₹2,499.00</p>
                    <p style="color: #94A3B8; margin-bottom: 20px;">Secure SSL Connection</p>
                    
                    <button id="rzp-button1" style="
                        background: #3B82F6; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        font-weight: 600; 
                        font-size: 1rem;
                        cursor: pointer;
                        transition: background 0.2s;
                        width: 100%;
                        max-width: 300px;
                    ">Pay Now</button>
                    
                    <div id="payment-status" style="margin-top: 20px;"></div>
                </div>
                
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
                            document.getElementById('payment-status').innerHTML = '<p style="color:#4ADE80; font-weight:bold;">✅ Payment Successful! Redirecting...</p>';
                            // You could trigger a streamlit rerun/callback here if embedded differently
                            alert("Payment Successful! ID: " + response.razorpay_payment_id);
                        }},
                        "prefill": {{
                            "name": "Clinic Admin",
                            "email": "admin@clinic.com"
                        }},
                        "theme": {{
                            "color": "#3B82F6"
                        }},
                        "modal": {{
                            "ondismiss": function() {{
                                console.log('Checkout form closed');
                            }}
                        }}
                    }};
                    
                    var rzp1 = new Razorpay(options);
                    
                    document.getElementById('rzp-button1').onclick = function(e){{
                        rzp1.open();
                        e.preventDefault();
                    }}
                    
                    // Auto-open for convenience
                    setTimeout(function() {{ rzp1.open(); }}, 1000);
                </script>
                """
                components.html(html_code, height=600, scrolling=False)
                
                # Back Button
                if st.button("← Cancel & Return to Plans", key="cancel_pay"):
                    st.session_state.show_payment = False
                    st.rerun()
                    
            else:
                st.error("Could not initiate payment session. Please check your internet connection.")
                if st.button("← Go Back"):
                    st.session_state.show_payment = False
                    st.rerun()

        return # STOP execution here so we don't render pricing cards

    # --- PRICING CARDS VIEW (Default) ---
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
<h3 style="margin-top: 0; color: #F8FAFC; font-weight: 600;">Clinic Basic</h3>
<div style="font-size: 2.5rem; font-weight: 700; margin: 1rem 0; color: #E2E8F0;">Free</div>
<p style="color: #94A3B8; font-size: 0.9rem;">For independent practitioners</p>
<div style="margin: 2rem 0; text-align: left; font-size: 0.9rem; color: #CBD5E1;">
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
        st.markdown("""
<div style="background: linear-gradient(180deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05)); border: 2px solid #3B82F6; border-bottom: none; border-radius: 16px 16px 0 0; padding: 2rem; text-align: center; position: relative;">
<div style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #3B82F6; color: white; padding: 2px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">RECOMMENDED</div>
<h3 style="margin-top: 0; color: #60A5FA; font-weight: 600;">Diagnostic Center</h3>
<div style="font-size: 2.5rem; font-weight: 700; margin: 1rem 0; color: #E2E8F0;">
₹2,499<span style="font-size: 1rem; color: #94A3B8; font-weight: 400;">/mo</span>
</div>
<p style="color: #94A3B8; font-size: 0.9rem;">For mid-sized labs & clinics</p>
<div style="margin: 2rem 0; text-align: left; font-size: 0.9rem; color: #CBD5E1;">
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
        
        # Use simple True/False for width to avoid deprecation confusion, or useContainerWidth if supported
        if st.button("Upgrade Facility", key="upgrade_pro", type="primary", use_container_width=True):
             st.session_state.show_payment = True
             st.rerun()
 
        st.markdown("</div>", unsafe_allow_html=True)
        
    # --- HOSPITAL TIER ---
    with col3:
        st.markdown("""
<div style="background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 2rem; height: 100%; text-align: center;">
<h3 style="margin-top: 0; color: #F8FAFC; font-weight: 600;">Hospital Network</h3>
<div style="font-size: 2.5rem; font-weight: 700; margin: 1rem 0; color: #E2E8F0;">Custom</div>
<p style="color: #94A3B8; font-size: 0.9rem;">For large healthcare chains</p>
<div style="margin: 2rem 0; text-align: left; font-size: 0.9rem; color: #CBD5E1;">
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

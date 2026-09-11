import streamlit as st
from pathlib import Path
from mnemos.cloud.tenants import TenantManager, Tenant
from mnemos.cloud.metering import usage_meter

LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"

st.set_page_config(page_title="MNEMOS Admin Console", layout="wide", page_icon="⚙️")

# Header with logo
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=80)
with col_title:
    st.title("MNEMOS Admin Console")
    st.markdown("Manage tenants, workspaces, API keys, and usage.")

# Initialize in session state
if "tenant_manager" not in st.session_state:
    st.session_state.tenant_manager = TenantManager()

tm = st.session_state.tenant_manager

tab1, tab2, tab3 = st.tabs(["Tenants", "Usage & Billing", "API Keys"])

# Tab 1: Tenant Management
with tab1:
    st.subheader("Create New Tenant")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Organization Name")
    with col2:
        new_plan = st.selectbox("Plan", ["free", "pro", "enterprise"])
    
    if st.button("Create Tenant"):
        if new_name:
            tenant = tm.create_tenant(new_name, new_plan)
            st.success(f"Created tenant **{tenant.name}** with API key `{tenant.api_key}`")
        else:
            st.warning("Enter a name.")

    st.divider()
    st.subheader("Active Tenants")
    tenants = tm.list_tenants()
    if tenants:
        for t in tenants:
            with st.expander(f"🏢 {t.name} ({t.plan})"):
                st.write(f"**ID:** `{t.id}`")
                st.write(f"**API Key:** `{t.api_key}`")
                st.write(f"**Created:** {t.created_at}")
                st.write(f"**Max Memories:** {t.max_memories if t.max_memories != -1 else 'Unlimited'}")
                st.write(f"**Max Queries/Day:** {t.max_queries_per_day if t.max_queries_per_day != -1 else 'Unlimited'}")
                
                # Workspace management
                st.markdown("---")
                ws_name = st.text_input("New Workspace Name", key=f"ws_{t.id}")
                if st.button("Add Workspace", key=f"ws_btn_{t.id}"):
                    if ws_name:
                        ws = tm.create_workspace(t.id, ws_name)
                        st.success(f"Workspace `{ws.name}` created.")
                
                workspaces = tm.get_workspaces(t.id)
                if workspaces:
                    for ws in workspaces:
                        st.write(f"  📁 {ws.name} (`{ws.id}`)")
    else:
        st.info("No tenants yet. Create one above.")

# Tab 2: Usage & Billing
with tab2:
    st.subheader("Usage Reports")
    tenants = tm.list_tenants()
    if tenants:
        selected = st.selectbox("Select Tenant", [t.name for t in tenants])
        tenant = next((t for t in tenants if t.name == selected), None)
        if tenant:
            report = usage_meter.get_usage_report(tenant.id)
            if report:
                for metric, data in report.items():
                    col1, col2 = st.columns(2)
                    col1.metric(f"{metric} (today)", data["today"])
                    col2.metric(f"{metric} (total)", data["total"])
            else:
                st.info("No usage recorded yet for this tenant.")
    else:
        st.info("Create a tenant first.")

# Tab 3: API Keys
with tab3:
    st.subheader("API Key Lookup")
    key_input = st.text_input("Enter API Key to verify")
    if key_input:
        tenant = tm.get_tenant_by_api_key(key_input)
        if tenant:
            st.success(f"Valid key for tenant **{tenant.name}** (plan: {tenant.plan})")
        else:
            st.error("Invalid API key.")

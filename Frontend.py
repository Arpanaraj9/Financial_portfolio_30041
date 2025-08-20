import streamlit as st
import pandas as pd
from datetime import date
from Backend import (
    create_user_and_account, 
    create_asset_and_transaction, 
    read_portfolio, 
    update_asset,
    delete_asset, 
    get_insights
)

# --- Global Initialization (Run only once) ---
# Create a single user and account for the application
if 'user_id' not in st.session_state or 'account_id' not in st.session_state:
    user_id, account_id = create_user_and_account()
    st.session_state['user_id'] = user_id
    st.session_state['account_id'] = account_id

st.set_page_config(layout="wide")
st.title("📈 Personal Financial Portfolio Tracker")
st.markdown("Track your investments and monitor portfolio performance.")

# --- Dashboard & Business Insights ---
if st.session_state['account_id']:
    st.header("Portfolio Summary")
    insights = get_insights(st.session_state['account_id'])
    
    if isinstance(insights, dict):
        total_value = insights['total_value']
        total_gain_loss = insights['total_gain_loss']
        asset_allocation = insights['asset_allocation']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Portfolio Value", f"${total_value:,.2f}")
        with col2:
            st.metric("Total Gain/Loss", f"${total_gain_loss:,.2f}", delta=f"{total_gain_loss/total_value * 100 if total_value > 0 else 0:,.2f}%")
        
        st.subheader("Asset Allocation")
        # Display asset allocation as a pie chart
        allocation_df = pd.DataFrame(list(asset_allocation.items()), columns=['Asset Class', 'Value'])
        st.bar_chart(allocation_df.set_index('Asset Class'))
    else:
        st.error(insights)

st.markdown("---")

# --- CRUD Operations ---
st.header("Manage Assets")
tab1, tab2, tab3 = st.tabs(["Add Asset", "Update Asset", "Delete Asset"])

with tab1:
    st.subheader("Add a New Asset")
    with st.form("add_asset_form"):
        ticker = st.text_input("Ticker Symbol (e.g., AAPL, BTC)").upper()
        asset_class = st.selectbox(
            "Asset Class",
            ('Equity', 'Fixed Income', 'Crypto', 'ETF', 'Commodity')
        )
        shares = st.number_input("Number of Shares", min_value=0.01, format="%.2f")
        cost_basis = st.number_input("Cost Per Share ($)", min_value=0.01, format="%.2f")
        purchase_date = st.date_input("Purchase Date", date.today())
        
        submitted = st.form_submit_button("Add Asset")
        if submitted:
            if st.session_state['user_id'] and st.session_state['account_id']:
                message = create_asset_and_transaction(
                    st.session_state['user_id'], st.session_state['account_id'], ticker, asset_class, purchase_date, shares, cost_basis
                )
                st.success(message)
            else:
                st.error("Application setup failed. Please check the backend connection.")

with tab2:
    st.subheader("Update an Existing Asset")
    st.info("Enter the Asset ID and the new values to update. Leave a field empty if you don't want to change it.")
    update_id = st.number_input("Asset ID to Update", min_value=1)
    with st.form("update_asset_form"):
        new_shares = st.number_input("New Number of Shares (Optional)", value=None, format="%.2f")
        new_cost_basis = st.number_input("New Cost Per Share ($) (Optional)", value=None, format="%.2f")
        update_submitted = st.form_submit_button("Update Asset")
        if update_submitted:
            message = update_asset(update_id, new_shares, new_cost_basis)
            st.success(message)

with tab3:
    st.subheader("Delete an Asset")
    st.warning("Deleting an asset is permanent and will also remove all its transaction history!")
    delete_id = st.number_input("Asset ID to Delete", min_value=1)
    delete_submitted = st.button("Delete Asset")
    if delete_submitted:
        message = delete_asset(delete_id)
        st.success(message)

st.markdown("---")

# --- Portfolio View (Read) ---
st.header("Your Portfolio Holdings")
portfolio = read_portfolio(st.session_state['account_id'])

if isinstance(portfolio, list):
    if portfolio:
        # Convert list of dicts to DataFrame for better display
        df = pd.DataFrame(portfolio)
        st.dataframe(df.set_index('asset_id'), use_container_width=True)
    else:
        st.info("Your portfolio is currently empty. Add a new asset to get started!")
else:
    st.error(portfolio)


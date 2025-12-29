import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --------------------------------------------------
# LOGIN CONFIG
# --------------------------------------------------
VALID_USERNAME = "admin"
VALID_PASSWORD = "admin123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    # --------------------------------------------------
    # BACKGROUND IMAGE CSS
    # --------------------------------------------------
    # Replace this URL with your preferred image if needed
    bg_image_url = "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?q=80&w=2072&auto=format&fit=crop"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{bg_image_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Make the input fields slightly transparent to look good on dark backgrounds */
        input {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------
    # CENTERED LOGIN BOX
    # --------------------------------------------------
    
    # 1. Vertical Spacing: Push the box down to the middle
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # 2. Horizontal Centering: Use 3 columns
    col1, col2, col3 = st.columns([1, 1.5, 1])

    # 3. Put the login form inside the middle column
    with col2:
        # Use a container with a border to create the "Card" effect
        with st.container(border=True):
            st.title("🔐 EV Dashboard")
            st.markdown("Please login to continue")
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            st.write("") # small spacer
            
            # use_container_width=True makes the button stretch to fill the box
            if st.button("Login", use_container_width=True):
                if username == VALID_USERNAME and password == VALID_PASSWORD:
                    st.session_state.logged_in = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

def logout():
    st.session_state.logged_in = False
    # No need to call st.rerun(); Streamlit does it automatically after the button click

if not st.session_state.logged_in:
    login_page()
    st.stop()
st.sidebar.button("🚪 Logout", on_click=logout)

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="EV Sales Dashboard",
    page_icon="⚡",
    layout="wide"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    makers = pd.read_csv(os.path.join(BASE_DIR, "EV_Makers_Sales_Cleaned.csv"))
    states = pd.read_csv(os.path.join(BASE_DIR, "EV_States_Sales_Cleaned.csv"))
    infra = pd.read_csv(os.path.join(BASE_DIR, "EV_Infrastructure_Map.csv"))
    return makers, states, infra

makers_df, states_df, infra_df = load_data()

# Ensure date is datetime
makers_df["date"] = pd.to_datetime(makers_df["date"])
states_df["date"] = pd.to_datetime(states_df["date"])

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.title("🔍 Filters")

year = st.sidebar.multiselect(
    "Fiscal Year",
    sorted(makers_df["fiscal_year"].unique()),
    default=sorted(makers_df["fiscal_year"].unique())
)

quarter = st.sidebar.multiselect(
    "Quarter",
    sorted(makers_df["quarter"].unique()),
    default=sorted(makers_df["quarter"].unique())
)

vehicle_category = st.sidebar.multiselect(
    "Vehicle Category",
    sorted(makers_df["vehicle_category"].unique()),
    default=sorted(makers_df["vehicle_category"].unique())
)

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------
makers_f = makers_df[
    (makers_df["fiscal_year"].isin(year)) &
    (makers_df["quarter"].isin(quarter)) &
    (makers_df["vehicle_category"].isin(vehicle_category))
]

states_f = states_df[
    (states_df["fiscal_year"].isin(year)) &
    (states_df["quarter"].isin(quarter)) &
    (states_df["vehicle_category"].isin(vehicle_category))
]

# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------
page = st.radio(
    "Navigation",
    ["Executive Overview", "Makers & Categories", "States & Penetration"],
    horizontal=True
)

# ==================================================
# 1️⃣ EXECUTIVE OVERVIEW
# ==================================================
if page == "Executive Overview":

    st.title("📊 Executive Overview")

    total_evs = makers_f["sales"].sum()
    total_market = states_f["total_market_sales"].sum()
    ev_penetration = total_evs / total_market if total_market else 0

    top_maker = (
        makers_f.groupby("maker")["sales"].sum().idxmax()
        if total_evs else "N/A"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total EV Sales", f"{total_evs/1e6:.2f}M")
    col2.metric("Total Market Sales", f"{total_market/1e6:.2f}M")
    col3.metric("EV Penetration %", f"{ev_penetration:.2%}")
    col4.metric("Top EV Maker", top_maker)

    st.divider()

    trend = makers_f.groupby("date")["sales"].sum().reset_index()
    fig = px.line(
        trend,
        x="date",
        y="sales",
        title="EV Sales Trend Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)

    cat = makers_f.groupby("vehicle_category")["sales"].sum().reset_index()
    fig = px.pie(
        cat,
        values="sales",
        names="vehicle_category",
        title="EV Sales Share by Vehicle Category"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- NEW VISUAL: Quarterly Sales Growth ---
    st.markdown("### 📅 Quarterly Performance")
    
    # Group by Fiscal Year and Quarter
    q_growth = makers_f.groupby(["fiscal_year", "quarter"])["sales"].sum().reset_index()
    # Create a combined column for sorting nicely on x-axis
    q_growth["period"] = q_growth["fiscal_year"].astype(str) + " - " + q_growth["quarter"]

    fig_q = px.bar(
        q_growth,
        x="period",
        y="sales",
        color="quarter",
        title="Sales Performance by Quarter (Across Years)",
        text_auto=".2s", # Adds numbers on top of bars
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_q, use_container_width=True)

# ==================================================
# 2️⃣ MAKERS & CATEGORIES (WITH KPIs)
# ==================================================
elif page == "Makers & Categories":

    st.title("🏭 Makers & Categories")

    total_evs = makers_f["sales"].sum()
    total_makers = makers_f["maker"].nunique()
    avg_sales = total_evs / total_makers if total_makers else 0

    top_maker = (
        makers_f.groupby("maker")["sales"].sum().idxmax()
        if total_evs else "N/A"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total EV Sales", f"{total_evs/1e6:.2f}M")
    col2.metric("Active Makers", total_makers)
    col3.metric("Top Maker", top_maker)
    col4.metric("Avg Sales / Maker", f"{avg_sales:,.0f}")

    st.divider()

    maker_sales = (
        makers_f.groupby("maker")["sales"]
        .sum()
        .reset_index()
        .sort_values(by="sales", ascending=False)
    )

    fig = px.bar(
        maker_sales,
        x="maker",
        y="sales",
        title="EV Sales by Maker"
    )
    st.plotly_chart(fig, use_container_width=True)

    maker_cat = (
        makers_f.groupby(["maker", "vehicle_category"])["sales"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        maker_cat,
        x="maker",
        y="sales",
        color="vehicle_category",
        title="Maker × Vehicle Category Sales"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider() 
    st.markdown("### 🧩 Market Share Hierarchy")

    # --- NEW VISUAL: Treemap (Category -> Maker) ---
    # We aggregate data to get total sales for the hierarchy
    treemap_df = makers_f.groupby(["vehicle_category", "maker"])["sales"].sum().reset_index()
    
    # Filter out very small sales to keep the chart clean (optional)
    treemap_df = treemap_df[treemap_df["sales"] > 0]

    fig_tree = px.treemap(
        treemap_df,
        path=[px.Constant("All Categories"), "vehicle_category", "maker"],
        values="sales",
        title="Market Share: Category > Maker Hierarchy",
        color="sales",
        color_continuous_scale="Viridis"
    )
    # Update layout to show labels clearly
    fig_tree.update_traces(root_color="lightgrey")
    fig_tree.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    
    st.plotly_chart(fig_tree, use_container_width=True)

# ==================================================
# 3️⃣ STATES & PENETRATION (WITH KPIs)
# ==================================================
else:

    st.title("🗺 States & EV Penetration")

    total_states = states_f["state"].nunique()
    total_evs = states_f["sales"].sum()

    states_f["ev_penetration"] = (
        states_f["sales"] / states_f["total_market_sales"]
    )

    avg_penetration = states_f["ev_penetration"].mean()

    top_state = (
        states_f.groupby("state")["sales"].sum().idxmax()
        if total_evs else "N/A"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total EV Sales", f"{total_evs/1e6:.2f}M")
    col2.metric("States Covered", total_states)
    col3.metric("Top State", top_state)
    col4.metric("Avg EV Penetration", f"{avg_penetration:.2%}")

    st.divider()

    state_sales = (
        states_f.groupby("state")["sales"]
        .sum()
        .reset_index()
        .sort_values(by="sales", ascending=False)
    )

    fig = px.bar(
        state_sales,
        x="sales",
        y="state",
        orientation="h",
        title="Total EV Sales by State"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(
        states_f,
        x="date",
        y="ev_penetration",
        color="state",
        title="EV Penetration Trend by State"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### 🎯 State Maturity Matrix")

    # --- NEW VISUAL: Scatter Plot (Market Size vs Penetration) ---
    # Group data by state to get totals
    state_scatter = states_f.groupby("state").agg({
        "sales": "sum", # EV Sales
        "total_market_sales": "sum", # Total Vehicle Sales
        "ev_penetration": "mean" # Avg Penetration
    }).reset_index()

    fig_scatter = px.scatter(
        state_scatter,
        x="total_market_sales",
        y="ev_penetration",
        size="sales",   # Bubble size = EV Sales volume
        color="state",  # Different color for each state
        hover_name="state",
        title="EV Maturity: Total Market Size vs. EV Penetration",
        labels={
            "total_market_sales": "Total Vehicle Market Size (Sales)",
            "ev_penetration": "EV Penetration %"
        },
        log_x=True # Use log scale because some states (like UP/Maharashtra) are huge
    )
    
    # Add a reference line for average penetration
    fig_scatter.add_hline(y=avg_penetration, line_dash="dot", 
                        annotation_text="Avg Penetration", annotation_position="bottom right")

    st.plotly_chart(fig_scatter, use_container_width=True)
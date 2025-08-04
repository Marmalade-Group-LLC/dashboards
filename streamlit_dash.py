# app.py
import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------- Page config ---------------------------
st.set_page_config(page_title="Sales Analysis", page_icon="📈", layout="wide")

# --------------------------- Helpers ---------------------------
EXPECTED_COLUMNS = [
    "Company","Customer Number","Customer ID","Customer Name",
    "Customer City","Customer State","Customer Country",
    "ShipTo Name","ShipTo City","ShipTo State","ZIP Code","ShipTo Country",
    "Order Number","Plant","Invoice Number","Invoice Date","Invoice Amount",
    "Invoice Line","Part Number","Line Description","Product Family",
    "Order Qty","Ship Qty","Misc Charges","Tax Code","Rate Code",
    "Taxable Amount","Tax Percent","Tax Amount",
    "Avg Total Cost","Avg Labor Cost","Avg Burden Cost","Avg Material Cost",
    "Avg Subcontract Cost","Avg Material Burden Cost","Cost ID"
]

def add_calendar_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Add Year / Month Name / Quarter / Year-Month if they are missing.
    (Light-touch; your CSV is already cleaned.)"""
    out = df.copy()
    if "Invoice Date" in out.columns and not np.issubdtype(out["Invoice Date"].dtype, np.datetime64):
        # Only parse type; no transformation of values
        out["Invoice Date"] = pd.to_datetime(out["Invoice Date"], errors="coerce")

    if "Year" not in out.columns and "Invoice Date" in out.columns:
        out["Year"] = out["Invoice Date"].dt.year

    month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    if "Month Name" not in out.columns and "Invoice Date" in out.columns:
        out["Month Name"] = out["Invoice Date"].dt.strftime('%b')
    if "Month Name" in out.columns:
        out["Month Name"] = pd.Categorical(out["Month Name"], categories=month_order, ordered=True)

    if "Quarter" not in out.columns and "Invoice Date" in out.columns:
        out["Quarter"] = 'Q' + out["Invoice Date"].dt.quarter.astype(str)

    if "Year-Month" not in out.columns and "Invoice Date" in out.columns:
        out["Year-Month"] = out["Invoice Date"].dt.to_period("M").astype(str)

    return out

def kpi_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)

def plot_top_cities_map(df, size_by="sales", color_hex="#2E86AB", title=None):
    """Expects df with ['lat','lon','total_sales','n_invoices','Customer City','Customer State']."""
    if not {"lat","lon"}.issubset(df.columns):
        st.info("No 'lat'/'lon' columns found. Precompute geocodes in your data to enable the map.")
        return

    m = df.dropna(subset=['lat','lon']).copy()
    m["total_sales"] = pd.to_numeric(m["total_sales"], errors="coerce")
    m["n_invoices"]  = pd.to_numeric(m["n_invoices"], errors="coerce")
    m["total_sales_$"] = m["total_sales"].map(lambda x: f"${x:,.2f}")
    size_col = "total_sales" if size_by == "sales" else "n_invoices"

    # Prefer MapLibre API when available
    if hasattr(px, "scatter_map"):
        fig = px.scatter_map(
            m, lat="lat", lon="lon", size=size_col, hover_name="Customer City",
            hover_data={"total_sales_$": True, "n_invoices":":.0f"},
            size_max=40, zoom=3, map_style="carto-positron",
            title=title or f"Top Cities by {'Sales' if size_by=='sales' else 'Invoice Count'}"
        )
    else:
        fig = px.scatter_mapbox(
            m, lat="lat", lon="lon", size=size_col, hover_name="Customer City",
            hover_data={"total_sales_$": True, "n_invoices":":.0f"},
            size_max=40, zoom=3, mapbox_style="carto-positron",
            title=title or f"Top Cities by {'Sales' if size_by=='sales' else 'Invoice Count'}"
        )
    fig.update_traces(marker=dict(color=color_hex, opacity=0.85))
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------- Data loader ---------------------------
@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    if isinstance(file, str):
        df = pd.read_csv(file, encoding="latin1", parse_dates=["Invoice Date"])
    else:
        df = pd.read_csv(file, encoding="latin1", parse_dates=["Invoice Date"])
    return add_calendar_if_missing(df)

# --------------------------- Sidebar ---------------------------
st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader("Upload cleaned CSV", type=["csv"])
default_path = st.sidebar.text_input("...or path to CSV", value="", help="Optional local path on the server.")
df = None
if uploaded is not None:
    df = load_data(uploaded)
elif default_path:
    df = load_data(default_path)
else:
    st.info("Upload your **cleaned** CSV to get started.")
    st.stop()

# Global display prefs (just for Streamlit tables)
pd.options.display.float_format = "{:,.2f}".format

# Filters
st.sidebar.header("Filters")
state_filter = st.sidebar.multiselect("Customer State", sorted(df["Customer State"].dropna().unique().tolist()))
family_filter = st.sidebar.multiselect("Product Family", sorted(df["Product Family"].dropna().unique().tolist()))
date_min, date_max = df["Invoice Date"].min(), df["Invoice Date"].max()
date_range = st.sidebar.date_input("Date range", value=(date_min, date_max))

mask = pd.Series(True, index=df.index)
if state_filter:
    mask &= df["Customer State"].isin(state_filter)
if family_filter:
    mask &= df["Product Family"].isin(family_filter)
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask &= (df["Invoice Date"] >= start) & (df["Invoice Date"] <= end)

data = df.loc[mask].copy()

# --------------------------- Header KPIs ---------------------------
st.title("📈 Sales Analysis Dashboard")

c1, c2, c3, c4 = st.columns(4)
kpi_card("Revenue", f"${data['Invoice Amount'].sum():,.0f}")
kpi_card("Invoices", f"{data['Invoice Number'].nunique():,.0f}")
kpi_card("Customers", f"{data['Customer ID'].nunique():,.0f}")
avg_order = data.groupby("Invoice Number")["Invoice Amount"].sum().mean()
kpi_card("Avg Invoice", f"${avg_order:,.0f}")

st.divider()

# --------------------------- Tabs ---------------------------
tabs = st.tabs([
    "Overview", "Customers", "Geography", "Time Series",
    "Profitability", "Service Quality", "Cohorts & RFM",
    "Product Mix", "Market Basket"
])

# ---------- Overview ----------
with tabs[0]:
    st.subheader("Top Cities & States")
    city_group = (
        data.groupby(["Customer City", "Customer State"], dropna=False)
            .agg(total_sales=("Invoice Amount","sum"),
                 n_invoices=("Invoice Number","nunique"))
            .reset_index()
            .sort_values("total_sales", ascending=False)
    )
    cA, cB = st.columns([2,1])
    with cA:
        fig = px.bar(city_group.head(20), x="total_sales", y="Customer City",
                     orientation="h", labels={"total_sales":"Total Sales ($)"},
                     title="Top 20 Cities by Sales", color_discrete_sequence=["#2E86AB"])
        fig.update_layout(yaxis={"categoryorder":"total ascending"})
        fig.update_xaxes(separatethousands=True, tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)
    with cB:
        st.dataframe(city_group.head(20).style.format({
            "total_sales":"${:,.2f}", "n_invoices":"{:,.0f}"
        }), use_container_width=True)

# ---------- Customers ----------
with tabs[1]:
    st.subheader("Top Customers")
    cust_group = (
        data.groupby("Customer Name", dropna=False)
            .agg(total_sales=("Invoice Amount","sum"),
                 n_invoices=("Invoice Number","nunique"),
                 n_orders=("Order Number","nunique"))
            .reset_index()
            .sort_values("total_sales", ascending=False)
    )
    fig = px.bar(cust_group.head(20), x="total_sales", y="Customer Name",
                 orientation="h", labels={"total_sales":"Total Sales ($)"},
                 title="Top 20 Customers by Sales")
    fig.update_layout(yaxis={"categoryorder":"total ascending"})
    fig.update_xaxes(separatethousands=True, tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(cust_group.head(50).style.format({
        "total_sales":"${:,.2f}", "n_invoices":"{:,.0f}", "n_orders":"{:,.0f}"
    }), use_container_width=True)

# ---------- Geography ----------
with tabs[2]:
    st.subheader("Revenue by State (USA)")
    state_rev = (data.groupby("Customer State", as_index=False)
                    .agg(revenue=("Invoice Amount","sum"),
                         invoices=("Invoice Number","nunique")))
    state_rev_us = state_rev[state_rev["Customer State"].str.len()==2].copy()
    fig = px.choropleth(state_rev_us, locationmode="USA-states",
                        locations="Customer State", color="revenue", scope="usa",
                        hover_name="Customer State",
                        hover_data={"revenue":":$", "invoices":":.0f"},
                        title="Revenue by State")
    fig.update_layout(coloraxis_colorbar=dict(title="Revenue"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Cities (Map)")
    # If your data file already includes 'lat'/'lon' for top cities, this will render
    plot_top_cities_map(city_group.head(15))

# ---------- Time Series ----------
with tabs[3]:
    st.subheader("Monthly Sales")
    monthly_sales = (
        data.groupby("Year-Month", as_index=False)
            .agg(total_sales=("Invoice Amount","sum"),
                 invoices=("Invoice Number","nunique"))
            .sort_values("Year-Month")
    )
    fig = px.line(monthly_sales, x="Year-Month", y="total_sales",
                  markers=True, title="Monthly Sales ($)")
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("YoY Monthly Sales by Month")
    month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    yoy_month = (
        data.groupby(["Year","Month Name"], as_index=False, observed=True)
            .agg(total_sales=("Invoice Amount","sum"))
            .sort_values(["Year","Month Name"])
    )
    yoy_month_plot = yoy_month.copy()
    yoy_month_plot["Year"] = yoy_month_plot["Year"].astype(str)
    fig = px.line(yoy_month_plot, x="Month Name", y="total_sales", color="Year",
                  category_orders={"Month Name": month_order},
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  markers=True, title="YoY Monthly Sales by Month")
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Quarterly Revenue")
    qrev = (data.groupby(["Year","Quarter"], as_index=False, observed=True)
              .agg(total_sales=("Invoice Amount","sum"))
              .sort_values(["Year","Quarter"]))
    qrev["Year"] = qrev["Year"].astype(str)
    fig = px.bar(qrev, x="Quarter", y="total_sales", color="Year",
                 barmode="group", title="Quarterly Revenue",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_xaxes(categoryorder="array", categoryarray=["Q1","Q2","Q3","Q4"])
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Profitability ----------
with tabs[4]:
    st.subheader("Margin by Product Family")
    # Expect either precomputed total cost or per-unit cost; use best effort
    COST_IS_PER_UNIT = True
    d = data.copy()
    if "Avg Total Cost" in d.columns:
        if COST_IS_PER_UNIT:
            d["Total Cost Calc"] = np.where(
                pd.to_numeric(d["Ship Qty"], errors="coerce").fillna(0) > 0,
                d["Avg Total Cost"] * pd.to_numeric(d["Ship Qty"], errors="coerce").fillna(0),
                d["Avg Total Cost"]
            )
        else:
            d["Total Cost Calc"] = d["Avg Total Cost"]
    else:
        d["Total Cost Calc"] = np.nan

    pf_margin = (d.groupby("Product Family", as_index=False)
                   .agg(revenue=("Invoice Amount","sum"),
                        cost=("Total Cost Calc","sum"),
                        orders=("Invoice Number","nunique")))
    pf_margin["margin"]  = pf_margin["revenue"] - pf_margin["cost"]
    pf_margin["margin%"] = np.where(pf_margin["revenue"]>0, pf_margin["margin"]/pf_margin["revenue"], np.nan)
    pf_margin = pf_margin.sort_values("margin", ascending=False)

    fig = px.bar(pf_margin, x="margin", y="Product Family", orientation="h",
                 labels={"margin":"Margin ($)"}, title="Margin by Product Family")
    fig.update_xaxes(tickprefix="$", separatethousands=True)
    fig.update_layout(yaxis={"categoryorder":"total ascending"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pf_margin.style.format({
        "revenue":"${:,.0f}","cost":"${:,.0f}","margin":"${:,.0f}","margin%":"{:.1%}"
    }), use_container_width=True)

# ---------- Service Quality ----------
with tabs[5]:
    st.subheader("Fill Rate by Month × Product Family")
    # Expect 'Order Qty' / 'Ship Qty' present
    svc = data.copy()
    svc["Order Qty"] = pd.to_numeric(svc["Order Qty"], errors="coerce").fillna(0)
    svc["Ship Qty"]  = pd.to_numeric(svc["Ship Qty"], errors="coerce").fillna(0)
    svc["Fill Rate"] = np.where(svc["Order Qty"]>0, svc["Ship Qty"]/svc["Order Qty"], np.nan).clip(0,1)

    fill = (svc.groupby(["Year-Month","Product Family"], as_index=False)
              .agg(fill_rate=("Fill Rate","mean"),
                   invoices=("Invoice Number","nunique")))
    pivot = fill.pivot(index="Product Family", columns="Year-Month", values="fill_rate").fillna(0)
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale="Blues",
                    title="Fill Rate (Avg) by Product Family × Month", text_auto=".0%")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Cohorts & RFM ----------
with tabs[6]:
    st.subheader("New vs Returning Customers per Month")
    tmp = data.copy()
    first_purchase = (tmp.sort_values("Invoice Date")
                        .groupby("Customer ID", as_index=False)["Invoice Date"].first()
                        .rename(columns={"Invoice Date":"First Purchase Date"}))
    first_purchase["First YM"] = first_purchase["First Purchase Date"].dt.to_period("M").astype(str)
    tmp = tmp.merge(first_purchase[["Customer ID","First YM"]], on="Customer ID", how="left")
    tmp["Year-Month"] = tmp["Invoice Date"].dt.to_period("M").astype(str)
    tmp["Cust Type"] = np.where(tmp["Year-Month"] == tmp["First YM"], "New", "Returning")
    nr_month = (tmp.groupby(["Year-Month","Cust Type"], as_index=False)
                  .agg(total_sales=("Invoice Amount","sum"),
                       invoices=("Invoice Number","nunique"),
                       customers=("Customer ID","nunique")))
    fig = px.area(nr_month, x="Year-Month", y="total_sales", color="Cust Type",
                  title="Monthly Sales: New vs Returning Customers")
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("RFM (Recency–Frequency–Monetary)")
    snapshot = data["Invoice Date"].max() + pd.Timedelta(days=1)
    rfm = (data.groupby("Customer ID")
              .agg(Recency=("Invoice Date", lambda s: (snapshot - s.max()).days),
                   Frequency=("Invoice Number","nunique"),
                   Monetary=("Invoice Amount","sum"))
              .reset_index())
    # Quintiles
    rfm["R"] = pd.qcut(rfm["Recency"], 5, labels=[5,4,3,2,1]).astype(int)
    rfm["F"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    rfm["M"] = pd.qcut(rfm["Monetary"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    rfm["RFM Score"] = rfm["R"]*100 + rfm["F"]*10 + rfm["M"]
    fig = px.scatter(rfm, x="Frequency", y="Monetary", size="R",
                     hover_data=["Customer ID"], title="RFM: Frequency vs Monetary")
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Product Mix ----------
with tabs[7]:
    st.subheader("Monthly Sales by Product Family")
    pf_month = (data.groupby(["Year-Month","Product Family"], as_index=False)
                  .agg(total_sales=("Invoice Amount","sum"))
                  .sort_values("Year-Month"))
    fig = px.line(pf_month, x="Year-Month", y="total_sales", color="Product Family",
                  markers=True, title="Monthly Sales by Product Family")
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Market Basket ----------
with tabs[8]:
    st.subheader("Top Co-Purchased Product Family Pairs")
    pairs = []
    for inv, g in data.groupby("Invoice Number"):
        fams = sorted(set(g["Product Family"].dropna()))
        for i in range(len(fams)):
            for j in range(i+1, len(fams)):
                pairs.append((fams[i], fams[j]))
    if pairs:
        pairs_df = pd.DataFrame(pairs, columns=["A","B"])
        pair_counts = pairs_df.value_counts().reset_index(name="count").sort_values("count", ascending=False).head(20)
        fig = px.bar(pair_counts, x="count",
                     y=pair_counts.apply(lambda r: f"{r['A']} + {r['B']}", axis=1),
                     orientation="h", title="Top Co-Purchased Product Family Pairs")
        fig.update_layout(yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pair_counts, use_container_width=True)
    else:
        st.info("Not enough diversity in Product Family per invoice to compute pairs.")

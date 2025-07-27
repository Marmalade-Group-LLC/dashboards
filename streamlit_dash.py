import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Invoice Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load data
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Rename columns for readability
    rename_map = {
        'Sales_Tax__c': 'Sales Tax',
        'Total_Cost__c': 'Total Cost',
        'Total_Price__c': 'Total Price',
        'BurUnitCost__c': 'Unit Cost',
        'Product_Family__c': 'Product Family',
        'Packaging': 'Packaging',
        'Product': 'Product',
        'CreatedDate_month': 'Month',
        'CreatedDate_year': 'Year'
    }
    df = df.rename(columns=rename_map)

    # Ensure necessary date columns
    for col in ['Month', 'Year']:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    # Enforce chronological month order
    month_cats = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    df['Month'] = pd.Categorical(df['Month'], categories=month_cats, ordered=True)

    return df

# Main
#data_path = "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/duet_invoice_cleaned.csv"
data_path = "duet_invoice_cleaned.csv"
df_original = load_data(data_path)

# Keep only relevant columns
df = df_original[[
    'Sales Tax', 'Total Cost', 'Total Price', 'Unit Cost',
    'Product Family', 'Packaging', 'Product', 'Month', 'Year'
]].copy()

# Sidebar filters
st.sidebar.header("Filters")
families = st.sidebar.multiselect(
    "Product Family", df['Product Family'].unique(), df['Product Family'].unique()
)
df_filtered = df[df['Product Family'].isin(families)].copy()

# Analysis options
st.sidebar.markdown("### Analysis Options")
metric_options = ['Sales Tax', 'Total Cost', 'Total Price', 'Unit Cost']
agg_options = ['sum', 'mean', 'median', 'count', 'mode']
selected_metric = st.sidebar.selectbox("Select metric", metric_options, index=2)
selected_agg = st.sidebar.selectbox("Select aggregation", agg_options, index=0)

# Tabs for analyses
tabs = st.tabs([
    "Descriptive Stats", "Correlation", "Time Trends",
    "Family Breakdown", "Packaging Analysis", "Product Analysis",
    "Tax Rate", "Cost vs Price", "YoY Growth"
])

# 1. Descriptive Statistics
def descriptive_stats():
    st.write("### Descriptive Statistics")
    desc = df_filtered[metric_options].describe().T
    styled = desc.style.format({
        'mean': '${:,.2f}',
        'std': '${:,.2f}',
        'min': '${:,.2f}',
        '25%': '${:,.2f}',
        '50%': '${:,.2f}',
        '75%': '${:,.2f}',
        'max': '${:,.2f}',
        'count': '{:,.0f}'
    })
    st.dataframe(styled)

# 2. Value Correlation
def correlation_matrix():
    st.write("### Value Correlation Matrix")
    corr = df_filtered[metric_options].corr()
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale='Blues',
        labels={'x':'Metrics','y':'Metrics','color':'Correlation'}
    )
    st.plotly_chart(fig, use_container_width=True)

# 3. Monthly Trends

def monthly_trend():
    st.write(f"### Monthly Trend: {selected_agg.title()} of {selected_metric}")
    # aggregate selected metric by Year and Month with chosen aggregation
    if selected_agg == 'mode':
        temp = df_filtered.groupby(['Year','Month'])[selected_metric].apply(
            lambda x: x.mode().iat[0] if not x.mode().empty else np.nan
        ).reset_index(name=selected_metric)
    else:
        grp = df_filtered.groupby(['Year','Month'])[selected_metric]
        agg_func = 'count' if selected_agg=='count' else selected_agg
        temp = grp.agg(agg_func).reset_index()

    # drop zero or NaN values for clarity
    temp = temp.dropna(subset=[selected_metric])
    if selected_agg in ['sum','count']:
        temp = temp[temp[selected_metric] != 0]

    # ensure chronological month order
    month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    temp['Month'] = pd.Categorical(temp['Month'], categories=month_order, ordered=True)
    temp = temp.sort_values(['Year','Month'])

    # plot
    fig = px.line(
        temp,
        x='Month',
        y=selected_metric,
        color='Year',
        markers=True,
        category_orders={'Month': month_order},
        labels={selected_metric:f"{selected_agg.title()} of {selected_metric}", 'Month':'Month'}
    )
    # formatting axis
    if selected_agg in ['mean','median']:
        fig.update_yaxes(tickformat='.2f')
    elif selected_agg=='count':
        fig.update_yaxes(tickformat='d')
    else:
        fig.update_yaxes(tickformat=',.2f')

    st.plotly_chart(fig, use_container_width=True)

# 4. Family Breakdown
def family_breakdown():
    st.write("### Revenue by Product Family")
    fam = (
        df_filtered
        .groupby('Product Family')['Total Price']
        .agg(['count','sum','mean'])
        .reset_index()
        .sort_values('sum', ascending=False)
    )
    fig = px.bar(
        fam,
        x='Product Family',
        y='sum',
        title='Total Revenue per Product Family',
        labels={'sum':'Total Revenue ($)'}
    )
    st.plotly_chart(fig, use_container_width=True)

    fam_display = fam.copy()
    fam_display.columns = ['Product Family','Count','Total Revenue','Average Revenue']
    fam_display['Total Revenue'] = fam_display['Total Revenue'].map(lambda x: f"${x:,.2f}")
    fam_display['Average Revenue'] = fam_display['Average Revenue'].map(lambda x: f"${x:,.2f}")
    st.dataframe(fam_display)

# 5. Packaging Analysis
def packaging_analysis():
    st.write(f"### Packaging Analysis: {selected_agg.title()} of {selected_metric}")
    dfg = df_filtered.groupby('Packaging')[selected_metric]
    if selected_agg == 'mode':
        pkg = dfg.apply(lambda x: x.mode().iat[0] if not x.mode().empty else np.nan)
    elif selected_agg == 'count':
        pkg = dfg.count()
    else:
        pkg = getattr(dfg, selected_agg)()
    pkg = pkg.reset_index().dropna()
    pkg.columns = ['Packaging', selected_metric]
    pkg = pkg.sort_values(selected_metric, ascending=False)
    fig = px.bar(
        pkg,
        x='Packaging',
        y=selected_metric,
        title=f"{selected_agg.title()} of {selected_metric} by Packaging",
        labels={selected_metric:f"{selected_agg.title()} of {selected_metric}"}
    )
    st.plotly_chart(fig, use_container_width=True)

# 6. Product Analysis
def product_analysis():
    st.write(f"### Product Analysis: Top 20 Products by {selected_agg.title()} of {selected_metric}")
    dfg = df_filtered.groupby('Product')[selected_metric]
    if selected_agg == 'mode':
        prod = dfg.apply(lambda x: x.mode().iat[0] if not x.mode().empty else np.nan)
    elif selected_agg == 'count':
        prod = dfg.count()
    else:
        prod = getattr(dfg, selected_agg)()
    prod = (
        prod.reset_index()
        .rename(columns={selected_metric:selected_metric})
        .dropna()
        .sort_values(selected_metric, ascending=False)
        .head(20)
    )
    fig = px.bar(
        prod,
        x='Product',
        y=selected_metric,
        title=f"Top 20 Products by {selected_agg.title()} of {selected_metric}",
        labels={selected_metric:f"{selected_agg.title()} of {selected_metric}"}
    )
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# 7. Tax Rate Analysis
def tax_rate():
    st.write("### Effective Tax Rate by Product Family")
    temp = df_filtered.dropna(subset=['Sales Tax','Total Price']).copy()
    temp = temp[temp['Total Price'] > 0]
    temp['Tax Rate'] = temp['Sales Tax'] / temp['Total Price']
    fig = px.box(
        temp,
        x='Product Family',
        y='Tax Rate',
        points='outliers',
        labels={'Tax Rate':'Tax Rate (%)'}
    )
    fig.update_yaxes(tickformat='.1%')
    st.plotly_chart(fig, use_container_width=True)

# 8. Cost vs Price Scatter
def cost_vs_price():
    st.write("### Unit Cost vs Total Price Scatter Plot")
    fig = px.scatter(
        df_filtered,
        x='Unit Cost',
        y='Total Price',
        color='Product Family',
        hover_data=['Product','Packaging'],
        opacity=0.6,
        labels={'Unit Cost':'Unit Cost ($)','Total Price':'Total Price ($)'}
    )
    st.plotly_chart(fig, use_container_width=True)

# 9. YoY Growth
def yoy_growth():
    st.write("### Year-over-Year Revenue Growth Rate")
    all_years = [2022,2023,2024,2025]
    rev = df_filtered.groupby('Year')['Total Price'].sum().reset_index()
    pct = rev.copy()
    pct['Growth'] = pct['Total Price'].pct_change().mul(100)
    pct_full = pd.DataFrame({'Year':all_years}).merge(
        pct[['Year','Growth']], on='Year', how='left'
    ).fillna({'Growth':0})
    pct_full['Year'] = pct_full['Year'].astype(str)
    fig = px.bar(
        pct_full,
        x='Year',
        y='Growth',
        text=pct_full['Growth'].round(1).astype(str)+'%',
        labels={'Growth':'Growth Rate (%)','Year':'Year'},
        title='Year-over-Year Revenue Growth Rate'
    )
    fig.update_traces(textposition='outside')
    fig.update_yaxes(tickformat='.1f')
    st.plotly_chart(fig, use_container_width=True)

# Render tabs
funcs = [
    descriptive_stats, correlation_matrix, monthly_trend,
    family_breakdown, packaging_analysis, product_analysis,
    tax_rate, cost_vs_price, yoy_growth
]
for tab, fn in zip(tabs, funcs):
    with tab:
        fn()

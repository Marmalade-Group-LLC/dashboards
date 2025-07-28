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
    "Tax Rate", "Cost vs Price", "Quarterly Growth"
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

# 9. Quarterly Growth (YoY and QoQ)
def yoy_growth_quarterly():
    st.write("### Quarterly and Yearly Revenue Growth")

    # --- 1. Prepare Quarterly Data ---
    temp = df_filtered.copy()
    # Create a Quarter column based on Month
    month_to_q = {'Jan': 'Q1', 'Feb': 'Q1', 'Mar': 'Q1',
                  'Apr': 'Q2', 'May': 'Q2', 'Jun': 'Q2',
                  'Jul': 'Q3', 'Aug': 'Q3', 'Sep': 'Q3',
                  'Oct': 'Q4', 'Nov': 'Q4', 'Dec': 'Q4'}
    temp['Quarter'] = temp['Month'].map(month_to_q)
    # Keep only 2023–2025
    years = [2023, 2024, 2025]
    temp = temp[temp['Year'].isin(years)]
    
    # Aggregate revenue per Year-Quarter
    qrev = temp.groupby(['Year', 'Quarter'])['Total Price'].sum().reset_index()
    # Ensure all quarters exist
    all_combos = pd.MultiIndex.from_product([years, ['Q1','Q2','Q3','Q4']], names=['Year', 'Quarter'])
    qrev = qrev.set_index(['Year','Quarter']).reindex(all_combos, fill_value=0).reset_index()

    # --- 2. Compute QoQ and YoY Growth ---
    qrev['QoQ Growth (%)'] = qrev.groupby('Year')['Total Price'].pct_change().mul(100)
    # Year-over-Year Growth per quarter (e.g. Q2 2024 vs Q2 2023)
    qrev['YoY Growth (%)'] = qrev.groupby('Quarter')['Total Price'].pct_change().mul(100)
    
    # --- 3. Visualization ---
    # A. Bar chart for Revenue (grouped by Year, x=Quarter)
    fig = go.Figure()
    for year in years:
        data = qrev[qrev['Year'] == year]
        fig.add_trace(go.Bar(
            x=data['Quarter'],
            y=data['Total Price'],
            name=f"{year} Revenue",
            text=[f"${x:,.0f}" for x in data['Total Price']],
            textposition='outside'
        ))

    # B. Add YoY Growth Line for each year (excluding 2023, which has no YoY)
    colors = {2024: 'crimson', 2025: 'mediumseagreen'}
    for year in [2024, 2025]:
        data = qrev[qrev['Year'] == year]
        fig.add_trace(go.Scatter(
            x=data['Quarter'],
            y=data['YoY Growth (%)'],
            name=f"{year} YoY Growth",
            mode='lines+markers',
            yaxis='y2',
            marker=dict(size=10, color=colors[year]),
            line=dict(width=3, color=colors[year]),
            text=[f"{x:.1f}%" for x in data['YoY Growth (%)']],
            textposition='top center'
        ))
    # Layout
    fig.update_layout(
        title='Quarterly Revenue and Year-over-Year Growth',
        xaxis=dict(title='Quarter'),
        yaxis=dict(title='Revenue ($)'),
        yaxis2=dict(title='YoY Growth (%)', overlaying='y', side='right', showgrid=False),
        barmode='group',
        legend=dict(orientation='h'),
        margin=dict(t=50, b=30),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(qrev)

# Render tabs
funcs = [
    descriptive_stats, correlation_matrix, monthly_trend,
    family_breakdown, packaging_analysis, product_analysis,
    tax_rate, cost_vs_price, yoy_growth_quarterly
]
for tab, fn in zip(tabs, funcs):
    with tab:
        fn()

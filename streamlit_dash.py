import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Salesforce Product & Order Analytics",
    page_icon="▊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure plotly defaults for better visibility
import plotly.io as pio

pio.templates.default = "plotly_white"

# Professional CSS styling
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stApp {
        background-color: #ffffff;
    }
    /* Force white background for the main content area */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #ddd;
        margin: 10px 0;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-family: Arial, sans-serif;
        font-weight: normal;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: #f0f0f0;
        padding: 0px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        padding: 8px 16px;
        background-color: #e0e0e0;
        border-radius: 0px;
        font-weight: normal;
        border: 1px solid #ccc;
        color: #000000 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 1px solid #ffffff;
        color: #000000 !important;
    }
    .stMetric label {
        font-size: 14px;
        color: #000000 !important;
        font-weight: normal;
    }
    .stMetric > div {
        font-size: 24px;
        font-weight: normal;
        color: #000000 !important;
    }
    div[data-testid="metric-container"] {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 4px;
        box-shadow: none;
    }
    /* Ensure text is visible */
    .stMarkdown {
        color: #000000 !important;
    }
    p {
        color: #000000 !important;
    }
    /* White background for plots */
    .js-plotly-plot {
        background-color: white !important;
    }
    /* Ensure dataframes have white background */
    .stDataFrame {
        background-color: white;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #000000 !important;
    }
    /* Force black text in all plotly charts */
    .plotly text {
        fill: #000000 !important;
    }
    .plotly .gtitle {
        fill: #000000 !important;
    }
    .plotly .g-xtitle, .plotly .g-ytitle {
        fill: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)


# Load data with caching
@st.cache_data
def load_data():
    product_df = pd.read_csv(
        "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/Salesforce-Pipeline/ccrz__E_Product__c-7_22_2025.csv")
    order_df = pd.read_csv(
        "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/Salesforce-Pipeline/ccrz__E_Order__c-7_22_2025.csv")

    # Convert date columns
    if 'CreatedDate' in product_df.columns:
        product_df['CreatedDate'] = pd.to_datetime(product_df['CreatedDate'], errors='coerce')

    return product_df, order_df


# Helper functions
def format_currency(value):
    if pd.isna(value) or value == 0:
        return "$0.00"
    return f"${value:,.2f}"


def format_percentage(value):
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1f}%"


def update_chart_layout(fig, **kwargs):
    """Apply consistent white background styling to all charts"""
    default_layout = {
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'font': {'color': '#333333'},
        'xaxis': {'gridcolor': '#E5E5E5', 'zerolinecolor': '#E5E5E5'},
        'yaxis': {'gridcolor': '#E5E5E5', 'zerolinecolor': '#E5E5E5'}
    }
    default_layout.update(kwargs)
    fig.update_layout(**default_layout)
    return fig


# Main app
try:
    # Load data
    product_df, order_df = load_data()

    # Theme toggle
    col1, col2, col3 = st.columns([1, 4, 1])
    with col3:
        dark_mode = st.checkbox("Dark Mode Compatible", value=True,
                                help="Enable white backgrounds for dark browser themes")

    # Apply theme-specific styling
    if dark_mode:
        chart_bg_color = 'white'
        grid_color = '#E5E5E5'
    else:
        chart_bg_color = 'rgba(0,0,0,0)'
        grid_color = 'rgba(0,0,0,0.1)'


    # Update the helper function based on theme
    def update_chart_layout(fig, **kwargs):
        """Apply consistent styling to all charts"""
        default_layout = {
            'plot_bgcolor': chart_bg_color,
            'paper_bgcolor': chart_bg_color,
            'font': {'color': '#000000', 'size': 12},  # Black text for maximum contrast
            'xaxis': {
                'gridcolor': grid_color,
                'zerolinecolor': grid_color,
                'tickfont': {'color': '#000000', 'size': 11},
                'title': {'font': {'color': '#000000', 'size': 12}}
            },
            'yaxis': {
                'gridcolor': grid_color,
                'zerolinecolor': grid_color,
                'tickfont': {'color': '#000000', 'size': 11},
                'title': {'font': {'color': '#000000', 'size': 12}}
            },
            'title': {
                'font': {'color': '#000000', 'size': 14}
            }
        }
        default_layout.update(kwargs)
        fig.update_layout(**default_layout)
        # Update legend text color
        fig.update_layout(legend=dict(font=dict(color='#000000')))
        return fig


    # Header
    st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>Salesforce Product & Order Analytics</h1>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #666; margin-top: 0px;'>Comprehensive analysis of products, pricing, and profitability</p>",
        unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        # Category filter
        if 'Category__c' in product_df.columns:
            categories = st.multiselect(
                "Product Categories",
                options=product_df['Category__c'].dropna().unique(),
                default=product_df['Category__c'].dropna().unique()
            )
            filtered_products = product_df[product_df['Category__c'].isin(categories)]
        else:
            filtered_products = product_df

        # Packaging Type filter
        if 'Packaging_Type__c' in product_df.columns:
            packaging_types = st.multiselect(
                "Packaging Types",
                options=product_df['Packaging_Type__c'].dropna().unique(),
                default=product_df['Packaging_Type__c'].dropna().unique()
            )
            filtered_products = filtered_products[filtered_products['Packaging_Type__c'].isin(packaging_types)]

        # Royalty filter
        if 'Royalty__c' in product_df.columns:
            show_royalty = st.radio("Royalty Products", ["All", "Royalty Only", "Non-Royalty Only"])
            if show_royalty == "Royalty Only":
                filtered_products = filtered_products[filtered_products['Royalty__c'].astype(str).str.upper() == 'TRUE']
            elif show_royalty == "Non-Royalty Only":
                filtered_products = filtered_products[
                    filtered_products['Royalty__c'].astype(str).str.upper() == 'FALSE']

        st.markdown("---")
        st.markdown("### Summary Statistics")
        st.metric("Total Products", f"{len(filtered_products):,}")
        st.metric("Total Orders", f"{len(order_df):,}")

        if 'Total_Cost__c' in order_df.columns:
            total_cost = order_df['Total_Cost__c'].sum()
            st.metric("Total Cost", format_currency(total_cost))

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Executive Summary",
        "Product Analysis",
        "Pricing & Costs",
        "Profitability Analysis",
        "Order Analysis"
    ])

    with tab1:
        # Executive Summary
        st.markdown("### Key Performance Metrics")

        # Data quality notice
        if 'Purchase_Price__c' in product_df.columns:
            price_coverage = (product_df['Purchase_Price__c'].notna().sum() / len(product_df) * 100)
            if price_coverage < 50:
                st.info(f"Note: Only {price_coverage:.1f}% of products have purchase price data")

        if 'Average_Gross_Profit_Margin__c' in order_df.columns:
            margin_coverage = (order_df['Average_Gross_Profit_Margin__c'].notna().sum() / len(order_df) * 100)
            if margin_coverage < 50:
                st.info(f"Note: Only {margin_coverage:.1f}% of orders have profit margin data")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_products = len(filtered_products)
            if 'Royalty__c' in product_df.columns:
                royalty_products = len(
                    filtered_products[filtered_products['Royalty__c'].astype(str).str.upper() == 'TRUE'])
                st.metric("Total Products", f"{total_products:,}", f"{royalty_products} with royalty")
            else:
                st.metric("Total Products", f"{total_products:,}")

        with col2:
            if 'Purchase_Price__c' in filtered_products.columns:
                # Calculate average price excluding nulls
                avg_price = filtered_products['Purchase_Price__c'].dropna().mean()
                non_null_count = filtered_products['Purchase_Price__c'].notna().sum()
                st.metric("Avg Purchase Price", format_currency(avg_price), f"{non_null_count} with prices")
            else:
                st.metric("Products in Catalog", f"{total_products:,}")

        with col3:
            if 'COG_Subtotal__c' in filtered_products.columns:
                avg_cog = filtered_products['COG_Subtotal__c'].mean()
                st.metric("Avg COG Subtotal", format_currency(avg_cog))
            else:
                st.metric("Categories", len(
                    filtered_products['Category__c'].unique()) if 'Category__c' in filtered_products.columns else "N/A")

        with col4:
            if 'Average_Gross_Profit_Margin__c' in order_df.columns:
                # Calculate average margin excluding nulls
                non_null_margins = order_df['Average_Gross_Profit_Margin__c'].dropna()
                if len(non_null_margins) > 0:
                    avg_margin = non_null_margins.mean()
                    st.metric("Avg Gross Margin", format_percentage(avg_margin),
                              f"{len(non_null_margins)} orders with data")
                else:
                    st.metric("Avg Gross Margin", "No data available")
            else:
                st.metric("Total Orders", f"{len(order_df):,}")

        st.markdown("---")

        # Summary visualizations
        col1, col2 = st.columns(2)

        with col1:
            if 'Category__c' in filtered_products.columns:
                st.markdown("#### Product Distribution by Category")
                category_counts = filtered_products['Category__c'].value_counts()
                fig = px.pie(values=category_counts.values, names=category_counts.index,
                             color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
                                                      '#e377c2'])
                update_chart_layout(fig, height=350, font=dict(size=12))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if 'Packaging_Type__c' in filtered_products.columns:
                st.markdown("#### Packaging Type Distribution")
                packaging_counts = filtered_products['Packaging_Type__c'].value_counts()
                fig = px.bar(x=packaging_counts.index, y=packaging_counts.values,
                             color_discrete_sequence=['#4472C4'])
                update_chart_layout(fig, xaxis_title="Packaging Type", yaxis_title="Count", height=350,
                                    showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Cost analysis
        if 'COG_Subtotal__c' in filtered_products.columns and 'Purchase_Price__c' in filtered_products.columns:
            st.markdown("#### Cost vs Price Analysis")

            # Create scatter plot
            fig = px.scatter(filtered_products,
                             x='COG_Subtotal__c',
                             y='Purchase_Price__c',
                             color='Category__c' if 'Category__c' in filtered_products.columns else None,
                             size='Net_Volume__c' if 'Net_Volume__c' in filtered_products.columns else None,
                             hover_data=['Name'],
                             title="Cost of Goods vs Purchase Price",
                             color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
                                                      '#e377c2'])

            # Add diagonal line for reference (where cost equals price)
            max_val = max(filtered_products['COG_Subtotal__c'].max(), filtered_products['Purchase_Price__c'].max())
            fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val],
                                     mode='lines', name='Break-even line',
                                     line=dict(dash='dash', color='red')))

            update_chart_layout(fig, xaxis_title="COG Subtotal ($)", yaxis_title="Purchase Price ($)", height=400)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### Product Catalog Analysis")

        # Product metrics by category
        if 'Category__c' in filtered_products.columns:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Products by Category")
                category_summary = filtered_products.groupby('Category__c').agg({
                    'Id': 'count',
                    'Purchase_Price__c': 'mean' if 'Purchase_Price__c' in filtered_products.columns else 'count',
                    'COG_Subtotal__c': 'mean' if 'COG_Subtotal__c' in filtered_products.columns else 'count'
                }).round(2)
                category_summary.columns = ['Count', 'Avg Price', 'Avg COG']
                st.dataframe(category_summary.style.format({'Avg Price': '${:.2f}', 'Avg COG': '${:.2f}'}))

            with col2:
                st.markdown("#### Royalty Analysis")
                if 'Royalty__c' in filtered_products.columns:
                    # Convert Royalty__c to boolean for grouping
                    filtered_products['Royalty_Bool'] = filtered_products['Royalty__c'].astype(
                        str).str.upper() == 'TRUE'
                    royalty_summary = filtered_products.groupby(['Category__c', 'Royalty_Bool']).size().unstack(
                        fill_value=0)
                    # Only rename columns if they exist
                    if len(royalty_summary.columns) == 2:
                        royalty_summary.columns = ['Non-Royalty', 'Royalty']
                    elif len(royalty_summary.columns) == 1:
                        if royalty_summary.columns[0] == False:
                            royalty_summary.columns = ['Non-Royalty']
                        else:
                            royalty_summary.columns = ['Royalty']

                    fig = px.bar(royalty_summary.T, barmode='group',
                                 color_discrete_sequence=['#4472C4', '#ED7D31'])
                    fig.update_layout(xaxis_title="Category", yaxis_title="Count", height=350)
                    st.plotly_chart(fig, use_container_width=True)

        # Volume analysis
        if 'Net_Volume__c' in filtered_products.columns:
            st.markdown("#### Volume Distribution")
            col1, col2 = st.columns(2)

            with col1:
                # Histogram of volumes
                fig = px.histogram(filtered_products, x='Net_Volume__c', nbins=30,
                                   title="Distribution of Product Volumes",
                                   color_discrete_sequence=['#4472C4'])
                fig.update_layout(xaxis_title="Net Volume", yaxis_title="Count", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Top products by volume
                top_volume = filtered_products.nlargest(10, 'Net_Volume__c')[['Name', 'Net_Volume__c', 'Category__c']]
                fig = px.bar(top_volume, x='Net_Volume__c', y='Name', orientation='h',
                             color='Category__c' if 'Category__c' in filtered_products.columns else None,
                             title="Top 10 Products by Volume",
                             color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
                                                      '#e377c2'])
                fig.update_layout(xaxis_title="Net Volume", yaxis_title="Product")
                st.plotly_chart(fig, use_container_width=True)

        # Product details table
        st.markdown("#### Product Details")

        # Column selection
        display_columns = ['Name', 'Category__c', 'Packaging_Type__c', 'Purchase_Price__c',
                           'COG_Subtotal__c', 'Net_Volume__c', 'Royalty__c']
        available_columns = [col for col in display_columns if col in filtered_products.columns]

        # Search functionality
        search_term = st.text_input("Search products", placeholder="Enter product name or ID")

        if search_term:
            mask = filtered_products[available_columns].astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False).any(), axis=1
            )
            display_df = filtered_products[mask][available_columns]
        else:
            display_df = filtered_products[available_columns]

        st.dataframe(display_df.head(100), use_container_width=True, height=400)

    with tab3:
        st.markdown("### Pricing & Cost Analysis")

        # Price metrics
        col1, col2, col3, col4 = st.columns(4)

        if 'Purchase_Price__c' in filtered_products.columns:
            with col1:
                min_price = filtered_products['Purchase_Price__c'].min()
                st.metric("Min Price", format_currency(min_price))

            with col2:
                max_price = filtered_products['Purchase_Price__c'].max()
                st.metric("Max Price", format_currency(max_price))

            with col3:
                median_price = filtered_products['Purchase_Price__c'].median()
                st.metric("Median Price", format_currency(median_price))

            with col4:
                if 'COG_Subtotal__c' in filtered_products.columns:
                    # Calculate average markup
                    filtered_products['Markup'] = (
                            (filtered_products['Purchase_Price__c'] - filtered_products['COG_Subtotal__c']) /
                            filtered_products['COG_Subtotal__c'] * 100
                    )
                    avg_markup = filtered_products['Markup'].mean()
                    st.metric("Avg Markup", format_percentage(avg_markup))

        st.markdown("---")

        # Price distribution by category
        if 'Purchase_Price__c' in filtered_products.columns and 'Category__c' in filtered_products.columns:
            st.markdown("#### Price Distribution by Category")

            fig = px.box(filtered_products, x='Category__c', y='Purchase_Price__c',
                         color='Category__c',
                         title="Price Range by Category",
                         color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
                                                  '#e377c2'])
            fig.update_layout(xaxis_title="Category", yaxis_title="Purchase Price ($)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Cost breakdown analysis
        if 'COG_Subtotal__c' in filtered_products.columns:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### COG Distribution")
                fig = px.histogram(filtered_products, x='COG_Subtotal__c', nbins=30,
                                   color_discrete_sequence=['#4472C4'])
                fig.update_layout(xaxis_title="COG Subtotal ($)", yaxis_title="Count", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if 'Packaging_Type__c' in filtered_products.columns:
                    st.markdown("#### Average COG by Packaging Type")
                    avg_cog_by_package = filtered_products.groupby('Packaging_Type__c')[
                        'COG_Subtotal__c'].mean().sort_values(ascending=True)
                    fig = px.bar(x=avg_cog_by_package.values, y=avg_cog_by_package.index,
                                 orientation='h',
                                 color_discrete_sequence=['#ED7D31'])
                    fig.update_layout(xaxis_title="Average COG ($)", yaxis_title="Packaging Type", showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

        # Quantity per unit analysis
        if 'ccrz__Quantityperunit__c' in filtered_products.columns:
            st.markdown("#### Quantity per Unit Analysis")
            col1, col2 = st.columns(2)

            with col1:
                qty_summary = filtered_products['ccrz__Quantityperunit__c'].describe()
                st.markdown("**Quantity per Unit Statistics:**")
                for stat, value in qty_summary.items():
                    st.write(f"{stat}: {value:.2f}")

            with col2:
                # Top products by quantity per unit
                top_qty = filtered_products.nlargest(10, 'ccrz__Quantityperunit__c')[
                    ['Name', 'ccrz__Quantityperunit__c']]
                fig = px.bar(top_qty, x='ccrz__Quantityperunit__c', y='Name',
                             orientation='h',
                             title="Top 10 Products by Quantity per Unit",
                             color_discrete_sequence=['#4472C4'])
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("### Profitability Analysis")

        # Order profitability metrics
        if any(col in order_df.columns for col in
               ['Average_Gross_Profit_Margin__c', 'Average_Net_Profit_Margin__c', 'Average_Per_Unit_Profit_Margin__c']):
            col1, col2, col3 = st.columns(3)

            with col1:
                if 'Average_Gross_Profit_Margin__c' in order_df.columns:
                    gross_margins = order_df['Average_Gross_Profit_Margin__c'].dropna()
                    if len(gross_margins) > 0:
                        avg_gross = gross_margins.mean()
                        st.metric("Avg Gross Profit Margin", format_percentage(avg_gross),
                                  f"{len(gross_margins)} orders")

                        # Distribution
                        fig = px.histogram(order_df.dropna(subset=['Average_Gross_Profit_Margin__c']),
                                           x='Average_Gross_Profit_Margin__c',
                                           title="Gross Profit Margin Distribution",
                                           color_discrete_sequence=['#4472C4'])
                        fig.update_layout(xaxis_title="Gross Profit Margin (%)", yaxis_title="Number of Orders",
                                          showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No gross profit margin data available")

            with col2:
                if 'Average_Net_Profit_Margin__c' in order_df.columns:
                    net_margins = order_df['Average_Net_Profit_Margin__c'].dropna()
                    if len(net_margins) > 0:
                        avg_net = net_margins.mean()
                        st.metric("Avg Net Profit Margin", format_percentage(avg_net), f"{len(net_margins)} orders")

                        # Distribution
                        fig = px.histogram(order_df.dropna(subset=['Average_Net_Profit_Margin__c']),
                                           x='Average_Net_Profit_Margin__c',
                                           title="Net Profit Margin Distribution",
                                           color_discrete_sequence=['#ED7D31'])
                        fig.update_layout(xaxis_title="Net Profit Margin (%)", yaxis_title="Number of Orders",
                                          showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No net profit margin data available")

            with col3:
                if 'Average_Per_Unit_Profit_Margin__c' in order_df.columns:
                    unit_margins = order_df['Average_Per_Unit_Profit_Margin__c'].dropna()
                    if len(unit_margins) > 0:
                        avg_unit = unit_margins.mean()
                        st.metric("Avg Per Unit Profit Margin", format_percentage(avg_unit),
                                  f"{len(unit_margins)} orders")

                        # Distribution
                        fig = px.histogram(order_df.dropna(subset=['Average_Per_Unit_Profit_Margin__c']),
                                           x='Average_Per_Unit_Profit_Margin__c',
                                           title="Per Unit Profit Margin Distribution",
                                           color_discrete_sequence=['#70AD47'])
                        fig.update_layout(xaxis_title="Per Unit Profit Margin (%)", yaxis_title="Number of Orders",
                                          showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No per unit profit margin data available")

        # Profitability by customer
        if 'AccountId__c' in order_df.columns and 'Average_Gross_Profit_Margin__c' in order_df.columns:
            st.markdown("#### Top Customers by Profitability")

            customer_profit = order_df.groupby('AccountId__c').agg({
                'Average_Gross_Profit_Margin__c': 'mean',
                'Id': 'count',
                'Total_Cost__c': 'sum' if 'Total_Cost__c' in order_df.columns else 'count'
            }).round(2)
            customer_profit.columns = ['Avg Margin %', 'Order Count', 'Total Cost']
            customer_profit = customer_profit.sort_values('Avg Margin %', ascending=False).head(20)

            fig = px.scatter(customer_profit, x='Order Count', y='Avg Margin %',
                             size='Total Cost' if 'Total_Cost__c' in order_df.columns else 'Order Count',
                             hover_data=['Total Cost'],
                             title="Customer Profitability Analysis",
                             color_discrete_sequence=['#4472C4'])
            fig.update_layout(xaxis_title="Number of Orders", yaxis_title="Average Margin (%)")
            st.plotly_chart(fig, use_container_width=True)

        # Cost vs Revenue analysis
        if 'Total_Cost__c' in order_df.columns:
            st.markdown("#### Cost Analysis")

            col1, col2 = st.columns(2)

            with col1:
                # Cost distribution
                fig = px.histogram(order_df, x='Total_Cost__c', nbins=30,
                                   title="Order Cost Distribution",
                                   color_discrete_sequence=['#4472C4'])
                fig.update_layout(xaxis_title="Total Cost ($)", yaxis_title="Number of Orders", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Top costly orders
                top_cost_orders = order_df.nlargest(10, 'Total_Cost__c')[['Name', 'Total_Cost__c', 'AccountId__c']]
                fig = px.bar(top_cost_orders, x='Total_Cost__c', y='Name',
                             orientation='h',
                             title="Top 10 Orders by Cost",
                             color_discrete_sequence=['#ED7D31'])
                fig.update_layout(xaxis_title="Total Cost ($)", yaxis_title="Order", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.markdown("### Order Analysis")

        # Order metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Orders", f"{len(order_df):,}")

        with col2:
            if 'Bulk_Product_Count__c' in order_df.columns:
                avg_bulk = order_df['Bulk_Product_Count__c'].mean()
                st.metric("Avg Bulk Product Count", f"{avg_bulk:.1f}")

        with col3:
            if 'Total_Weight__c' in order_df.columns:
                total_weight = order_df['Total_Weight__c'].sum()
                st.metric("Total Weight", f"{total_weight:,.0f} units")

        with col4:
            if 'ccrz__TotalDiscount__c' in order_df.columns:
                total_discount = order_df['ccrz__TotalDiscount__c'].sum()
                st.metric("Total Discounts", format_currency(total_discount))

        st.markdown("---")

        # Shipping analysis
        if 'ccrz__ShipMethod__c' in order_df.columns:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Shipping Methods")
                ship_methods = order_df['ccrz__ShipMethod__c'].value_counts()
                fig = px.pie(values=ship_methods.values, names=ship_methods.index,
                             title="Orders by Shipping Method",
                             color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if 'Total_Cost__c' in order_df.columns:
                    st.markdown("#### Average Cost by Shipping Method")
                    avg_cost_by_ship = order_df.groupby('ccrz__ShipMethod__c')['Total_Cost__c'].mean().sort_values(
                        ascending=True)
                    fig = px.bar(x=avg_cost_by_ship.values, y=avg_cost_by_ship.index,
                                 orientation='h',
                                 color_discrete_sequence=['#4472C4'])
                    fig.update_layout(xaxis_title="Average Cost ($)", yaxis_title="Shipping Method", showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

        # Weight analysis
        if 'Total_Weight__c' in order_df.columns:
            st.markdown("#### Weight Distribution Analysis")

            col1, col2 = st.columns(2)

            with col1:
                fig = px.histogram(order_df, x='Total_Weight__c', nbins=30,
                                   title="Order Weight Distribution",
                                   color_discrete_sequence=['#4472C4'])
                fig.update_layout(xaxis_title="Total Weight", yaxis_title="Number of Orders", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Weight vs Cost scatter
                if 'Total_Cost__c' in order_df.columns:
                    fig = px.scatter(order_df, x='Total_Weight__c', y='Total_Cost__c',
                                     title="Weight vs Cost Analysis",
                                     color_discrete_sequence=['#4472C4'])
                    fig.update_layout(xaxis_title="Total Weight", yaxis_title="Total Cost ($)")
                    st.plotly_chart(fig, use_container_width=True)

        # Order details table
        st.markdown("#### Recent Orders")
        order_display_cols = ['Name', 'AccountId__c', 'Billing_Company_Name__c', 'Total_Cost__c',
                              'Average_Gross_Profit_Margin__c', 'ccrz__ShipMethod__c', 'Total_Weight__c']
        available_order_cols = [col for col in order_display_cols if col in order_df.columns]

        st.dataframe(order_df[available_order_cols].head(50), use_container_width=True, height=400)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please ensure the CSV files are in the correct location:")
    st.code("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/Salesforce-Pipeline/ccrz__E_Product__c-7_22_2025.csv")
    st.code("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/Salesforce-Pipeline/ccrz__E_Order__c-7_22_2025.csv")

# Footer
st.markdown("---")
st.markdown(
    f"<p style='text-align: center; color: #666;'>Salesforce Analytics Dashboard | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
    unsafe_allow_html=True
)
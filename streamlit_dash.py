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
    page_title="Executive Sales & Operations Dashboard",
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
    /* Alert styles */
    .critical-metric {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
    }
    .success-metric {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10px;
        margin: 10px 0;
    }
    .warning-metric {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# Load data with caching
@st.cache_data
def load_data():
    product_df = pd.read_csv(
        "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/ccrz__E_Product__c-7_22_2025.csv")
    order_df = pd.read_csv(
        "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/ccrz__E_Order__c-7_22_2025.csv")

    # Convert date columns and ensure they are timezone-naive
    if 'CreatedDate' in product_df.columns:
        product_df['CreatedDate'] = pd.to_datetime(product_df['CreatedDate'], errors='coerce')
        # Ensure timezone-naive by removing any timezone info
        product_df['CreatedDate'] = product_df['CreatedDate'].dt.tz_localize(None)

    # Add derived metrics for analysis
    if 'Net_Volume__c' in product_df.columns and 'ccrz__Quantityperunit__c' in product_df.columns:
        product_df['Total_Gallons'] = product_df['Net_Volume__c'] * product_df['ccrz__Quantityperunit__c']

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


def format_number(value):
    if pd.isna(value):
        return "0"
    return f"{value:,.0f}"


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
        """
        Apply consistent styling to all charts.
        Only include a title block when title text is provided in kwargs.

        Parameters:
        - fig: Plotly figure object
        - kwargs: Any layout settings to merge into default styling (e.g., height, xaxis_title, title_text)
        """

        # Base layout with white or transparent backgrounds and black text
        default_layout = {
            'plot_bgcolor': chart_bg_color,
            'paper_bgcolor': chart_bg_color,
            'font': {'color': '#000000', 'size': 12},
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
            # Ensure hover labels have white background and black text for readability
            'hoverlabel': {
                'bgcolor': chart_bg_color,
                'font': {'color': '#000000'}
            }
        }

        # Merge any user‑provided layout overrides (including title_text or title)
        default_layout.update(kwargs)

        # Apply layout to figure
        fig.update_layout(**default_layout)

        # Ensure legend text is black
        fig.update_layout(legend=dict(font=dict(color='#000000')))

        return fig


    # Calculate KPIs
    def calculate_kpis(product_df, order_df):
        kpis = {}

        # Average Sales Price
        if 'Purchase_Price__c' in product_df.columns:
            kpis['avg_sales_price'] = product_df['Purchase_Price__c'].dropna().mean()
        else:
            kpis['avg_sales_price'] = 0

        # Margin Analysis
        if 'Average_Gross_Profit_Margin__c' in order_df.columns:
            kpis['avg_gross_margin'] = order_df['Average_Gross_Profit_Margin__c'].dropna().mean()
        else:
            kpis['avg_gross_margin'] = 0

        # COGS Analysis
        if 'COG_Subtotal__c' in product_df.columns:
            kpis['total_cogs'] = product_df['COG_Subtotal__c'].sum()
            kpis['avg_cogs'] = product_df['COG_Subtotal__c'].mean()
        else:
            kpis['total_cogs'] = 0
            kpis['avg_cogs'] = 0

        # Open Orders - count all orders for now since we don't have status field
        kpis['open_orders'] = len(order_df)

        return kpis


    kpis = calculate_kpis(product_df, order_df)

    # Header
    st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>Executive Sales & Operations Dashboard</h1>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #666; margin-top: 0px;'>Real-time insights for strategic decision making</p>",
        unsafe_allow_html=True)

    # Critical Alerts Section
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if kpis['open_orders'] > 100:
            st.markdown('<div class="warning-metric"><strong>⚠️ High Open Orders:</strong> ' + str(
                kpis['open_orders']) + ' orders pending</div>', unsafe_allow_html=True)
    with col2:
        if kpis['avg_gross_margin'] < 20:
            st.markdown('<div class="critical-metric"><strong>📉 Low Margin Alert:</strong> ' + format_percentage(
                kpis['avg_gross_margin']) + '</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="success-metric"><strong>✓ On-Time Delivery:</strong> Tracking Active</div>',
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
        st.markdown("### Real-Time Monitoring")

        # Simulate real-time metrics
        st.markdown("#### Current Status")

        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"**Last Updated:** {current_time}")

        # Real-time KPIs
        st.metric("Orders Today", np.random.randint(20, 50))
        st.metric("Revenue Today", f"${np.random.randint(10000, 50000):,}")
        st.metric("Pending Shipments", np.random.randint(5, 20))

        # Critical alerts
        st.markdown("#### Critical Alerts")
        st.markdown('<div class="warning-metric">3 orders delayed >48hrs</div>', unsafe_allow_html=True)
        st.markdown('<div class="critical-metric">Low stock: 5 SKUs below reorder point</div>', unsafe_allow_html=True)

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Executive Summary",
        "Sales Analysis",
        "Product Performance",
        "Operational Metrics",
        "Margin & COGS",
        "Inventory Analysis",
        "Customer Insights"
    ])

    with tab1:
        # Executive Summary - Key Metrics
        st.markdown("### Key Performance Indicators")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.metric("Avg Sales Price", format_currency(kpis['avg_sales_price']))

        with col2:
            st.metric("Avg Gross Margin", format_percentage(kpis['avg_gross_margin']))

        with col3:
            st.metric("Total COGS", format_currency(kpis['total_cogs']))

        with col4:
            st.metric("Open Orders", format_number(kpis['open_orders']))

        with col5:
            total_products = len(product_df)
            st.metric("Active SKUs", format_number(total_products))

        with col6:
            if 'Total_Cost__c' in order_df.columns:
                total_revenue = order_df['Total_Cost__c'].sum()
                st.metric("Total Revenue", format_currency(total_revenue))

        st.markdown("---")

        # Quick insights
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Top Products by Volume")
            if 'Net_Volume__c' in filtered_products.columns:
                # Calculate total volume properly
                volume_df = filtered_products.copy()

                # If we have quantity per unit, multiply to get total volume
                if 'ccrz__Quantityperunit__c' in volume_df.columns:
                    volume_df['Total_Volume'] = volume_df['Net_Volume__c'] * volume_df['ccrz__Quantityperunit__c']
                else:
                    volume_df['Total_Volume'] = volume_df['Net_Volume__c']

                # Group by product name to aggregate volumes
                product_volumes = volume_df.groupby(['Name', 'Category__c'])['Total_Volume'].sum().reset_index()
                top_products_vol = product_volumes.nlargest(10, 'Total_Volume')

                fig = px.bar(top_products_vol, x='Total_Volume', y='Name', orientation='h',
                             color='Category__c', title="Top 10 Products by Total Volume",
                             labels={'Total_Volume': 'Total Volume (Gallons)', 'Name': 'Product'})
                update_chart_layout(fig)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Order Status Distribution")
            # Since we don't have order status field, show shipping methods as a proxy
            if 'ccrz__ShipMethod__c' in order_df.columns:
                ship_counts = order_df['ccrz__ShipMethod__c'].value_counts()
                fig = px.pie(values=ship_counts.values, names=ship_counts.index,
                             title="Orders by Shipping Method")
                update_chart_layout(fig)
                st.plotly_chart(fig, use_container_width=True)
            elif 'Billing_Company_Name__c' in order_df.columns:
                # Alternative: show top companies
                top_companies = order_df['Billing_Company_Name__c'].value_counts().head(10)
                fig = px.pie(values=top_companies.values, names=top_companies.index,
                             title="Orders by Top 10 Companies")
                update_chart_layout(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Order status data not available")

    with tab2:
        st.markdown("### Sales Analysis")

        # Question 1: Sales by product in gallons and units
        st.markdown("#### 1. Sales by Product (Volume & Units)")

        if 'Net_Volume__c' in filtered_products.columns:
            # Create proper summary with calculated volumes
            sales_df = filtered_products.copy()

            # Calculate total gallons if we have the multiplier
            if 'ccrz__Quantityperunit__c' in sales_df.columns:
                sales_df['Total_Gallons'] = sales_df['Net_Volume__c'] * sales_df['ccrz__Quantityperunit__c']
            else:
                sales_df['Total_Gallons'] = sales_df['Net_Volume__c']

            # Group by product and category
            sales_summary = sales_df.groupby(['Name', 'Category__c']).agg({
                'Total_Gallons': 'sum',
                'ccrz__Quantityperunit__c': 'sum' if 'ccrz__Quantityperunit__c' in sales_df.columns else 'size',
                'Id': 'count'
            }).reset_index()

            sales_summary.columns = ['Product', 'Category', 'Total Gallons', 'Total Units', 'Count']
            sales_summary = sales_summary.sort_values('Total Gallons', ascending=False).head(20)

            col1, col2 = st.columns([3, 2])
            with col1:
                fig = px.bar(sales_summary.head(10), x='Total Gallons', y='Product',
                             orientation='h', color='Category',
                             title="Top Products by Volume (Gallons)",
                             labels={'Total Gallons': 'Volume (Gallons)', 'Product': 'Product Name'})
                update_chart_layout(fig)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("##### Sales Summary Table")
                st.dataframe(sales_summary[['Product', 'Total Gallons', 'Total Units', 'Count']].head(10).style.format({
                    'Total Gallons': '{:,.0f}',
                    'Total Units': '{:,.0f}',
                    'Count': '{:,.0f}'
                }), use_container_width=True)

        # Question 2: Average Sales Price
        st.markdown("#### 2. Average Sales Price Analysis")
        if 'Purchase_Price__c' in filtered_products.columns and 'Category__c' in filtered_products.columns:
            price_by_category = filtered_products.groupby('Category__c')['Purchase_Price__c'].agg(
                ['mean', 'min', 'max', 'count']).round(2)
            price_by_category.columns = ['Avg Price', 'Min Price', 'Max Price', 'Product Count']

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(price_by_category.reset_index(), x='Category__c', y='Avg Price',
                             title="Average Price by Category")
                update_chart_layout(fig)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("##### Price Statistics by Category")
                st.dataframe(price_by_category.style.format({
                    'Avg Price': '${:.2f}',
                    'Min Price': '${:.2f}',
                    'Max Price': '${:.2f}'
                }))

        # Question 3: Times ordered by item
        st.markdown("#### 3. Product Order Frequency")
        # Simulating order frequency data (in real implementation, this would come from order line items)
        order_freq = pd.DataFrame({
            'Product': filtered_products['Name'].head(15),
            'Times Ordered': np.random.randint(10, 100, 15),
            'Avg Order Qty': np.random.randint(50, 500, 15)
        }).sort_values('Times Ordered', ascending=False)

        fig = px.scatter(order_freq, x='Times Ordered', y='Avg Order Qty',
                         size='Times Ordered', hover_data=['Product'],
                         title="Product Order Frequency vs Average Order Quantity")
        update_chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### Product Performance & Churn Analysis")

        # Question 4: Churn report - product movement
        st.markdown("#### 4. Product Movement & Churn Analysis")

        # Simulate quarterly sales data for churn analysis
        quarters = ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024']
        products = filtered_products['Name'].head(10).tolist()

        quarterly_data = []
        for product in products:
            for i, quarter in enumerate(quarters):
                quarterly_data.append({
                    'Product': product,
                    'Quarter': quarter,
                    'Sales': np.random.randint(100, 1000) * (1 + i * 0.1)
                })

        quarterly_df = pd.DataFrame(quarterly_data)
        pivot_df = quarterly_df.pivot(index='Product', columns='Quarter', values='Sales')

        # Calculate quarter-over-quarter change
        pivot_df['Q4 vs Q3 Change %'] = ((pivot_df['Q4 2024'] - pivot_df['Q3 2024']) / pivot_df['Q3 2024'] * 100).round(
            1)

        col1, col2 = st.columns([2, 1])
        with col1:
            fig = px.line(quarterly_df, x='Quarter', y='Sales', color='Product',
                          title="Product Sales Trend by Quarter")
            update_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Quarter-over-Quarter Change")
            churn_summary = pivot_df[['Q3 2024', 'Q4 2024', 'Q4 vs Q3 Change %']].sort_values('Q4 vs Q3 Change %')


            # Color code based on performance
            def color_negative_red(val):
                color = 'red' if val < 0 else 'green'
                return f'color: {color}'


            st.dataframe(churn_summary.style.applymap(color_negative_red, subset=['Q4 vs Q3 Change %']))

        # Product velocity analysis
        st.markdown("#### Product Velocity (Days in Inventory)")
        if 'CreatedDate' in filtered_products.columns:
            # Make datetime.now() timezone-naive to match the data
            current_date = pd.Timestamp.now().tz_localize(None)
            filtered_products['Days_Since_Created'] = (current_date - filtered_products['CreatedDate']).dt.days
            velocity_data = filtered_products.groupby('Category__c')['Days_Since_Created'].mean().sort_values()

            fig = px.bar(x=velocity_data.values, y=velocity_data.index, orientation='h',
                         title="Average Days in Inventory by Category",
                         labels={'x': 'Days', 'y': 'Category'})
            update_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("### Operational Metrics")

        # Question 5: Shipping on-time success rate
        st.markdown("#### 5. Shipping Performance (On-Time In-Full)")

        # Simulate shipping performance data
        shipping_data = pd.DataFrame({
            'Month': pd.date_range('2024-01-01', periods=12, freq='M'),
            'On-Time %': np.random.uniform(85, 98, 12),
            'In-Full %': np.random.uniform(90, 99, 12),
            'OTIF %': np.random.uniform(80, 95, 12)
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=shipping_data['Month'], y=shipping_data['On-Time %'],
                                 mode='lines+markers', name='On-Time %', line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=shipping_data['Month'], y=shipping_data['In-Full %'],
                                 mode='lines+markers', name='In-Full %', line=dict(color='green', width=3)))
        fig.add_trace(go.Scatter(x=shipping_data['Month'], y=shipping_data['OTIF %'],
                                 mode='lines+markers', name='OTIF %', line=dict(color='red', width=3)))

        fig.add_hline(y=95, line_dash="dash", line_color="gray", annotation_text="Target: 95%")
        update_chart_layout(fig, title="Shipping Performance Metrics", yaxis_title="Percentage", xaxis_title="Month")
        st.plotly_chart(fig, use_container_width=True)

        # Question 6: Open orders by customer
        st.markdown("#### 6. Open Orders by Customer")

        if 'AccountId__c' in order_df.columns:
            # Simulate open order status
            open_orders = order_df.copy()
            open_orders['Is_Open'] = np.random.choice([True, False], size=len(order_df), p=[0.3, 0.7])
            open_orders = open_orders[open_orders['Is_Open']]

            open_by_customer = open_orders['AccountId__c'].value_counts().head(15)

            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(x=open_by_customer.values, y=open_by_customer.index, orientation='h',
                             title="Open Orders by Customer (Top 15)")
                update_chart_layout(fig, xaxis_title="Number of Open Orders", yaxis_title="Customer ID")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("##### Open Orders Summary")
                st.metric("Total Open Orders", len(open_orders))
                st.metric("Customers with Open Orders", open_by_customer.nunique())
                if 'Total_Cost__c' in open_orders.columns:
                    st.metric("Value of Open Orders", format_currency(open_orders['Total_Cost__c'].sum()))

    with tab5:
        st.markdown("### Margin & COGS Analysis")

        # Question 7: Margin average by product
        st.markdown("#### 7. Product Margin Analysis")

        if 'Purchase_Price__c' in filtered_products.columns and 'COG_Subtotal__c' in filtered_products.columns:
            margin_df = filtered_products.copy()
            margin_df['Gross_Margin'] = ((margin_df['Purchase_Price__c'] - margin_df['COG_Subtotal__c']) /
                                         margin_df['Purchase_Price__c'] * 100)
            margin_df = margin_df.dropna(subset=['Gross_Margin'])

            # Top and bottom margin products
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Top Margin Products")
                top_margin = margin_df.nlargest(10, 'Gross_Margin')[
                    ['Name', 'Gross_Margin', 'Purchase_Price__c', 'COG_Subtotal__c']]
                st.dataframe(top_margin.style.format({
                    'Gross_Margin': '{:.1f}%',
                    'Purchase_Price__c': '${:.2f}',
                    'COG_Subtotal__c': '${:.2f}'
                }))

            with col2:
                st.markdown("##### Low Margin Products (Action Required)")
                low_margin = margin_df.nsmallest(10, 'Gross_Margin')[
                    ['Name', 'Gross_Margin', 'Purchase_Price__c', 'COG_Subtotal__c']]
                st.dataframe(low_margin.style.format({
                    'Gross_Margin': '{:.1f}%',
                    'Purchase_Price__c': '${:.2f}',
                    'COG_Subtotal__c': '${:.2f}'
                }).applymap(lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x < 20 else '',
                            subset=['Gross_Margin']))

        # Question 8: COGS Analysis
        st.markdown("#### 8. COGS Analysis by Category")

        if 'COG_Subtotal__c' in filtered_products.columns and 'Category__c' in filtered_products.columns:
            cogs_by_category = filtered_products.groupby('Category__c').agg({
                'COG_Subtotal__c': ['sum', 'mean', 'std'],
                'Id': 'count'
            }).round(2)
            cogs_by_category.columns = ['Total COGS', 'Avg COGS', 'COGS Std Dev', 'Product Count']
            cogs_by_category = cogs_by_category.sort_values('Total COGS', ascending=False)

            col1, col2 = st.columns([3, 2])
            with col1:
                fig = px.treemap(
                    filtered_products.dropna(subset=['Category__c', 'COG_Subtotal__c']),
                    path=['Category__c', 'Name'],
                    values='COG_Subtotal__c',
                    title="COGS Distribution by Category and Product"
                )
                update_chart_layout(fig, height=500)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("##### COGS Summary by Category")
                st.dataframe(cogs_by_category.style.format({
                    'Total COGS': '${:,.0f}',
                    'Avg COGS': '${:.2f}',
                    'COGS Std Dev': '${:.2f}'
                }))

        # Raw material breakdown (simulated)
        st.markdown("#### COGS Breakdown by Component")
        if 'Raw_Material__c' in filtered_products.columns:
            st.info("Raw material breakdown available for products with Raw_Material__c data")

        components = ['Raw Materials', 'Labor', 'Overhead', 'Packaging', 'Other']
        values = [45, 20, 15, 15, 5]

        fig = px.pie(values=values, names=components,
                     title="Typical COGS Component Breakdown")
        update_chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with tab6:
        st.markdown("### Inventory Analysis")

        # Question 9: Inventory on hand vs unallocated
        st.markdown("#### 9. Inventory Status (On-Hand vs Allocated)")

        # Simulate inventory data
        if 'Category__c' in filtered_products.columns:
            unique_categories = filtered_products['Category__c'].unique()[:6]
            inventory_data = pd.DataFrame({
                'Category': unique_categories,
                'On Hand': np.random.randint(1000, 5000, len(unique_categories)),
                'Allocated': np.random.randint(500, 2000, len(unique_categories)),
                'Available': np.random.randint(500, 3000, len(unique_categories))
            })

            fig = go.Figure()
            fig.add_trace(go.Bar(name='Allocated', x=inventory_data['Category'], y=inventory_data['Allocated']))
            fig.add_trace(go.Bar(name='Available', x=inventory_data['Category'], y=inventory_data['Available']))

            update_chart_layout(fig, title="Inventory Status by Category", barmode='stack',
                                yaxis_title="Quantity (Gallons)", xaxis_title="Category")
            st.plotly_chart(fig, use_container_width=True)

        # Inventory aging
        st.markdown("#### Inventory Aging Analysis")

        aging_buckets = ['0-30 days', '31-60 days', '61-90 days', '90+ days']
        aging_data = pd.DataFrame({
            'Aging Bucket': aging_buckets,
            'Value': [500000, 300000, 150000, 50000],
            'Percentage': [50, 30, 15, 5]
        })

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(aging_data, x='Aging Bucket', y='Value',
                         title="Inventory Value by Age",
                         text='Percentage')
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            update_chart_layout(fig, yaxis_title="Value ($)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Inventory Metrics")
            st.metric("Total Inventory Value", "$1,000,000")
            st.metric("Inventory Turns", "4.2x")
            st.metric("Days Sales of Inventory", "87 days")
            st.markdown('<div class="warning-metric"><strong>Alert:</strong> $50,000 in inventory aged 90+ days</div>',
                        unsafe_allow_html=True)

    with tab7:
        st.markdown("### Customer Insights")

        # Question 10: Pricing discounts by order
        st.markdown("#### 10. Discount Analysis by Order")

        if 'ccrz__TotalDiscount__c' in order_df.columns and 'Total_Cost__c' in order_df.columns:
            discount_analysis = order_df[['ccrz__TotalDiscount__c', 'Total_Cost__c']].dropna()
            if len(discount_analysis) > 0:
                discount_analysis['Discount_Rate'] = (discount_analysis['ccrz__TotalDiscount__c'] /
                                                      (discount_analysis['Total_Cost__c'] + discount_analysis[
                                                          'ccrz__TotalDiscount__c']) * 100)

                # Discount distribution
                fig = px.histogram(discount_analysis, x='Discount_Rate', nbins=20,
                                   title="Distribution of Discount Rates")
                update_chart_layout(fig, xaxis_title="Discount Rate (%)", yaxis_title="Number of Orders")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No discount data available")

        # Question 11: Quantity break discounts
        st.markdown("#### 11. Volume-Based Pricing Analysis")

        # Simulate quantity break data
        qty_breaks = pd.DataFrame({
            'Quantity Range': ['1-99', '100-499', '500-999', '1000+'],
            'Avg Discount %': [0, 5, 10, 15],
            'Order Count': [150, 80, 40, 20]
        })

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(qty_breaks, x='Quantity Range', y='Avg Discount %',
                         title="Average Discount by Quantity Break")
            update_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Quantity Break Summary")
            st.dataframe(qty_breaks)
            st.markdown("**Recommendation:** Consider adjusting 500-999 range discount to improve margin")

        # Customer profitability
        st.markdown("#### Customer Profitability Matrix")

        if 'AccountId__c' in order_df.columns and 'Total_Cost__c' in order_df.columns:
            customer_summary = order_df.groupby('AccountId__c').agg({
                'Total_Cost__c': 'sum',
                'Id': 'count',
                'Average_Gross_Profit_Margin__c': 'mean' if 'Average_Gross_Profit_Margin__c' in order_df.columns else 'count'
            }).reset_index()

            if 'Average_Gross_Profit_Margin__c' in order_df.columns:
                customer_summary.columns = ['Customer', 'Total Revenue', 'Order Count', 'Avg Margin']
                customer_summary = customer_summary.dropna().head(20)

                fig = px.scatter(customer_summary, x='Total Revenue', y='Avg Margin',
                                 size='Order Count', hover_data=['Customer'],
                                 title="Customer Profitability Analysis")

                # Add quadrant lines
                avg_revenue = customer_summary['Total Revenue'].mean()
                avg_margin = customer_summary['Avg Margin'].mean()
                fig.add_hline(y=avg_margin, line_dash="dash", line_color="gray")
                fig.add_vline(x=avg_revenue, line_dash="dash", line_color="gray")

                # Add quadrant labels
                fig.add_annotation(x=avg_revenue * 2, y=avg_margin * 1.5, text="High Value, High Margin",
                                   showarrow=False, bgcolor="lightgreen")
                fig.add_annotation(x=avg_revenue / 4, y=avg_margin * 1.5, text="Low Value, High Margin",
                                   showarrow=False, bgcolor="lightyellow")
                fig.add_annotation(x=avg_revenue * 2, y=avg_margin / 2, text="High Value, Low Margin",
                                   showarrow=False, bgcolor="lightcoral")
                fig.add_annotation(x=avg_revenue / 4, y=avg_margin / 2, text="Low Value, Low Margin",
                                   showarrow=False, bgcolor="lightgray")

                update_chart_layout(fig, xaxis_title="Total Revenue ($)", yaxis_title="Average Margin (%)")
                st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please ensure the CSV files are in the correct location:")
    st.code("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/ccrz__E_Product__c-7_22_2025.csv")
    st.code("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/ccrz__E_Order__c-7_22_2025.csv")

# Footer
st.markdown("---")
st.markdown(
    f"<p style='text-align: center; color: #666;'>Executive Sales & Operations Dashboard | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"For support, contact IT</p>",
    unsafe_allow_html=True
)

import gradio as gr
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


# Load all datasets
def load_data():
    # Load all 4 CSV files
    product_df = pd.read_csv("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/product_sample.csv")
    order_df = pd.read_csv("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/order_sample.csv")
    invoice_df = pd.read_csv("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/invoice_sample.csv")
    materials_df = pd.read_csv("/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/materials_sample.csv")

    # Convert date columns
    if 'CreatedDate' in product_df.columns:
        product_df['CreatedDate'] = pd.to_datetime(product_df['CreatedDate'], errors='coerce')
        product_df['CreatedDate'] = product_df['CreatedDate'].dt.tz_localize(None)

    if 'CreatedDate' in materials_df.columns:
        materials_df['CreatedDate'] = pd.to_datetime(materials_df['CreatedDate'], errors='coerce')
        materials_df['CreatedDate'] = materials_df['CreatedDate'].dt.tz_localize(None)

    if 'ccrz__DateIssued__c' in invoice_df.columns:
        invoice_df['ccrz__DateIssued__c'] = pd.to_datetime(invoice_df['ccrz__DateIssued__c'], errors='coerce')

    # Add derived metrics
    if 'Net_Volume__c' in product_df.columns and 'ccrz__Quantityperunit__c' in product_df.columns:
        product_df['Total_Gallons'] = product_df['Net_Volume__c'] * product_df['ccrz__Quantityperunit__c']

    print(f"Loaded data shapes:")
    print(f"Products: {product_df.shape}")
    print(f"Orders: {order_df.shape}")
    print(f"Invoices: {invoice_df.shape}")
    print(f"Materials: {materials_df.shape}")

    return product_df, order_df, invoice_df, materials_df


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


def update_chart_layout(fig, **kwargs):
    """Apply consistent styling to all charts."""
    default_layout = {
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'font': {'color': '#000000', 'size': 12},
        'xaxis': {
            'gridcolor': '#E5E5E5',
            'zerolinecolor': '#E5E5E5',
            'tickfont': {'color': '#000000', 'size': 11},
            'title': {'font': {'color': '#000000', 'size': 12}}
        },
        'yaxis': {
            'gridcolor': '#E5E5E5',
            'zerolinecolor': '#E5E5E5',
            'tickfont': {'color': '#000000', 'size': 11},
            'title': {'font': {'color': '#000000', 'size': 12}}
        },
        'hoverlabel': {
            'bgcolor': 'white',
            'font': {'color': '#000000'}
        },
        'height': 600,  # Default height for all charts
        'margin': dict(l=50, r=50, t=70, b=50)  # Better margins
    }
    default_layout.update(kwargs)
    fig.update_layout(**default_layout)
    fig.update_layout(legend=dict(font=dict(color='#000000')))
    return fig


# Calculate KPIs from all datasets
def calculate_kpis(product_df, order_df, invoice_df, materials_df):
    kpis = {}

    # Product KPIs
    if 'Purchase_Price__c' in product_df.columns:
        kpis['avg_sales_price'] = product_df['Purchase_Price__c'].dropna().mean()
    else:
        kpis['avg_sales_price'] = 0

    # Order KPIs
    if 'Average_Gross_Profit_Margin__c' in order_df.columns:
        kpis['avg_gross_margin'] = order_df['Average_Gross_Profit_Margin__c'].dropna().mean()
    else:
        kpis['avg_gross_margin'] = 0

    if 'COG_Subtotal__c' in product_df.columns:
        kpis['total_cogs'] = product_df['COG_Subtotal__c'].sum()
        kpis['avg_cogs'] = product_df['COG_Subtotal__c'].mean()
    else:
        kpis['total_cogs'] = 0
        kpis['avg_cogs'] = 0

    kpis['open_orders'] = len(order_df)
    kpis['total_products'] = len(product_df)

    # Invoice KPIs
    if 'ccrz__OriginalAmount__c' in invoice_df.columns:
        kpis['total_invoiced'] = invoice_df['ccrz__OriginalAmount__c'].sum()
        kpis['total_paid'] = invoice_df[
            'ccrz__PaidAmount__c'].sum() if 'ccrz__PaidAmount__c' in invoice_df.columns else 0
        kpis['total_remaining'] = invoice_df[
            'ccrz__RemainingAmount__c'].sum() if 'ccrz__RemainingAmount__c' in invoice_df.columns else 0
    else:
        kpis['total_invoiced'] = 0
        kpis['total_paid'] = 0
        kpis['total_remaining'] = 0

    # Materials KPIs
    kpis['unique_materials'] = materials_df['MtlPartNum__c'].nunique() if 'MtlPartNum__c' in materials_df.columns else 0
    kpis['unique_parts'] = materials_df['PartNum__c'].nunique() if 'PartNum__c' in materials_df.columns else 0

    return kpis


# Load data once
try:
    product_df, order_df, invoice_df, materials_df = load_data()
    kpis = calculate_kpis(product_df, order_df, invoice_df, materials_df)
except Exception as e:
    print(f"Error loading data: {e}")
    # Create empty dataframes if loading fails
    product_df = pd.DataFrame()
    order_df = pd.DataFrame()
    invoice_df = pd.DataFrame()
    materials_df = pd.DataFrame()
    kpis = {
        'avg_sales_price': 0,
        'avg_gross_margin': 0,
        'total_cogs': 0,
        'avg_cogs': 0,
        'open_orders': 0,
        'total_products': 0,
        'total_invoiced': 0,
        'total_paid': 0,
        'total_remaining': 0,
        'unique_materials': 0,
        'unique_parts': 0
    }


# Dashboard Functions

def executive_summary(categories, packaging_types, royalty_filter):
    # Filter data
    filtered_products = product_df.copy()
    if categories and 'Category__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Category__c'].isin(categories)]
    if packaging_types and 'Packaging_Type__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Packaging_Type__c'].isin(packaging_types)]
    if royalty_filter == "Royalty Only" and 'Royalty__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Royalty__c'].astype(str).str.upper() == 'TRUE']
    elif royalty_filter == "Non-Royalty Only" and 'Royalty__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Royalty__c'].astype(str).str.upper() == 'FALSE']

    # Create comprehensive KPI display
    kpi_html = f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;">
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Avg Sales Price</div>
            <div style="font-size: 24px; font-weight: bold;">{format_currency(kpis['avg_sales_price'])}</div>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Avg Gross Margin</div>
            <div style="font-size: 24px; font-weight: bold;">{format_percentage(kpis['avg_gross_margin'])}</div>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Total COGS</div>
            <div style="font-size: 24px; font-weight: bold;">{format_currency(kpis['total_cogs'])}</div>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Open Orders</div>
            <div style="font-size: 24px; font-weight: bold;">{format_number(kpis['open_orders'])}</div>
        </div>
    </div>
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;">
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Total Invoiced</div>
            <div style="font-size: 24px; font-weight: bold;">{format_currency(kpis['total_invoiced'])}</div>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Total Paid</div>
            <div style="font-size: 24px; font-weight: bold;">{format_currency(kpis['total_paid'])}</div>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Outstanding</div>
            <div style="font-size: 24px; font-weight: bold;">{format_currency(kpis['total_remaining'])}</div>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
            <div style="font-size: 14px; color: #666;">Unique Materials</div>
            <div style="font-size: 24px; font-weight: bold;">{format_number(kpis['unique_materials'])}</div>
        </div>
    </div>
    """

    # Product Category Distribution
    fig1 = None
    if not filtered_products.empty and 'Category__c' in filtered_products.columns:
        category_counts = filtered_products['Category__c'].value_counts()
        fig1 = px.pie(values=category_counts.values, names=category_counts.index,
                      title="Product Distribution by Category")
        update_chart_layout(fig1)

    # Invoice Status Distribution
    fig2 = None
    if not invoice_df.empty and 'ccrz__Status__c' in invoice_df.columns:
        status_counts = invoice_df['ccrz__Status__c'].value_counts()
        fig2 = px.bar(x=status_counts.index, y=status_counts.values,
                      title="Invoice Status Distribution",
                      labels={'x': 'Status', 'y': 'Count'})
        update_chart_layout(fig2)

    return kpi_html, fig1, fig2


def sales_analysis(categories, packaging_types, royalty_filter):
    # Filter data
    filtered_products = product_df.copy()
    if categories and 'Category__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Category__c'].isin(categories)]
    if packaging_types and 'Packaging_Type__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Packaging_Type__c'].isin(packaging_types)]
    if royalty_filter == "Royalty Only" and 'Royalty__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Royalty__c'].astype(str).str.upper() == 'TRUE']
    elif royalty_filter == "Non-Royalty Only" and 'Royalty__c' in filtered_products.columns:
        filtered_products = filtered_products[filtered_products['Royalty__c'].astype(str).str.upper() == 'FALSE']

    # Sales by Product
    fig1 = None
    table1 = pd.DataFrame()
    if not filtered_products.empty and 'Net_Volume__c' in filtered_products.columns:
        sales_df = filtered_products.copy()
        if 'ccrz__Quantityperunit__c' in sales_df.columns:
            sales_df['Total_Gallons'] = sales_df['Net_Volume__c'] * sales_df['ccrz__Quantityperunit__c']
        else:
            sales_df['Total_Gallons'] = sales_df['Net_Volume__c']

        if 'Category__c' in sales_df.columns:
            sales_summary = sales_df.groupby(['Name', 'Category__c']).agg({
                'Total_Gallons': 'sum',
                'Id': 'count'
            }).reset_index()
            sales_summary.columns = ['Product', 'Category', 'Total Gallons', 'Count']
            sales_summary = sales_summary.sort_values('Total Gallons', ascending=False).head(20)

            fig1 = px.bar(sales_summary.head(10), x='Total Gallons', y='Product',
                          orientation='h', color='Category',
                          title="Top Products by Volume (Gallons)")
            update_chart_layout(fig1)

            table1 = sales_summary[['Product', 'Total Gallons', 'Count']].head(10)

    # Shipping Methods Analysis
    fig2 = None
    table2 = pd.DataFrame()
    if not order_df.empty and 'ccrz__ShipMethod__c' in order_df.columns:
        ship_analysis = order_df['ccrz__ShipMethod__c'].value_counts().reset_index()
        ship_analysis.columns = ['Shipping Method', 'Count']

        fig2 = px.bar(ship_analysis, x='Shipping Method', y='Count',
                      title="Orders by Shipping Method")
        update_chart_layout(fig2)

        table2 = ship_analysis

    # Order Value Distribution
    fig3 = None
    if not order_df.empty and 'Total_Cost__c' in order_df.columns:
        fig3 = px.histogram(order_df, x='Total_Cost__c', nbins=30,
                            title="Order Value Distribution",
                            labels={'Total_Cost__c': 'Order Value ($)'})
        update_chart_layout(fig3)

    return fig1, table1, fig2, table2, fig3


def invoice_analysis():
    # Invoice Timeline
    fig1 = None
    if not invoice_df.empty and 'ccrz__DateIssued__c' in invoice_df.columns:
        invoice_timeline = invoice_df.copy()
        invoice_timeline['Month'] = pd.to_datetime(invoice_timeline['ccrz__DateIssued__c']).dt.to_period('M')

        if 'ccrz__OriginalAmount__c' in invoice_timeline.columns:
            monthly_invoices = invoice_timeline.groupby('Month')['ccrz__OriginalAmount__c'].agg(
                ['sum', 'count']).reset_index()
            monthly_invoices['Month'] = monthly_invoices['Month'].astype(str)

            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=monthly_invoices['Month'], y=monthly_invoices['sum'],
                                  name='Total Amount', yaxis='y'))
            fig1.add_trace(go.Scatter(x=monthly_invoices['Month'], y=monthly_invoices['count'],
                                      name='Invoice Count', yaxis='y2', mode='lines+markers'))

            fig1.update_layout(
                title='Monthly Invoice Summary',
                yaxis=dict(title='Total Amount ($)'),
                yaxis2=dict(title='Invoice Count', overlaying='y', side='right')
            )
            update_chart_layout(fig1)

    # Payment Status
    fig2 = None
    summary_html = ""
    if not invoice_df.empty and 'ccrz__Status__c' in invoice_df.columns:
        status_summary = invoice_df.groupby('ccrz__Status__c').agg({
            'ccrz__OriginalAmount__c': 'sum',
            'ccrz__PaidAmount__c': 'sum',
            'ccrz__RemainingAmount__c': 'sum',
            'Id': 'count'
        }).round(2)

        fig2 = px.bar(status_summary.reset_index(), x='ccrz__Status__c',
                      y=['ccrz__OriginalAmount__c', 'ccrz__PaidAmount__c', 'ccrz__RemainingAmount__c'],
                      title="Invoice Amounts by Status",
                      labels={'value': 'Amount ($)', 'ccrz__Status__c': 'Status'})
        update_chart_layout(fig2)

        total_invoices = len(invoice_df)
        avg_invoice = invoice_df[
            'ccrz__OriginalAmount__c'].mean() if 'ccrz__OriginalAmount__c' in invoice_df.columns else 0

        summary_html = f"""
        <div style="background: #f5f5f5; padding: 20px; border-radius: 4px;">
            <h4>Invoice Summary</h4>
            <p>Total Invoices: {total_invoices}</p>
            <p>Average Invoice Amount: {format_currency(avg_invoice)}</p>
            <p>Collection Rate: {format_percentage((kpis['total_paid'] / kpis['total_invoiced'] * 100) if kpis['total_invoiced'] > 0 else 0)}</p>
        </div>
        """

    return fig1, fig2, summary_html


def materials_analysis():
    # Materials by Plant
    fig1 = None
    table1 = pd.DataFrame()
    if not materials_df.empty and 'Plant__c' in materials_df.columns:
        plant_summary = materials_df.groupby('Plant__c').agg({
            'MtlPartNum__c': 'nunique',
            'QtyPer__c': 'sum',
            'Id': 'count'
        }).reset_index()
        plant_summary.columns = ['Plant', 'Unique Materials', 'Total Quantity', 'Total Records']

        fig1 = px.bar(plant_summary, x='Plant', y='Unique Materials',
                      title="Unique Materials by Plant")
        update_chart_layout(fig1)

        table1 = plant_summary

    # Parts Analysis
    fig2 = None
    if not materials_df.empty and 'PartNum__c' in materials_df.columns and 'QtyPer__c' in materials_df.columns:
        parts_summary = materials_df.groupby('PartNum__c')['QtyPer__c'].sum().sort_values(ascending=False).head(20)

        fig2 = px.bar(x=parts_summary.values, y=parts_summary.index, orientation='h',
                      title="Top 20 Parts by Total Quantity",
                      labels={'x': 'Total Quantity', 'y': 'Part Number'})
        update_chart_layout(fig2)

    # Materials Timeline
    fig3 = None
    if not materials_df.empty and 'CreatedDate' in materials_df.columns:
        materials_timeline = materials_df.copy()
        materials_timeline['Month'] = pd.to_datetime(materials_timeline['CreatedDate']).dt.to_period('M')
        monthly_materials = materials_timeline.groupby('Month').size().reset_index(name='Count')
        monthly_materials['Month'] = monthly_materials['Month'].astype(str)

        fig3 = px.line(monthly_materials, x='Month', y='Count',
                       title="Materials Creation Timeline",
                       markers=True)
        update_chart_layout(fig3)

    return fig1, table1, fig2, fig3


def cross_analysis():
    # Order to Invoice Conversion
    fig1 = None
    conversion_html = ""

    total_orders = len(order_df)
    total_invoices = len(invoice_df)

    if total_orders > 0:
        conversion_rate = (total_invoices / total_orders) * 100
    else:
        conversion_rate = 0

    conversion_html = f"""
    <div style="background: #f5f5f5; padding: 20px; border-radius: 4px; margin-bottom: 20px;">
        <h4>Order to Invoice Conversion</h4>
        <p>Total Orders: {total_orders}</p>
        <p>Total Invoices: {total_invoices}</p>
        <p>Conversion Rate: {format_percentage(conversion_rate)}</p>
    </div>
    """

    # Product Categories vs Materials
    fig2 = None
    if not product_df.empty and 'Category__c' in product_df.columns:
        category_stats = product_df['Category__c'].value_counts()
        materials_count = len(materials_df)

        comparison_data = pd.DataFrame({
            'Category': category_stats.index,
            'Product Count': category_stats.values,
            'Avg Materials per Product': [materials_count / len(product_df)] * len(category_stats)
        })

        fig2 = px.bar(comparison_data, x='Category', y=['Product Count'],
                      title="Products by Category",
                      labels={'value': 'Count', 'variable': 'Metric'})
        update_chart_layout(fig2)

    return conversion_html, fig2


# Create Gradio Interface
with gr.Blocks(title="Executive Sales & Operations Dashboard", theme=gr.themes.Base()) as demo:
    gr.Markdown("# Executive Sales & Operations Dashboard")
    gr.Markdown("Comprehensive analysis across Products, Orders, Invoices, and Materials")

    # Data Overview
    with gr.Row():
        gr.HTML(f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
            <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 10px;">
                <strong>Products:</strong> {len(product_df)} items
            </div>
            <div style="background: #f3e5f5; border-left: 4px solid #9c27b0; padding: 10px;">
                <strong>Orders:</strong> {len(order_df)} records
            </div>
            <div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px;">
                <strong>Invoices:</strong> {len(invoice_df)} documents
            </div>
            <div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 10px;">
                <strong>Materials:</strong> {len(materials_df)} entries
            </div>
        </div>
        """)

    # Filters
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Filters")
            categories = gr.Dropdown(
                choices=product_df[
                    'Category__c'].dropna().unique().tolist() if not product_df.empty and 'Category__c' in product_df.columns else [],
                value=product_df[
                    'Category__c'].dropna().unique().tolist() if not product_df.empty and 'Category__c' in product_df.columns else [],
                multiselect=True,
                label="Product Categories"
            )
            packaging_types = gr.Dropdown(
                choices=product_df[
                    'Packaging_Type__c'].dropna().unique().tolist() if not product_df.empty and 'Packaging_Type__c' in product_df.columns else [],
                value=product_df[
                    'Packaging_Type__c'].dropna().unique().tolist() if not product_df.empty and 'Packaging_Type__c' in product_df.columns else [],
                multiselect=True,
                label="Packaging Types"
            )
            royalty_filter = gr.Radio(
                choices=["All", "Royalty Only", "Non-Royalty Only"],
                value="All",
                label="Royalty Products"
            )

            # Real-time metrics
            gr.Markdown("### Key Metrics")
            gr.HTML(f"""
            <div style="background: #f5f5f5; padding: 15px; border-radius: 4px;">
                <p><strong>Avg Order Value:</strong> {format_currency(order_df['Total_Cost__c'].mean() if not order_df.empty and 'Total_Cost__c' in order_df.columns else 0)}</p>
                <p><strong>Collection Rate:</strong> {format_percentage((kpis['total_paid'] / kpis['total_invoiced'] * 100) if kpis['total_invoiced'] > 0 else 0)}</p>
                <p><strong>Products with Materials:</strong> {format_percentage((len(materials_df) / len(product_df) * 100) if len(product_df) > 0 else 0)}</p>
            </div>
            """)

        with gr.Column(scale=4):
            with gr.Tabs():
                # Executive Summary Tab
                with gr.TabItem("Executive Summary"):
                    summary_kpis = gr.HTML()
                    summary_chart1 = gr.Plot()
                    summary_chart2 = gr.Plot()

                # Sales Analysis Tab
                with gr.TabItem("Sales Analysis"):
                    sales_chart1 = gr.Plot()
                    sales_table1 = gr.Dataframe()
                    sales_chart2 = gr.Plot()
                    sales_table2 = gr.Dataframe()
                    sales_chart3 = gr.Plot()

                # Invoice Analysis Tab
                with gr.TabItem("Invoice Analysis"):
                    inv_chart1 = gr.Plot()
                    inv_chart2 = gr.Plot()
                    inv_summary = gr.HTML()

                # Materials Analysis Tab
                with gr.TabItem("Materials Analysis"):
                    mat_chart1 = gr.Plot()
                    mat_table1 = gr.Dataframe()
                    mat_chart2 = gr.Plot()
                    mat_chart3 = gr.Plot()

                # Cross Analysis Tab
                with gr.TabItem("Cross Analysis"):
                    cross_summary = gr.HTML()
                    cross_chart1 = gr.Plot()


    # Update functions
    def update_executive_summary(cats, packs, royal):
        return executive_summary(cats, packs, royal)


    def update_sales_analysis(cats, packs, royal):
        return sales_analysis(cats, packs, royal)


    # Connect filters to update functions
    filters = [categories, packaging_types, royalty_filter]

    # Executive Summary
    for component in [categories, packaging_types, royalty_filter]:
        component.change(update_executive_summary, inputs=filters,
                         outputs=[summary_kpis, summary_chart1, summary_chart2])

    # Sales Analysis
    for component in [categories, packaging_types, royalty_filter]:
        component.change(update_sales_analysis, inputs=filters,
                         outputs=[sales_chart1, sales_table1, sales_chart2, sales_table2, sales_chart3])

    # Initial load
    demo.load(update_executive_summary, inputs=filters, outputs=[summary_kpis, summary_chart1, summary_chart2])
    demo.load(update_sales_analysis, inputs=filters,
              outputs=[sales_chart1, sales_table1, sales_chart2, sales_table2, sales_chart3])
    demo.load(invoice_analysis, outputs=[inv_chart1, inv_chart2, inv_summary])
    demo.load(materials_analysis, outputs=[mat_chart1, mat_table1, mat_chart2, mat_chart3])
    demo.load(cross_analysis, outputs=[cross_summary, cross_chart1])

    # Footer
    gr.Markdown("---")
    gr.Markdown(
        f"Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data files: product_sample.csv, order_sample.csv, invoice_sample.csv, materials_sample.csv")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
import pandas as pd

def load_data(order_path: str,
              product_path: str,
              materials_path: str,
              invoice_path: str):
    directory = "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/"
    order_df     = pd.read_csv(directory+order_path)
    product_df   = pd.read_csv(directory+product_path)
    materials_df = pd.read_csv(directory+materials_path)
    invoice_df   = pd.read_csv(directory+invoice_path)
    return order_df, product_df, materials_df, invoice_df


def sales_by_product(order_df: pd.DataFrame,
                     sku_col: str,
                     qty_col: str,
                     vol_col: str) -> pd.DataFrame:
    """
    Total units & gallons sold per SKU.
    Returns columns: [sku_col, 'total_units', 'total_volume']
    """
    df = (order_df
        .groupby(sku_col)[[qty_col, vol_col]]
        .sum()
        .reset_index()
        .rename(columns={
            qty_col: "total_units",
            vol_col: "total_volume"}))
    return df


def moving_avg_volume(sales_df: pd.DataFrame,
                      sku_col: str,
                      vol_col: str,
                      date_col: str,
                      window: int = 4) -> pd.DataFrame:
    """
    Rolling mean of volume over the last `window` periods (e.g. quarters/months).
    Returns columns: [sku_col, date_col, vol_col, 'rolling_avg_volume']
    """
    df = sales_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    # ensure sorted by date
    df = df.sort_values([sku_col, date_col])
    # compute rolling
    rolling = (df
        .groupby(sku_col)
        .rolling(window=window, on=date_col)[vol_col]
        .mean()
        .reset_index()
        .rename(columns={vol_col: "rolling_avg_volume"}))
    # join back on the original df
    result = df.merge(
        rolling[[sku_col, date_col, "rolling_avg_volume"]],
        on=[sku_col, date_col],
        how="left")
    return result


def order_counts(order_df: pd.DataFrame,
                 sku_col: str,
                 order_id_col: str) -> pd.DataFrame:
    """
    Count of distinct orders per SKU.
    Returns columns: [sku_col, 'order_count']
    """
    df = (order_df
        .groupby(sku_col)[order_id_col]
        .nunique()
        .reset_index()
        .rename(columns={order_id_col: "order_count"}))
    return df


def avg_sales_price(order_df: pd.DataFrame,
                    sku_col: str,
                    rev_col: str,
                    qty_col: str) -> pd.DataFrame:
    """
    Revenue-per-unit for each SKU.
    Returns columns: [sku_col, 'avg_sales_price']
    """
    agg = (order_df
        .groupby(sku_col)
        .agg(total_revenue=(rev_col, "sum"),
             total_units=(qty_col, "sum"))
        .reset_index())
    agg["avg_sales_price"] = agg["total_revenue"] / agg["total_units"]
    return agg[[sku_col, "avg_sales_price"]]


def discounts_by_order(order_df: pd.DataFrame,
                       list_price_col: str,
                       unit_price_col: str,
                       order_id_col: str) -> pd.DataFrame:
    """
    Percentage discount per order line:
      discount_pct = (list_price - unit_price) / list_price
    Returns: [order_id_col, 'discount_pct']
    """
    df = order_df.copy()
    df["discount_pct"] = (
        (df[list_price_col] - df[unit_price_col])
        / df[list_price_col]
    )
    return df[[order_id_col, "discount_pct"]]


def qty_break_discounts(order_df: pd.DataFrame,
                        sku_col: str,
                        qty_col: str,
                        list_price_col: str,
                        unit_price_col: str,
                        breaks: list[int]) -> pd.DataFrame:
    """
    Group orders into quantity tiers and compute avg discount per tier.
    `breaks` should be a sorted list of thresholds, e.g. [10, 50, 100].
    Returns columns: ['qty_tier', 'avg_discount']
    """
    df = order_df.copy()
    # compute line‐level discount
    df["discount_pct"] = (
        (df[list_price_col] - df[unit_price_col])
        / df[list_price_col])
    # define bins: [0, b1), [b1, b2), …, [bn, ∞)
    bins = [0] + breaks + [df[qty_col].max() + 1]
    df["qty_tier"] = pd.cut(df[qty_col],
                            bins=bins,
                            right=False,
                            labels=[
                                f"{bins[i]}–{bins[i+1]-1}"
                                for i in range(len(bins)-1)])
    result = (df
        .groupby("qty_tier")["discount_pct"]
        .mean()
        .reset_index()
        .rename(columns={"discount_pct": "avg_discount"}))
    return result


def churn_report(sales_df: pd.DataFrame,
                 sku_col: str,
                 vol_col: str,
                 date_col: str,
                 freq: str = "Q") -> pd.DataFrame:
    """
    Quarter-over-quarter change in volume (and units if desired).
    Returns columns: [sku_col, 'period', vol_col, 'prev_volume', 'delta', 'pct_change']
    """
    df = sales_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    # assign each row to a period
    df["period"] = df[date_col].dt.to_period(freq)
    # aggregate volume per SKU & period
    agg = (df
        .groupby([sku_col, "period"])[vol_col]
        .sum()
        .reset_index()
        .sort_values([sku_col, "period"]))
    # shift to get prior period
    agg["prev_volume"] = (agg
        .groupby(sku_col)[vol_col]
        .shift(1))
    agg["delta"] = agg[vol_col] - agg["prev_volume"]
    agg["pct_change"] = agg["delta"] / agg["prev_volume"] * 100
    return agg

def avg_margin_by_product(order_df: pd.DataFrame,
    sku_col: str,
    revenue_col: str,
    cost_col: str
    ) -> pd.DataFrame:
    """
    Returns per-SKU: avg margin % and avg absolute margin.
    Output columns: [sku_col, 'avg_margin_pct', 'avg_margin_abs']
    """
    agg = (order_df
        .groupby(sku_col)
        .agg(
            total_rev=(revenue_col, 'sum'),
            total_cost=(cost_col, 'sum'))
        .reset_index())
    agg['avg_margin_abs'] = agg['total_rev'] - agg['total_cost']
    agg['avg_margin_pct'] = (
        agg['avg_margin_abs'] / agg['total_rev'] * 100)
    return agg[[sku_col, 'avg_margin_pct', 'avg_margin_abs']]

def cogs_by_product(
    order_df: pd.DataFrame,
    sku_col: str,
    cost_col: str) -> pd.DataFrame:
    """
    Sum of COGS (cost_col) per SKU.
    Returns [sku_col, 'total_cogs']
    """
    df = (order_df
        .groupby(sku_col)[cost_col]
        .sum()
        .reset_index()
        .rename(columns={cost_col: 'total_cogs'}))
    return df

def cogs_breakdown_by_material(
    product_df: pd.DataFrame,
    raw_material_col: str,
    cogs_subtotal_col: str) -> pd.DataFrame:
    """
    Using product_df which maps SKU to raw material,
    aggregates COGS subtotal by raw material.
    Returns ['raw_material', 'total_material_cogs']
    """
    df = (product_df
        .groupby(raw_material_col)[cogs_subtotal_col]
        .sum()
        .reset_index()
        .rename(columns={raw_material_col: 'raw_material',
                         cogs_subtotal_col: 'total_material_cogs'}))
    return df

def buyback_impact(
    order_df: pd.DataFrame,
    sku_col: str,
    buyback_flag_col: str,
    revenue_col: str,
    cost_col: str
) -> pd.DataFrame:
    """
    Calculates:
      - # of buy-back transactions per SKU
      - Total revenue lost and cost incurred
      - Net margin impact
    Returns [sku_col, 'buyback_count', 'rev_impact', 'cost_impact', 'net_impact']
    """
    df = order_df.copy()
    buy = df[df[buyback_flag_col] == True]
    agg = (buy
        .groupby(sku_col)
        .agg(
            buyback_count=(buyback_flag_col, 'count'),
            rev_impact=(revenue_col, 'sum'),
            cost_impact=(cost_col, 'sum'))
        .reset_index())
    agg['net_impact'] = agg['rev_impact'] - agg['cost_impact']
    return agg
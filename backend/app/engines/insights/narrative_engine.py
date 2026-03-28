from typing import Dict, Any, List


def format_currency(value: float) -> str:
    try:
        return f"{value:,.2f}"
    except Exception:
        return str(value)


def get_top_item(items: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if items and isinstance(items, list) and len(items) > 0:
        return items[0]
    return None


def generate_narrative(
    schema_suggestions: Dict[str, Any],
    capabilities: Dict[str, Any],
    profile: Dict[str, Any],
    insights: Dict[str, Any]
) -> Dict[str, Any]:
    narratives = {
        "dataset_summary": "",
        "capability_summary": "",
        "sales_summary": "",
        "inventory_summary": "",
        "logistics_summary": "",
        "data_quality_summary": ""
    }

    dataset_profile = profile.get("dataset_profile", {})
    total_rows = dataset_profile.get("total_rows", 0)
    total_columns = dataset_profile.get("total_columns", 0)
    duplicate_rows = dataset_profile.get("duplicate_rows", 0)
    datetime_cols = dataset_profile.get("datetime_candidate_columns", [])
    numeric_cols = dataset_profile.get("numeric_columns", [])
    categorical_cols = dataset_profile.get("categorical_columns", [])

    narratives["dataset_summary"] = (
        f"The uploaded dataset contains {total_rows} rows and {total_columns} columns. "
        f"It includes {len(numeric_cols)} numeric columns, {len(categorical_cols)} categorical columns, "
        f"and {len(datetime_cols)} date-like columns."
    )

    enabled_caps = [
        cap_name for cap_name, cap_data in capabilities.items()
        if cap_data.get("enabled")
    ]
    if enabled_caps:
        narratives["capability_summary"] = (
            f"The dataset strongly supports the following business analysis areas: "
            f"{', '.join(enabled_caps)}."
        )
    else:
        narratives["capability_summary"] = (
            "The dataset does not strongly support any predefined business capability yet."
        )

    total_nulls = sum(dataset_profile.get("null_counts", {}).values()) if dataset_profile.get("null_counts") else 0
    narratives["data_quality_summary"] = (
        f"The dataset contains {duplicate_rows} duplicate rows and {total_nulls} missing values overall."
    )

    # SALES SUMMARY
    sales_cap = capabilities.get("sales", {})
    sales_insights = insights.get("sales", {})

    if sales_cap.get("enabled"):
        top_products = sales_insights.get("top_products_by_revenue", [])
        revenue_trend = sales_insights.get("revenue_trend", [])
        top_regions = sales_insights.get("top_regions_by_revenue", [])

        sales_lines = ["Sales analysis is enabled for this dataset."]

        top_product = get_top_item(top_products)
        if top_product:
            product_key = next((k for k in top_product.keys() if k.lower() != "total_amount" and k.lower() != "revenue"), None)
            value_key = next((k for k in top_product.keys() if k.lower() in ["total_amount", "revenue", "sales", "sales_amount"]), None)

            if product_key and value_key:
                sales_lines.append(
                    f"The top-performing product is {top_product[product_key]}, "
                    f"with total revenue of {format_currency(top_product[value_key])}."
                )

        if revenue_trend:
            sales_lines.append(
                f"Revenue trend data is available across {len(revenue_trend)} time points."
            )

        if top_regions:
            top_region = get_top_item(top_regions)
            if top_region:
                region_key = next((k for k in top_region.keys() if k.lower() not in ["total_amount", "revenue", "sales", "sales_amount"]), None)
                value_key = next((k for k in top_region.keys() if k.lower() in ["total_amount", "revenue", "sales", "sales_amount"]), None)

                if region_key and value_key:
                    sales_lines.append(
                        f"The leading region is {top_region[region_key]} with revenue of "
                        f"{format_currency(top_region[value_key])}."
                    )
        else:
            narratives_missing_region = schema_suggestions.get("region", {}).get("column") is None
            if narratives_missing_region:
                sales_lines.append(
                    "Region-wise revenue analysis is currently unavailable because no region field was confidently mapped."
                )

        narratives["sales_summary"] = " ".join(sales_lines)
    else:
        narratives["sales_summary"] = (
            "Sales analysis is not fully supported because key sales fields are missing or weakly mapped."
        )

    # INVENTORY SUMMARY
    inventory_cap = capabilities.get("inventory", {})
    inventory_insights = insights.get("inventory", {})

    if inventory_cap.get("enabled"):
        low_stock_items = inventory_insights.get("low_stock_items", [])
        if low_stock_items:
            narratives["inventory_summary"] = (
                f"Inventory analysis is enabled. There are {len(low_stock_items)} low-stock items currently flagged "
                f"for potential reorder attention."
            )
        else:
            narratives["inventory_summary"] = (
                "Inventory analysis is enabled, but no low-stock items were identified in the current output."
            )
    else:
        narratives["inventory_summary"] = (
            "Inventory analysis is not available because stock, reorder level, or lead time fields are missing."
        )

    # LOGISTICS SUMMARY
    logistics_cap = capabilities.get("logistics", {})
    logistics_insights = insights.get("logistics", {})

    if logistics_cap.get("enabled"):
        delay_summary = logistics_insights.get("delivery_delay_summary", {})
        status_distribution = logistics_insights.get("status_distribution", [])

        logistics_lines = ["Logistics analysis is enabled for this dataset."]

        if delay_summary:
            avg_days = delay_summary.get("average_delivery_days")
            if avg_days is not None:
                logistics_lines.append(
                    f"The average delivery time is {avg_days} days."
                )

        if status_distribution:
            top_status = get_top_item(status_distribution)
            if top_status:
                status_key = next((k for k in top_status.keys() if k != "count"), None)
                if status_key:
                    logistics_lines.append(
                        f"The most common logistics status is {top_status[status_key]}."
                    )

        narratives["logistics_summary"] = " ".join(logistics_lines)
    else:
        narratives["logistics_summary"] = (
            "Logistics analysis is not fully available because shipment date, status, or regional fields are missing."
        )

    return narratives
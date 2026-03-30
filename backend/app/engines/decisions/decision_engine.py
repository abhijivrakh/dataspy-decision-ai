from typing import Dict, Any, List


def generate_sales_decisions(insights: Dict[str, Any], forecast: Dict[str, Any], schema_suggestions: Dict[str, Any]) -> List[Dict[str, Any]]:
    decisions = []

    sales_insights = insights.get("sales", {})
    top_products = sales_insights.get("top_products_by_revenue", [])
    top_regions = sales_insights.get("top_regions_by_revenue", [])

    if top_products:
        top_product = top_products[0]
        product_key = next((k for k in top_product.keys() if k.lower() not in ["total_amount", "revenue", "sales", "sales_amount"]), None)
        value_key = next((k for k in top_product.keys() if k.lower() in ["total_amount", "revenue", "sales", "sales_amount"]), None)

        if product_key and value_key:
            decisions.append({
                "title": "Focus on top-performing product",
                "priority": "high",
                "action": f"Increase promotional and inventory focus on {top_product[product_key]}.",
                "rationale": f"{top_product[product_key]} is currently the highest revenue-generating product.",
                "supporting_evidence": {
                    "product": top_product[product_key],
                    "revenue": top_product[value_key]
                }
            })

    region_mapped = schema_suggestions.get("region", {}).get("column")
    if not region_mapped:
        decisions.append({
            "title": "Improve region-level data mapping",
            "priority": "medium",
            "action": "Map or standardize regional fields such as city/state/region to unlock regional sales analysis.",
            "rationale": "Region-wise insights are currently unavailable because no region field was confidently mapped.",
            "supporting_evidence": {
                "region_mapped": False
            }
        })

    forecast_data = forecast.get("forecast", {})
    avg_forecast_value = forecast_data.get("average_forecast_value")
    target_role = forecast_data.get("target_role")

    if avg_forecast_value is not None and target_role == "revenue":
        decisions.append({
            "title": "Plan for upcoming revenue demand",
            "priority": "high",
            "action": f"Prepare operations, stock, and campaign planning around an expected average revenue level of {avg_forecast_value}.",
            "rationale": "The forecast engine predicts upcoming revenue demand based on recent historical trends.",
            "supporting_evidence": {
                "average_forecast_value": avg_forecast_value,
                "forecast_horizon": forecast_data.get("forecast_horizon")
            }
        })

    return decisions


def generate_inventory_decisions(insights: Dict[str, Any]) -> List[Dict[str, Any]]:
    decisions = []

    inventory_insights = insights.get("inventory", {})
    low_stock_items = inventory_insights.get("low_stock_items", [])

    if low_stock_items:
        decisions.append({
            "title": "Reorder low-stock items",
            "priority": "high",
            "action": "Review and reorder products that have reached or fallen below the reorder threshold.",
            "rationale": "Some inventory items are below safe stock levels.",
            "supporting_evidence": {
                "low_stock_count": len(low_stock_items),
                "sample_items": low_stock_items[:5]
            }
        })

    return decisions


def generate_logistics_decisions(insights: Dict[str, Any]) -> List[Dict[str, Any]]:
    decisions = []

    logistics_insights = insights.get("logistics", {})
    delay_summary = logistics_insights.get("delivery_delay_summary", {})

    if delay_summary:
        avg_days = delay_summary.get("average_delivery_days")
        if avg_days is not None and avg_days > 7:
            decisions.append({
                "title": "Investigate delivery delays",
                "priority": "high",
                "action": "Review shipping operations, courier SLAs, and fulfillment bottlenecks to reduce delivery time.",
                "rationale": "Average delivery time is higher than the acceptable threshold.",
                "supporting_evidence": delay_summary
            })

    return decisions


def generate_decisions(
    capabilities: Dict[str, Any],
    insights: Dict[str, Any],
    forecast: Dict[str, Any],
    schema_suggestions: Dict[str, Any]
) -> Dict[str, Any]:
    decisions = {
        "sales": [],
        "inventory": [],
        "logistics": []
    }

    if capabilities.get("sales", {}).get("enabled"):
        decisions["sales"] = generate_sales_decisions(insights, forecast, schema_suggestions)

    if capabilities.get("inventory", {}).get("enabled"):
        decisions["inventory"] = generate_inventory_decisions(insights)

    if capabilities.get("logistics", {}).get("enabled"):
        decisions["logistics"] = generate_logistics_decisions(insights)

    all_decisions = decisions["sales"] + decisions["inventory"] + decisions["logistics"]

    return {
        "decision_summary": {
            "total_decisions": len(all_decisions),
            "high_priority": len([d for d in all_decisions if d["priority"] == "high"]),
            "medium_priority": len([d for d in all_decisions if d["priority"] == "medium"]),
            "low_priority": len([d for d in all_decisions if d["priority"] == "low"])
        },
        "decisions": decisions
    }
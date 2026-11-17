import pandas as pd

from src.data_prep import load_clean_data


def _filter_data(df: pd.DataFrame, category: str | None = None) -> pd.DataFrame:
    """Filtra o DataFrame por categoria, se uma categoria válida for informada."""
    if category and category.lower() != "todas":
        return df[df["category"].str.lower() == category.strip().lower()]
    return df


def get_total_revenue(category: str | None = None) -> float:
    """Retorna a receita total considerando apenas pedidos concluídos."""
    df = _filter_data(load_clean_data(), category)
    completed = df[df["status"] == "Concluído"]
    return round(float(completed["revenue"].sum()), 2)


def get_total_orders(category: str | None = None) -> int:
    """Retorna o total de pedidos concluídos."""
    df = _filter_data(load_clean_data(), category)
    completed = df[df["status"] == "Concluído"]
    return int(completed["order_id"].nunique())


def get_average_ticket(category: str | None = None) -> float:
    """Retorna o ticket médio (receita total / pedidos concluídos)."""
    revenue = get_total_revenue(category)
    orders = get_total_orders(category)
    if orders == 0:
        return 0.0
    return round(revenue / orders, 2)


def get_unique_customers(category: str | None = None) -> int:
    """Retorna a quantidade de clientes únicos com pedidos concluídos."""
    df = _filter_data(load_clean_data(), category)
    completed = df[df["status"] == "Concluído"]
    return int(completed["customer_id"].nunique())


def get_cancellation_rate(category: str | None = None) -> float:
    """Retorna a taxa de cancelamento (%) sobre o total de pedidos."""
    df = _filter_data(load_clean_data(), category)
    total_orders = df["order_id"].nunique()
    if total_orders == 0:
        return 0.0
    canceled_orders = df[df["status"] == "Cancelado"]["order_id"].nunique()
    return round((canceled_orders / total_orders) * 100, 2)


def get_monthly_revenue(category: str | None = None) -> pd.DataFrame:
    """Retorna a receita mensal (pedidos concluídos) ordenada cronologicamente."""
    df = _filter_data(load_clean_data(), category)
    completed = df[df["status"] == "Concluído"].copy()
    completed["month"] = completed["order_date"].dt.to_period("M").astype(str)
    monthly = (
        completed.groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")
    )
    return monthly


def get_top_cities(category: str | None = None, limit: int = 5) -> pd.DataFrame:
    """Retorna as cidades que mais geram receita (apenas pedidos concluídos)."""
    df = _filter_data(load_clean_data(), category)
    completed = df[df["status"] == "Concluído"]
    top_cities = (
        completed.groupby("city", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(limit)
    )
    return top_cities
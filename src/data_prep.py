import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/sales.csv")
CLEAN_PATH = Path("data/sales_clean.csv")


def clean_sales_data(input_path: Path = RAW_PATH, output_path: Path = CLEAN_PATH) -> pd.DataFrame:
    """Padroniza a base de vendas e salva a versão tratada em CSV."""
    df = pd.read_csv(input_path)

    # A base mistura datas YYYY-MM-DD e DD/MM/YYYY
    df["order_date"] = pd.to_datetime(df["order_date"], format="mixed", dayfirst=True)

    # Status com espaços e grafias diferentes
    status_clean = df["status"].str.strip().str.lower()
    status_map = {
        "concluido": "Concluído",
        "concluído": "Concluído",
        "cancelado": "Cancelado",
    }
    df["status"] = status_clean.map(status_map)

    # Remove duplicatas
    df = df.drop_duplicates()

    # Receita por linha: quantidade x preço unitário
    df["revenue"] = df["quantity"] * df["unit_price"]

    # Separador ';' e decimal ','
    df.to_csv(output_path, sep=";", decimal=",", index=False)

    return df


def load_clean_data(path: Path = CLEAN_PATH) -> pd.DataFrame:
    """Lê o arquivo limpo respeitando o separador ';' e o decimal ','."""
    if not path.exists():
        return clean_sales_data()

    df = pd.read_csv(path, sep=";", decimal=",")
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


if __name__ == "__main__":
    df_limpo = clean_sales_data()
    print(f"Linhas após o tratamento: {len(df_limpo)}")
    print(df_limpo.head())

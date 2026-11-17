import pandas as pd
from pathlib import Path

# Caminhos dos arquivos
RAW_PATH = Path("data/sales.csv")
CLEAN_PATH = Path("data/sales_clean.csv")


def clean_sales_data(input_path: Path = RAW_PATH, output_path: Path = CLEAN_PATH) -> pd.DataFrame:
    # 1. Ler o CSV original
    df = pd.read_csv(input_path)

    # 2. Converter datas (format="mixed" entende tanto YYYY-MM-DD quanto DD/MM/YYYY)
    df["order_date"] = pd.to_datetime(df["order_date"], format="mixed", dayfirst=True)

    # 3. Padronizar o status (remove espaços extras, deixa minúsculo e mapeia)
    status_clean = df["status"].str.strip().str.lower()
    status_map = {
        "concluido": "Concluído",
        "concluído": "Concluído",
        "cancelado": "Cancelado",
    }
    df["status"] = status_clean.map(status_map)

    # 4. Remover linhas duplicadas
    df = df.drop_duplicates()

    # 5. Criar a coluna de receita (revenue)
    df["revenue"] = df["quantity"] * df["unit_price"]

    # Salvar o arquivo limpo com ';' como separador e ',' como decimal
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
    print("Dados limpos com sucesso!")
    print(f"Total de linhas após limpeza: {len(df_limpo)}")
    print("\nPrimeiras 5 linhas:")
    print(df_limpo.head())
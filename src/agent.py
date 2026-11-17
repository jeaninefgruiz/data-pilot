import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.metrics import (
    get_average_ticket,
    get_cancellation_rate,
    get_monthly_revenue,
    get_top_cities,
    get_total_orders,
    get_total_revenue,
    get_unique_customers,
)

# Carrega as variáveis do arquivo .env
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

# Mapeamento entre o nome da ferramenta e a função Python real
AVAILABLE_FUNCTIONS = {
    "get_total_revenue": get_total_revenue,
    "get_total_orders": get_total_orders,
    "get_average_ticket": get_average_ticket,
    "get_unique_customers": get_unique_customers,
    "get_cancellation_rate": get_cancellation_rate,
    "get_top_cities": lambda category=None, limit=5: get_top_cities(category, limit).to_dict(orient="records"),
    "get_monthly_revenue": lambda category=None: get_monthly_revenue(category).to_dict(orient="records"),
}

# Descrição das ferramentas para o modelo de linguagem (JSON Schema)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_total_revenue",
            "description": "Calcula a receita total (faturamento) em reais considerando apenas pedidos concluídos. Pode filtrar por categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria de produto (ex: Eletrônicos, Móveis, Acessórios, Escritório). Deixe vazio para todas.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_total_orders",
            "description": "Retorna a quantidade total de pedidos concluídos. Pode filtrar por categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria de produto opcional.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_cities",
            "description": "Retorna o ranking das cidades que mais vendem (maior receita em pedidos concluídos). Use quando perguntarem sobre melhores cidades, ranking de cidades ou vendas por cidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria de produto opcional.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Quantidade de cidades no ranking (padrão é 5).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_average_ticket",
            "description": "Calcula o ticket médio (valor médio por pedido concluído) em reais. Pode filtrar por categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria de produto opcional.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_unique_customers",
            "description": "Conta quantos clientes únicos fizeram pedidos concluídos. Pode filtrar por categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria de produto opcional.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cancellation_rate",
            "description": "Calcula a taxa de cancelamento em porcentagem (%) sobre o total de pedidos. Pode filtrar por categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria de produto opcional.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_revenue",
            "description": "Retorna o faturamento mês a mês (receita mensal) dos pedidos concluídos. Use quando perguntarem sobre evolução mensal ou melhor/pior mês.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria de produto opcional.",
                    }
                },
            },
        },
    },
]

SYSTEM_PROMPT = (
    "Você é o Data Pilot, um assistente analítico de vendas. "
    "Responda sempre em português claro e objetivo. "
    "Nunca invente números: use sempre as ferramentas disponíveis para consultar os dados reais antes de responder. "
    "Formate valores monetários em reais (R$)."
)


def ask_agent(user_question: str, chat_history: list[dict] | None = None) -> tuple[str, list[str]]:
    """
    Envia a pergunta ao OpenRouter, executa as ferramentas solicitadas e retorna
    a resposta final junto com a lista de ferramentas utilizadas.
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "sua_chave_aqui":
        return "⚠️ Configure sua chave OPENROUTER_API_KEY no arquivo .env antes de usar o chat.", []

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": user_question})

    tools_used = []

    try:
        # 1ª chamada: o modelo analisa a pergunta e decide se precisa chamar ferramentas
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )

        response_message = response.choices[0].message

        # Se o modelo decidiu chamar uma ou mais ferramentas
        if response_message.tool_calls:
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments or "{}")
                tools_used.append(f"{func_name}({func_args})")

                if func_name in AVAILABLE_FUNCTIONS:
                    result = AVAILABLE_FUNCTIONS[func_name](**func_args)
                else:
                    result = {"erro": f"Ferramenta {func_name} não encontrada."}

                # Devolve o resultado calculado pelo Python para o modelo
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            # 2ª chamada: o modelo redige a resposta final usando os números calculados
            second_response = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=messages,
            )
            return second_response.choices[0].message.content, tools_used

        return response_message.content, tools_used

    except Exception as e:
        return (
            f"⚠️ Ocorreu uma instabilidade ao consultar o modelo gratuito no OpenRouter ({e}). "
            "Tente enviar a pergunta novamente em alguns segundos.",
            tools_used,
        )
import plotly.express as px
import streamlit as st

from src.agent import ask_agent
from src.data_prep import load_clean_data
from src.metrics import (
    get_average_ticket,
    get_cancellation_rate,
    get_monthly_revenue,
    get_top_cities,
    get_total_orders,
    get_total_revenue,
    get_unique_customers,
)

st.set_page_config(page_title="Data Pilot", page_icon="📊", layout="wide")

st.title("Data Pilot: Inteligência em Vendas")

menu = st.sidebar.radio(
    "Navegação",
    ["Painel de Vendas", "Conversa com os Dados"],
)

if menu == "Painel de Vendas":
    df = load_clean_data()

    categorias = ["Todas"] + sorted(df["category"].dropna().unique().tolist())
    categoria_selecionada = st.sidebar.selectbox("Filtrar por Categoria", categorias)

    st.subheader(f"Visão Geral (Categoria: {categoria_selecionada})")

    receita = get_total_revenue(categoria_selecionada)
    pedidos = get_total_orders(categoria_selecionada)
    ticket = get_average_ticket(categoria_selecionada)
    clientes = get_unique_customers(categoria_selecionada)
    cancelamento = get_cancellation_rate(categoria_selecionada)

    col1, col2, col3 = st.columns(3)
    col1.metric("Receita Total", f"R$ {receita:,.2f}")
    col2.metric("Pedidos Concluídos", pedidos)
    col3.metric("Ticket Médio", f"R$ {ticket:,.2f}")

    col4, col5, _ = st.columns(3)
    col4.metric("Clientes Únicos", clientes)
    col5.metric("Taxa de Cancelamento", f"{cancelamento:.1f}%")

    st.divider()

    graf1, graf2 = st.columns(2)

    with graf1:
        st.subheader("Receita Mensal (Pedidos Concluídos)")
        df_mensal = get_monthly_revenue(categoria_selecionada)
        fig_mensal = px.bar(
            df_mensal,
            x="month",
            y="revenue",
            text_auto=".2s",
            labels={"month": "Mês", "revenue": "Receita (R$)"},
            color_discrete_sequence=["#2E86C1"],
        )
        fig_mensal.update_layout(xaxis_type="category", yaxis_title="Receita (R$)", xaxis_title="Mês")
        st.plotly_chart(fig_mensal, use_container_width=True)

    with graf2:
        st.subheader("Top 5 Cidades por Receita")
        df_cidades = get_top_cities(categoria_selecionada, limit=5)
        fig_cidades = px.bar(
            df_cidades,
            x="revenue",
            y="city",
            orientation="h",
            text_auto=".2s",
            labels={"city": "Cidade", "revenue": "Receita (R$)"},
            color_discrete_sequence=["#1ABC9C"],
        )
        fig_cidades.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Receita (R$)",
            yaxis_title="Cidade",
        )
        st.plotly_chart(fig_cidades, use_container_width=True)

elif menu == "Conversa com os Dados":
    st.subheader("Converse com seus Dados")
    st.caption("Pergunte em português sobre faturamento, pedidos, ticket médio, clientes, cancelamentos ou ranking de cidades.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tools"):
                st.caption(f"Ferramenta acionada: `{', '.join(msg['tools'])}`")

    if prompt := st.chat_input("Ex: Quais são as 5 cidades que mais vendem?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando os dados..."):
                history_for_api = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]
                resposta, ferramentas = ask_agent(prompt, history_for_api)
                st.markdown(resposta)
                if ferramentas:
                    st.caption(f"Ferramenta acionada: `{', '.join(ferramentas)}`")

        st.session_state.messages.append(
            {"role": "assistant", "content": resposta, "tools": ferramentas}
        )

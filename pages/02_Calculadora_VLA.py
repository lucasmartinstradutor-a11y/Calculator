import datetime
import streamlit as st

st.set_page_config(page_title="Calculadora VLA", page_icon="📚", layout="wide")

# -------------------- CONSTANTES DE POLÍTICA --------------------
# Ajuste aqui, se mudar a política.
POLITICA_DESCONTOS = [
    {"min": 1,    "max": 49,   "pct": 0},
    {"min": 50,   "max": 99,   "pct": 20},
    {"min": 100,  "max": 149,  "pct": 30},
    {"min": 150,  "max": 249,  "pct": 40},
    {"min": 250,  "max": 999,  "pct": 45},
    {"min": 1000, "max": None, "pct": 50},
]

PARCELAS_PADRAO = 10
FRETE_GRATIS_MIN_QTD = 100
TXT_FRETE_GRATIS = "Frete Grátis"
TXT_FRETE_CALC = "À calcular"

# -------------------- HELPERS --------------------
def br_money(x: float) -> str:
    return f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def pct_por_qtd(qtd: int) -> float:
    for faixa in POLITICA_DESCONTOS:
        lo, hi, pct = faixa["min"], faixa["max"], faixa["pct"]
        if qtd >= lo and (hi is None or qtd <= hi):
            return float(pct)
    # fallback: menor faixa
    return float(POLITICA_DESCONTOS[0]["pct"])

# -------------------- UI --------------------
st.title("📚 Calculadora de Preços e Descontos (Autores)")
st.caption("Entradas: autor, consultor, preço de capa e tiragem. Política de descontos fixa por quantidade. Gera script pronto para WhatsApp/CRM.")

id1, id2 = st.columns(2)
with id1:
    nome_cliente = st.text_input("Nome do autor", placeholder="Ex.: Prof. João Silva")
with id2:
    consultor = st.text_input("Consultor", placeholder="Ex.: Lucas Martins")

c0, c1 = st.columns(2)
with c0:
    preco_capa = st.number_input("Preço de capa (R$)", min_value=0.0, step=0.10, value=84.90, format="%.2f")
with c1:
    qtd = st.number_input("Quantidade (tiragem)", min_value=1, step=1, value=100)

# -------------------- CÁLCULO --------------------
desconto_pct = pct_por_qtd(int(qtd))
bruto = preco_capa * qtd
desconto_rs = bruto * (desconto_pct/100.0)
total = bruto - desconto_rs
unitario = total / qtd if qtd > 0 else 0
parcela = total / PARCELAS_PADRAO
frete = TXT_FRETE_GRATIS if qtd >= FRETE_GRATIS_MIN_QTD else TXT_FRETE_CALC

st.subheader("Resultados")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Desconto aplicado", f"{desconto_pct:.0f}%")
m2.metric("Total a pagar", br_money(total))
m3.metric("Valor unitário", br_money(unitario))
m4.metric(f"Parcela ({PARCELAS_PADRAO}x)", br_money(parcela))
m5.metric("Frete", frete)

st.divider()

# -------------------- SCRIPT PARA WHATSAPP/CRM --------------------
st.subheader("Copiar e enviar 📄➡️📲")

data_hoje = datetime.date.today().strftime("%d/%m/%Y")

script = f"""
Olá {nome_cliente or ''}! 😊

Segue proposta da Editora Dialética (data {data_hoje}), preparada por {consultor or 'Consultor'}.

📘 Preço de capa: {br_money(preco_capa)}
🧮 Tiragem: {int(qtd)} un.
🎯 Desconto aplicado (política): {desconto_pct:.0f}%

💰 Total a pagar: {br_money(total)}
💵 Valor unitário: {br_money(unitario)}
💳 Parcela ({PARCELAS_PADRAO}x sem juros): {br_money(parcela)}
🚚 Frete: {frete}

Qualquer dúvida fico à disposição! 🙂
""".strip()

st.text_area("Script pronto para copiar", script, height=260)
st.download_button("⬇️ Baixar script (.txt)", data=script, file_name="script_calculadora_vla.txt")

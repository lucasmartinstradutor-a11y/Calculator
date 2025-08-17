# pages/02_calculadora_precos.py
import datetime
from typing import List, Dict

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calculadora de Preços", page_icon="💸", layout="wide")

# ---------- helpers ----------
def br_money(x: float) -> str:
    return f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_int_list(s: str) -> List[int]:
    vals = []
    for p in s.split(","):
        p = p.strip()
        if p:
            try:
                vals.append(int(p))
            except:
                pass
    return sorted(set(vals))

def parse_pct_list(s: str) -> List[float]:
    out = []
    for p in s.split(","):
        p = p.strip().replace("%", "").replace(",", ".")
        if p:
            try:
                out.append(float(p))
            except:
                pass
    return out

def desconto_permitido(qty: int, faixas: List[Dict]) -> float:
    for f in faixas:
        lo = f["min"]; hi = f["max"]
        if (qty >= lo) and (hi is None or qty <= hi):
            return f["pct"]
    return faixas[0]["pct"]

def make_faixas_by_thresholds(quantidades: List[int], descontos_pct: List[float]) -> List[Dict]:
    quantidades = sorted(quantidades)
    faixas = []
    for i, q in enumerate(quantidades):
        pct = descontos_pct[i] if i < len(descontos_pct) else descontos_pct[-1]
        hi = (quantidades[i+1] - 1) if i < len(quantidades)-1 else None
        faixas.append({"min": q, "max": hi, "pct": pct})
    return faixas

# ---------- UI ----------
st.title("💸 Calculadora de Preços e Descontos (Autores)")
st.caption("Cenários por tiragem, simulação e script automático para WhatsApp/CRM.")

# Identificação
id1, id2 = st.columns(2)
with id1:
    nome_cliente = st.text_input("Nome do cliente", placeholder="Ex.: Prof. João Silva")
with id2:
    consultor = st.text_input("Consultor", placeholder="Ex.: Lucas Martins")

# Entradas principais
c0, c1, c2, c3 = st.columns([1.2, 2.2, 2.2, 2.2])
with c0:
    preco_capa = st.number_input("Preço de capa (R$)", min_value=0.0, step=0.10, value=84.90, format="%.2f")
with c1:
    quantidades_str = st.text_input("Cenários de quantidades (vírgula)", value="50,100,150,250,1000")
    quantidades = parse_int_list(quantidades_str) or [50,100,150,250,1000]
with c2:
    descontos_str = st.text_input("Descontos % por cenário (mesma ordem)", value="20,30,40,45,50")
    descontos_pct = parse_pct_list(descontos_str) or [20,30,40,45,50]
with c3:
    parcelas = st.number_input("Parcelas sem juros (1–12)", min_value=1, max_value=12, value=10, step=1)

# Política de frete
col_f1, col_f2 = st.columns(2)
with col_f1:
    frete_gratis_min_qtd = st.number_input("Frete grátis a partir de (qtd.)", min_value=0, value=100, step=50)
with col_f2:
    texto_frete_gratis = st.text_input("Texto frete grátis", value="Frete Grátis")
texto_frete_calcular = "À calcular"

faixas = make_faixas_by_thresholds(quantidades, descontos_pct)

# ---------- tabela de cenários ----------
linhas = []
for i, qty in enumerate(quantidades):
    pct = descontos_pct[i] if i < len(descontos_pct) else descontos_pct[-1]
    bruto = preco_capa * qty
    desc_rs = bruto * (pct/100.0)
    total = bruto - desc_rs
    unitario = total / qty if qty > 0 else 0
    parcela_val = total / parcelas if parcelas > 0 else 0
    frete_txt = texto_frete_gratis if qty >= frete_gratis_min_qtd else texto_frete_calcular
    linhas.append({
        "Quantidade": qty,
        "Valor sem desconto": bruto,
        "Desc %": pct,
        "Desconto em R$": desc_rs,
        "Total a pagar": total,
        "Valor unitário": unitario,
        f"Parcela ({parcelas}x)": parcela_val,
        "Frete": frete_txt,
    })
df = pd.DataFrame(linhas)

st.subheader("Cenários")
fmt = {
    "Valor sem desconto": "R$ {:,.2f}",
    "Desconto em R$": "R$ {:,.2f}",
    "Total a pagar": "R$ {:,.2f}",
    "Valor unitário": "R$ {:,.2f}",
}
fmt_parc = f"Parcela ({parcelas}x)"; fmt[fmt_parc] = "R$ {:,.2f}"
st.dataframe(df.style.format(fmt).hide_index(), use_container_width=True)

# ---------- Pedido (a partir das tiragens definidas) ----------
st.subheader("Pedido (escolha uma tiragem)")
pedido_qtd = st.selectbox("Exemplares do pedido", options=quantidades, index=0)
idx = quantidades.index(pedido_qtd)
pedido_desc_pct = descontos_pct[idx] if idx < len(descontos_pct) else descontos_pct[-1]

if st.toggle("Editar % de desconto do pedido?", value=False):
    pedido_desc_pct = st.number_input("Desconto do pedido (%)", min_value=0.0, max_value=100.0,
                                      value=float(pedido_desc_pct), step=0.5)

pedido_bruto = preco_capa * pedido_qtd
pedido_desc_rs = pedido_bruto * (pedido_desc_pct/100.0)
pedido_total = pedido_bruto - pedido_desc_rs
pedido_unit = pedido_total / pedido_qtd if pedido_qtd > 0 else 0
pedido_parc = pedido_total / parcelas
pedido_frete = texto_frete_gratis if pedido_qtd >= frete_gratis_min_qtd else texto_frete_calcular

pc1, pc2, pc3, pc4 = st.columns(4)
pc1.metric("Total a pagar (pedido)", br_money(pedido_total))
pc2.metric("Valor unitário", br_money(pedido_unit))
pc3.metric(f"Parcela ({parcelas}x)", br_money(pedido_parc))
pc4.metric("Frete", pedido_frete)

# ---------- Simulador (verificação de política) ----------
st.subheader("Simulador rápido (verificar política)")
ss1, ss2 = st.columns(2)
with ss1:
    sim_qtd = st.number_input("Quantidade (qualquer)", min_value=1, value=120, step=10)
with ss2:
    sim_desc = st.number_input("Desconto proposto (%)", min_value=0.0, max_value=100.0, value=28.0, step=0.5)

permitido = desconto_permitido(int(sim_qtd), faixas)
status = "✅ Dentro da faixa" if sim_desc <= permitido else "⚠️ Fora da faixa"
st.write(f"**Desconto permitido para {int(sim_qtd)} un.:** {permitido:.1f}%")
st.write(f"**Status:** {status}")

sim_bruto = preco_capa * sim_qtd
sim_desc_rs = sim_bruto * (sim_desc/100.0)
sim_total = sim_bruto - sim_desc_rs
sim_unitario = sim_total / sim_qtd
sim_parcela = sim_total / parcelas
sim_frete = texto_frete_gratis if sim_qtd >= frete_gratis_min_qtd else texto_frete_calcular

scol1, scol2, scol3, scol4 = st.columns(4)
scol1.metric("Total a pagar", br_money(sim_total))
scol2.metric("Valor unitário", br_money(sim_unitario))
scol3.metric(f"Parcela ({parcelas}x)", br_money(sim_parcela))
scol4.metric("Frete", sim_frete)

st.divider()

# ---------- Script para WhatsApp/CRM ----------
st.subheader("Copiar e enviar 📄➡️📲 (WhatsApp/CRM)")

mostrar_tabela_no_script = st.checkbox("Incluir tabela de cenários no script", value=True)

linhas_txt = []
for r in linhas:
    linhas_txt.append(
        f"- {r['Quantidade']} un.: desc {r['Desc %']:.0f}% | "
        f"Total {br_money(r['Total a pagar'])} | Unit {br_money(r['Valor unitário'])} | "
        f"Parcela {br_money(r[fmt_parc])} | Frete {r['Frete']}"
    )
tabela_cenarios = "\n".join(linhas_txt)

data_hoje = datetime.date.today().strftime("%d/%m/%Y")

script = f"""
Olá {nome_cliente or ''}! 😊

Segue proposta de preços da Editora Dialética (data {data_hoje}), preparada por {consultor or 'Consultor'}.

Preço de capa: {br_money(preco_capa)}
Parcelamento padrão: {parcelas}x sem juros
Política de frete: grátis a partir de {frete_gratis_min_qtd} un.

{"Cenários por tiragem:\n" + tabela_cenarios if mostrar_tabela_no_script else ""}

Pedido escolhido:
- Quantidade: {pedido_qtd} un.
- Desconto aplicado: {pedido_desc_pct:.1f}% ({br_money(pedido_desc_rs)})
- Total a pagar: {br_money(pedido_total)}
- Valor unitário: {br_money(pedido_unit)}
- Parcela ({parcelas}x): {br_money(pedido_parc)}
- Frete: {pedido_frete}

Simulação avulsa:
- Quantidade: {int(sim_qtd)} un.
- Desconto proposto: {sim_desc:.1f}% (permitido {permitido:.1f}%) → {status}
- Total: {br_money(sim_total)} | Unit: {br_money(sim_unitario)} | Parcela: {br_money(sim_parcela)} | Frete: {sim_frete}
""".strip()

st.text_area("Script pronto para copiar", script, height=280)
st.download_button("⬇️ Baixar script (.txt)", data=script, file_name="script_precos.txt")

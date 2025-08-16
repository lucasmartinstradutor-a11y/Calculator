import datetime
import io
import tempfile
from pathlib import Path

import streamlit as st
from docxtpl import DocxTemplate

# PDF opcional (requer Microsoft Word no macOS)
try:
    from docx2pdf import convert as docx2pdf_convert
    DOCX2PDF_OK = True
except Exception:
    DOCX2PDF_OK = False

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Calculadora de Revisão", page_icon="📝")
st.title("📝 Calculadora de Orçamento de Revisão (Dialética)")
st.caption("Cálculo rápido + script de vendas para autores. Desconto sem limite e parcelas editáveis.")

# ----------------- DADOS DO ORÇAMENTO -----------------
st.markdown("### Dados do orçamento")
cA, cB = st.columns(2)
with cA:
    nome_cliente = st.text_input("Nome do cliente", placeholder="Ex.: Prof. João Silva")
with cB:
    consultor = st.text_input("Consultor", placeholder="Ex.: Lucas Martins")
observacoes = st.text_area(
    "Observações (opcional)",
    placeholder="Ex.: Valores válidos por 7 dias. Entrega estimada conforme cronograma.",
)

# ----------------- ENTRADAS -----------------
st.markdown("### Entradas de cálculo")
colI, colII = st.columns(2)
with colI:
    palavras = st.number_input("Contagem de palavras", min_value=0, step=100, value=30000)
with colII:
    valor_palavra = st.number_input("Valor por palavra (R$)", min_value=0.00, step=0.01, value=0.10, format="%.2f")

st.markdown("### Desconto e parcelamento")
c1, c2, c3 = st.columns(3)
with c1:
    aplicar_desconto = st.toggle("Aplicar desconto?", value=True)
with c2:
    taxa_desconto_pct = st.number_input("% de desconto", min_value=0.0, max_value=100.0, value=20.0, step=1.0, format="%.1f")
with c3:
    num_parcelas = st.number_input("Nº de parcelas (1 a 6)", min_value=1, max_value=6, value=4, step=1)

prazo_dias = 30

# -------- Helpers BR --------
def br_money(x: float) -> str:
    return f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def br_int(x: int) -> str:
    return f"{x:,}".replace(",", ".")

# ----------------- CÁLCULOS -----------------
preco_base = float(palavras) * float(valor_palavra)
taxa_desconto = (taxa_desconto_pct / 100.0) if aplicar_desconto else 0.0
valor_desconto = preco_base * taxa_desconto
preco_final = preco_base - valor_desconto
valor_parcela = preco_final / num_parcelas if preco_final > 0 else 0.0

data_hoje = datetime.date.today()
data_orcamento = data_hoje.strftime("%d/%m/%Y")
data_entrega = (data_hoje + datetime.timedelta(days=prazo_dias)).strftime("%d/%m/%Y")

parcelamento_texto = f"{int(num_parcelas)}x sem juros de {br_money(valor_parcela)} cada"

# ----------------- RESULTADOS -----------------
st.subheader("Resultados")
m1, m2, m3 = st.columns(3)
m1.metric("Preço base", br_money(preco_base))
m2.metric("Desconto aplicado?", "Sim" if aplicar_desconto and taxa_desconto_pct > 0 else "Não")
m3.metric("Preço final", br_money(preco_final))

st.write(f"**Data do orçamento:** {data_orcamento}")
st.write(f"**% de desconto aplicado:** {taxa_desconto_pct if aplicar_desconto else 0:.1f}%")
st.write(f"**Valor do desconto:** {br_money(valor_desconto)}")
st.write(f"**Parcelamento:** {parcelamento_texto}")
st.write(f"**Prazo estimado:** {prazo_dias} dias (até {data_entrega})")

st.divider()

# ----------------- SCRIPT (só para copiar/WhatsApp) -----------------
script = f"""
Olá! 😊 Segue o orçamento da revisão ortográfica e gramatical (data: {data_orcamento}):

• Cliente: {nome_cliente or "-"}
• Consultor: {consultor or "-"}
• Contagem de palavras: {br_int(int(palavras))}
• Preço base: {br_money(preco_base)}
• Desconto aplicado: {f"{taxa_desconto_pct:.1f}%" if aplicar_desconto and taxa_desconto_pct > 0 else "— (não aplicado)"}
• Valor do desconto: {br_money(valor_desconto)}
• Valor final: {br_money(preco_final)}
• Condição de pagamento: {parcelamento_texto}
• Prazo estimado de entrega: {prazo_dias} dias (até {data_entrega})

Observações: {observacoes or "-"}
""".strip()

st.subheader("Copiar e enviar (WhatsApp/CRM)")
st.text_area("Script de venda (não vai para o DOCX por padrão)", script, height=220)

st.divider()

# ----------------- DOCX/PDF -----------------
st.subheader("Gerar orçamento no seu modelo")
modelo = st.file_uploader(
    "Envie o seu modelo .docx com placeholders (ex.: {{data_orcamento}}, {{nome_cliente}}, {{consultor}}, {{observacoes}}, {{palavras}}, {{preco_base}}, {{desconto_percent}}, {{valor_desconto}}, {{preco_final}}, {{num_parcelas}}, {{valor_parcela}}, {{parcelamento_texto}}, {{prazo_dias}}, {{data_entrega}})",
    type=["docx"]
)

incluir_script_no_docx = st.checkbox("Incluir o script de venda dentro do DOCX", value=False)

contexto = {
    # cabeçalho/identificação
    "data_orcamento": data_orcamento,
    "nome_cliente": nome_cliente,
    "consultor": consultor,
    "observacoes": observacoes,
    # números
    "palavras": br_int(int(palavras)),
    "valor_palavra": br_money(valor_palavra),
    "preco_base": br_money(preco_base),
    "desconto_percent": f"{taxa_desconto_pct:.1f}%" if (aplicar_desconto and taxa_desconto_pct > 0) else "—",
    "valor_desconto": br_money(valor_desconto),
    "preco_final": br_money(preco_final),
    "num_parcelas": int(num_parcelas),
    "valor_parcela": br_money(valor_parcela),
    "parcelamento_texto": parcelamento_texto,  # prontinho para uma linha só
    "prazo_dias": prazo_dias,
    "data_entrega": data_entrega,
}

if incluir_script_no_docx:
    contexto["script"] = script  # só inclui se marcado

colA, colB = st.columns(2)
with colA:
    gerar_docx = st.button("📄 Gerar DOCX")
with colB:
    gerar_pdf = st.button("🧾 Gerar PDF (usa Microsoft Word)")

# Geração do DOCX preenchido
if gerar_docx:
    if not modelo:
        st.warning("Envie um arquivo de modelo .docx primeiro.")
    else:
        try:
            tpl = DocxTemplate(io.BytesIO(modelo.read()))
            tpl.render(contexto)
            buf = io.BytesIO()
            tpl.save(buf)
            buf.seek(0)
            nome = f"Orcamento_Rev_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            st.success("DOCX gerado com sucesso!")
            st.download_button(
                "⬇️ Baixar DOCX",
                data=buf,
                file_name=nome,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except Exception as e:
            st.error(f"Falha ao gerar DOCX: {e}")

# Conversão para PDF (requer Word no macOS)
if gerar_pdf:
    if not modelo:
        st.warning("Envie um arquivo de modelo .docx primeiro.")
    elif not DOCX2PDF_OK:
        st.info("Para PDF automático, instale Microsoft Word e o pacote 'docx2pdf'. Caso contrário, gere o DOCX e exporte para PDF manualmente.")
    else:
        try:
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "saida.docx"
                out_pdf = Path(td) / "saida.pdf"
                # gerar DOCX temporário
                tpl = DocxTemplate(io.BytesIO(modelo.read()))
                tpl.render(contexto)
                tpl.save(src.as_posix())
                # converter
                docx2pdf_convert(src.as_posix(), out_pdf.as_posix())
                pdf_bytes = out_pdf.read_bytes()
                st.success("PDF gerado com sucesso!")
                st.download_button(
                    "⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"Orcamento_Rev_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                )
        except Exception as e:
            st.error(f"Falha ao gerar PDF (verifique o Microsoft Word): {e}")

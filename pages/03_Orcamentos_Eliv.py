# pages/03_Orcamentos_ELIV.py
import io
import datetime as dt
from pathlib import Path

import streamlit as st
from docxtpl import DocxTemplate

# ========================= CONFIG VISUAL =========================
st.set_page_config(page_title="Orçamentos ELIV", page_icon="📦", layout="wide")

# CSS: números alinhados e avisa que os alerts usarão fonte normal
st.markdown("""
<style>
/* números com largura fixa melhoram a leitura de valores */
body, .stAlert p, .stMarkdown p, .st-emotion-cache-16idsys p {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}
</style>
""", unsafe_allow_html=True)


# ========================= HELPERS =========================
def br_money(x: float | int) -> str:
    """Formata para R$ 1.234,56."""
    if x is None:
        return "—"
    s = f"R$ {x:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def escape_md(s: str) -> str:
    """Escapa caracteres que o Markdown usa como sintaxe ($, _)"""
    return s.replace("$", r"\$").replace("_", r"\_")

def render_docxtpl(template_path: Path, context: dict) -> bytes:
    tpl = DocxTemplate(str(template_path))
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    buf.seek(0)
    return buf.read()

# Onde estão os templates (pasta na raiz do repo)
# pages/ está um nível abaixo da raiz → parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
TEMPLATE_COMUM = TEMPLATES_DIR / "ELIV_Comum.docx"
TEMPLATE_UNI   = TEMPLATES_DIR / "ELIV_Universidade.docx"


# ========================= TABELA DE PACOTES =========================
# Valores a partir do seu material (imagem): 6x e à vista (PIX)
PACOTES = {
    "Básico":   {"lista_pix": 1884.60, "mensal_6x": 349.00, "parcelas": 6},
    "Especial": {"lista_pix": 1938.60, "mensal_6x": 359.00, "parcelas": 6},
    "Premium":  {"lista_pix": 2694.60, "mensal_6x": 499.00, "parcelas": 6},
}

FORMAS = ["6x sem juros", "à vista (PIX)"]


# ========================= UI =========================
st.title("📦 Orçamentos ELIV")

# Dados principais (fica em uma aba separada da parte da universidade)
tabs = st.tabs(["Dados principais", "Universidade (opcional)"])
K = "eliv_"  # prefixo para keys únicas

with tabs[0]:
    c1, c2 = st.columns([1, 1])
    with c1:
        cliente = st.text_input("Nome do cliente", placeholder="Ex.: Prof. João Silva", key=f"{K}cliente")
        consultor = st.text_input("Consultor", placeholder="Ex.: Lucas Martins", key=f"{K}consultor")
        obra = st.text_input("Título da obra", placeholder="Ex.: DICIONÁRIO TEMÁTICO DE TURISMO E PATRIMÔNIO", key=f"{K}obra")
    with c2:
        paginas = st.number_input("Nº de páginas", min_value=20, max_value=2000, step=10, value=250, key=f"{K}paginas")
        pacote = st.selectbox("Pacote ELIV", list(PACOTES.keys()), index=1, key=f"{K}pacote")
        forma_pag = st.selectbox("Forma de pagamento", FORMAS, index=0, key=f"{K}fpag")

    # Desconto padrão (15% sugerido)
    desconto_pac_pct = st.slider("% de desconto no pacote", 0, 40, 15, 1, key=f"{K}desc_pac")

    # Cálculos
    base = PACOTES[pacote]["lista_pix"]
    parcelas = PACOTES[pacote]["parcelas"]
    total_com_desc = base * (1 - desconto_pac_pct/100)
    mensal = (total_com_desc / parcelas) if forma_pag == "6x sem juros" else None

    # Quadro de resumo sem quebrar o Markdown por causa do "R$"
    msg = f"Pacote **{pacote}** | **{forma_pag}** | **Com desconto:** {br_money(total_com_desc)}"
    if mensal:
        msg += f" ({parcelas}x de {br_money(mensal)})"
    st.success(escape_md(msg))

    st.divider()

    st.subheader("Gerar DOCX – Comum")
    obs = st.text_area("Observações (opcional)", key=f"{K}obs")

    btn_comum = st.button("Gerar DOCX – Comum", type="primary", key=f"{K}btn_docx_comum")
    if btn_comum:
        # Contexto do template COMUM
        context = {
            "data": dt.date.today().strftime("%d/%m/%Y"),
            "cliente": cliente or "",
            "consultor": consultor or "",
            "obra": obra or "",
            "paginas": int(paginas),
            "pacote": pacote,
            "forma_pag": forma_pag,
            "preco_lista": br_money(base),
            "desc_pac_pct": f"{desconto_pac_pct:.0f}%",
            "valor_com_desconto": br_money(total_com_desc),
            "mensal_final": br_money(mensal) if mensal else "",
            "observacoes": obs or "",
        }
        if not TEMPLATE_COMUM.exists():
            st.error("Template **ELIV_Comum.docx** não encontrado em /templates.")
        else:
            bin_doc = render_docxtpl(TEMPLATE_COMUM, context)
            st.download_button(
                "Baixar DOCX – Comum",
                data=bin_doc,
                file_name="Orcamento_Comum_ELIV.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"{K}down_comum"
            )


with tabs[1]:
    st.markdown("Ative esta seção **apenas** quando o orçamento for para Universidade. O nome do **autor/responsável** será o *nome do cliente* informado na aba anterior.")
    modo_uni = st.toggle("Orçamento para Universidade", value=False, key=f"{K}modo_uni")

    if modo_uni:
        cA, cB, cC = st.columns([1, 1, 1])
        with cA:
            universidade = st.text_input("Universidade", placeholder="Ex.: Universidade Federal de Viçosa", key=f"{K}uni_nome")
        with cB:
            tratamento = st.selectbox(
                "Pronome de tratamento",
                ["Prof.", "Profa.", "Prof. Dr.", "Profa. Dra.", "Sr.", "Sra.", "Doutor", "Doutora"],
                index=1, key=f"{K}trat"
            )
        with cC:
            contato = st.text_input("Contato (telefone/email)", placeholder="Ex.: (31) 99999-0000", key=f"{K}uni_contato")

        st.subheader("Tiragem da universidade")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            preco_capa = st.number_input("Preço de capa (R$)", min_value=10.00, step=0.50, value=75.00, key=f"{K}capafis")
        with c2:
            tir_qtd = st.number_input("Quantidade", min_value=10, step=10, value=100, key=f"{K}tir_qtd")
        with c3:
            tir_desc_pct = st.number_input("% de desconto na tiragem", min_value=0.0, step=1.0, value=30.0, key=f"{K}tir_desc")

        ebook_preco = st.number_input("Preço do e-book (R$)", min_value=0.0, step=1.0, value=0.0, key=f"{K}ebookp")

        # Cálculos de tiragem
        unitario_desc = preco_capa * (1 - tir_desc_pct/100)
        total_tiragem = unitario_desc * tir_qtd

        azul = f"Unitário com desconto: {br_money(unitario_desc)}  |  **Total tiragem ({int(tir_qtd)})** : {br_money(total_tiragem)}"
        st.info(escape_md(azul))

        st.subheader("Gerar DOCX – Universidade")
        btn_uni = st.button("Gerar DOCX – Universidade", type="primary", key=f"{K}btn_docx_uni")

        if btn_uni:
            # Autor/responsável = nome do cliente (aba 1)
            autor = cliente or ""

            context = {
                "data": dt.date.today().strftime("%d/%m/%Y"),
                # Cabeçalho específico de universidade
                "universidade": universidade or "",
                "contato": contato or "",
                "tratamento": tratamento or "",
                "autor": autor,
                # Obra / pacote / forma de pagamento
                "obra": obra or "",
                "paginas": int(paginas),
                "pacote": pacote,
                "forma_pag": forma_pag,
                "preco_lista": br_money(base),
                "desc_pac_pct": f"{desconto_pac_pct:.0f}%",
                "valor_com_desconto": br_money(total_com_desc),
                "mensal_final": br_money(mensal) if mensal else "",
                # Tiragem / e-book
                "preco_capa": br_money(preco_capa),
                "desc_tiragem_pct": f"{tir_desc_pct:.0f}%",
                "preco_unitario": br_money(unitario_desc),
                "tiragem_qtd": int(tir_qtd),
                "total_tiragem": br_money(total_tiragem),
                "ebook_preco": br_money(ebook_preco),
                # Total geral (editoração + tiragem)
                "total_geral": br_money(total_com_desc + total_tiragem),
            }

            if not TEMPLATE_UNI.exists():
                st.error("Template **ELIV_Universidade.docx** não encontrado em /templates.")
            else:
                bin_doc = render_docxtpl(TEMPLATE_UNI, context)
                st.download_button(
                    "Baixar DOCX – Universidade",
                    data=bin_doc,
                    file_name="Orcamento_Universidade_ELIV.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"{K}down_uni"
                )

"""Agenda Tributária — calendário de vencimentos de ICMS (por estado) e obrigações
federais, com destaque para ICMS, busca, favoritos e visão dos próximos 7 dias.

Rodar com:
    streamlit run app.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "agenda_data.json"
FAVORITOS_PATH = BASE_DIR / "favoritos.json"

UF_NOMES = {
    "FEDERAL": "Federal",
    "AL": "Alagoas", "BA": "Bahia", "CE": "Ceará", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe",
}
ESTADOS_ORDENADOS = sorted(c for c in UF_NOMES if c != "FEDERAL")

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
DIAS_SEMANA_PT = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

CATEGORIA_LABEL = {"PRINCIPAL": "🟨 Principal", "ACESSORIA": "🟦 Acessória", "FERIADO": "Feriado"}


@dataclass(frozen=True)
class Item:
    uf: str
    data: str
    categoria: str
    titulo: str
    descricao: str
    fundamentacao: str
    nota: str

    @property
    def data_obj(self) -> date:
        dia, mes, ano = (int(p) for p in self.data.split("/"))
        return date(ano, mes, dia)

    @property
    def mes_ano(self) -> str:
        _, mes, ano = self.data.split("/")
        return f"{mes}/{ano}"

    @property
    def is_icms(self) -> bool:
        return self.uf != "FEDERAL"

    @property
    def item_id(self) -> str:
        return f"{self.uf}|{self.data}|{self.titulo}"


@st.cache_data
def carregar_dados() -> list[Item]:
    bruto = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return [Item(**registro) for registro in bruto]


def carregar_favoritos() -> set[str]:
    if "favoritos" in st.session_state:
        return st.session_state["favoritos"]
    if FAVORITOS_PATH.exists():
        try:
            favoritos = set(json.loads(FAVORITOS_PATH.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            favoritos = set()
    else:
        favoritos = set()
    st.session_state["favoritos"] = favoritos
    return favoritos


def salvar_favoritos(favoritos: set[str]) -> None:
    st.session_state["favoritos"] = favoritos
    try:
        FAVORITOS_PATH.write_text(json.dumps(sorted(favoritos), ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # favoritos são conveniência local, não crítico se não puder gravar


def alternar_favorito(item_id: str) -> None:
    favoritos = carregar_favoritos()
    if item_id in favoritos:
        favoritos.discard(item_id)
    else:
        favoritos.add(item_id)
    salvar_favoritos(favoritos)


def meses_disponiveis(itens: list[Item]) -> list[tuple[str, str]]:
    vistos: dict[str, tuple[int, int]] = {}
    for item in itens:
        mes, ano = (int(p) for p in item.mes_ano.split("/"))
        vistos.setdefault(item.mes_ano, (ano, mes))
    ordenados = sorted(vistos.items(), key=lambda par: par[1])
    return [(chave, f"{MESES_PT[mes - 1].capitalize()} {ano}") for chave, (ano, mes) in ordenados]


def mes_padrao(opcoes: list[tuple[str, str]]) -> str:
    hoje = date.today()
    chave_atual = f"{hoje.month:02d}/{hoje.year}"
    chaves = [chave for chave, _ in opcoes]
    if chave_atual in chaves:
        return chave_atual
    futuros = [c for c in chaves if (int(c.split("/")[1]), int(c.split("/")[0])) >= (hoje.year, hoje.month)]
    if futuros:
        return sorted(futuros, key=lambda c: (int(c.split("/")[1]), int(c.split("/")[0])))[0]
    return chaves[-1]


def rotulo_proximidade(dias: int) -> str:
    if dias == 0:
        return "🔵 hoje"
    if dias == 1:
        return "amanhã"
    if dias > 1:
        return f"em {dias} dias"
    return f"há {abs(dias)} dias"


def renderizar_item(item: Item, favoritos: set[str], destacar: str) -> None:
    tags = []
    if item.is_icms:
        tags.append("🟩 ICMS")
    tags.append(CATEGORIA_LABEL[item.categoria])
    if st.session_state.get("mostrar_uf_no_titulo"):
        tags.append(item.uf)
    prefixo = " · ".join(tags)
    estrela = "★" if item.item_id in favoritos else "☆"

    with st.expander(f"{prefixo} — {item.titulo}"):
        st.write(item.descricao)
        if item.fundamentacao:
            st.caption(f"**Fund. legal:** {item.fundamentacao}")
        if item.nota:
            st.info(f"**Nota:** {item.nota}")
        st.button(
            f"{estrela} Favoritar",
            key=f"fav-{item.item_id}",
            on_click=alternar_favorito,
            args=(item.item_id,),
        )


def main() -> None:
    st.set_page_config(page_title="Agenda Tributária", page_icon="🧾", layout="wide")

    itens = carregar_dados()
    favoritos = carregar_favoritos()
    opcoes_mes = meses_disponiveis(itens)

    st.title("🧾 Agenda Tributária")

    with st.sidebar:
        st.header("Filtros")

        chave_mes = st.selectbox(
            "Mês",
            options=[c for c, _ in opcoes_mes],
            format_func=lambda c: dict(opcoes_mes)[c],
            index=[c for c, _ in opcoes_mes].index(mes_padrao(opcoes_mes)),
        )

        opcoes_uf = ["FEDERAL", "TODOS"] + ESTADOS_ORDENADOS
        uf_selecionado = st.selectbox(
            "Estado",
            options=opcoes_uf,
            format_func=lambda c: "Todos os estados" if c == "TODOS" else f"{c} — {UF_NOMES[c]}",
            index=0,
        )
        st.session_state["mostrar_uf_no_titulo"] = uf_selecionado == "TODOS"

        categoria = st.radio("Categoria", ["Todas", "Principal", "Acessória"], horizontal=True)
        so_icms = st.checkbox("Só ICMS")
        proximos_7 = st.checkbox("Só próximos 7 dias")
        so_favoritos = st.checkbox("Só favoritos")
        busca = st.text_input("Buscar", placeholder="obrigação, artigo, lei…")

        st.divider()
        st.caption(
            "Atualização mensal: ao final de cada mês, rode `python merge_mes.py` com os "
            "novos PDFs da Econet para incluir o próximo período."
        )

    filtrados = [item for item in itens if item.mes_ano == chave_mes]
    if uf_selecionado == "FEDERAL":
        filtrados = [item for item in filtrados if item.uf == "FEDERAL"]
    elif uf_selecionado != "TODOS":
        filtrados = [item for item in filtrados if item.uf == uf_selecionado]

    if categoria == "Principal":
        filtrados = [item for item in filtrados if item.categoria == "PRINCIPAL"]
    elif categoria == "Acessória":
        filtrados = [item for item in filtrados if item.categoria == "ACESSORIA"]

    if so_icms:
        filtrados = [item for item in filtrados if item.is_icms]

    if proximos_7:
        hoje = date.today()
        filtrados = [item for item in filtrados if 0 <= (item.data_obj - hoje).days <= 7]

    if so_favoritos:
        filtrados = [item for item in filtrados if item.item_id in favoritos]

    if busca:
        termo = busca.lower()
        filtrados = [
            item for item in filtrados
            if termo in item.titulo.lower() or termo in item.descricao.lower() or termo in item.fundamentacao.lower()
        ]

    total = len(filtrados)
    icms_n = sum(1 for i in filtrados if i.is_icms)
    principal_n = sum(1 for i in filtrados if i.categoria == "PRINCIPAL")
    acessoria_n = sum(1 for i in filtrados if i.categoria == "ACESSORIA")
    feriado_n = sum(1 for i in filtrados if i.categoria == "FERIADO")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total no filtro", total)
    c2.metric("ICMS", icms_n)
    c3.metric("Principal", principal_n)
    c4.metric("Acessória", acessoria_n)
    c5.metric("Feriados", feriado_n)

    st.divider()

    if not filtrados:
        st.info("Nenhuma obrigação encontrada com esses filtros.")
        return

    por_data: dict[str, list[Item]] = {}
    for item in filtrados:
        por_data.setdefault(item.data, []).append(item)

    hoje = date.today()
    for data_str in sorted(por_data, key=lambda d: datetime.strptime(d, "%d/%m/%Y")):
        grupo = por_data[data_str]
        d = grupo[0].data_obj
        dias = (d - hoje).days
        dia_semana = DIAS_SEMANA_PT[d.weekday()]

        feriados = [i for i in grupo if i.categoria == "FERIADO"]
        normais = sorted(
            (i for i in grupo if i.categoria != "FERIADO"),
            key=lambda i: (0 if i.categoria == "PRINCIPAL" else 1, i.titulo),
        )

        st.markdown(
            f"### {dia_semana}, {d.day:02d} de {MESES_PT[d.month - 1]} "
            f"&nbsp;·&nbsp; {len(normais)} {'item' if len(normais) == 1 else 'itens'} "
            f"&nbsp;·&nbsp; *{rotulo_proximidade(dias)}*"
        )

        for feriado in feriados:
            st.markdown(f"🇧🇷 **Feriado nacional** — {feriado.titulo}")

        for item in normais:
            renderizar_item(item, favoritos, destacar=busca)


if __name__ == "__main__":
    main()

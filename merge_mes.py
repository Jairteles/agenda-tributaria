"""Funde os JSONs de um novo mês (um arquivo por UF) no agenda_data.json consolidado.

Uso:
    python merge_mes.py --pasta dados_brutos

Cada arquivo de entrada deve ser um array JSON de objetos com os campos:
uf, data (DD/MM/AAAA), categoria (PRINCIPAL|ACESSORIA|FERIADO), titulo, descricao,
fundamentacao, nota — no mesmo formato que os arquivos gerados pela extração dos PDFs
da Econet (peça ao Claude para extrair os PDFs do novo mês nesse formato e salvar em
`dados_brutos/agenda_<UF>.json`, um arquivo por estado + agenda_FEDERAL.json).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "agenda_data.json"

CAMPOS_OBRIGATORIOS = {"uf", "data", "categoria", "titulo", "descricao", "fundamentacao", "nota"}


def chave(item: dict) -> tuple[str, str, str]:
    return (item["uf"], item["data"], item["titulo"])


def carregar_existentes() -> list[dict]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return []


def carregar_novos(pasta: Path) -> list[dict]:
    itens: list[dict] = []
    arquivos = sorted(pasta.glob("agenda_*.json"))
    if not arquivos:
        raise SystemExit(f"Nenhum arquivo agenda_*.json encontrado em {pasta}")
    for arquivo in arquivos:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        for item in dados:
            faltando = CAMPOS_OBRIGATORIOS - item.keys()
            if faltando:
                raise SystemExit(f"{arquivo.name}: item sem os campos {faltando}: {item}")
        print(f"  {arquivo.name}: {len(dados)} itens")
        itens.extend(dados)
    return itens


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pasta", default="dados_brutos", help="pasta com os agenda_<UF>.json do novo mês")
    args = parser.parse_args()

    pasta = Path(args.pasta)
    if not pasta.is_absolute():
        pasta = BASE_DIR / pasta

    print(f"Lendo novos arquivos de {pasta}:")
    novos = carregar_novos(pasta)

    existentes = carregar_existentes()
    fundido: dict[tuple[str, str, str], dict] = {chave(item): item for item in existentes}
    antes = len(fundido)
    for item in novos:
        fundido[chave(item)] = item  # novo item substitui um igual (mesma uf+data+titulo) se já existir

    resultado = sorted(fundido.values(), key=lambda i: (i["data"], i["uf"], i["titulo"]))
    DATA_PATH.write_text(json.dumps(resultado, ensure_ascii=False, indent=None), encoding="utf-8")

    print(f"\nagenda_data.json atualizado: {antes} → {len(resultado)} itens "
          f"({len(resultado) - antes:+d}).")


if __name__ == "__main__":
    main()

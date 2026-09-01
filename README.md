# Agenda Tributária

App Streamlit com o calendário de vencimentos de ICMS (20 estados) e obrigações federais,
compilado a partir das agendas mensais da Econet. Destaca os itens de ICMS, permite buscar,
favoritar, filtrar pelos próximos 7 dias e selecionar a empresa/estabelecimento (a partir de
`Filtro.xlsx`) para já cair direto no estado correto.

Esta ferramenta é independente do backend/frontend do projeto principal (`../backend`,
`../frontend`) — é um utilitário isolado, sem banco de dados.

## Rodar

Precisa de Python 3.10+ instalado.

```bash
cd agenda-tributaria
pip install -r requirements.txt
streamlit run app.py
```

Abre em http://localhost:8501.

## Atualizar todo mês

1. Baixe os PDFs "Agenda Mensal das Obrigações Fiscais" da Econet do novo mês (20 estados +
   o PDF federal).
2. Peça ao Claude para extrair cada PDF no mesmo formato usado em `dados_brutos/agenda_*.json`
   (um array JSON por UF com os campos `uf`, `data`, `categoria`, `titulo`, `descricao`,
   `fundamentacao`, `nota`) e salvar em `dados_brutos/`, substituindo os arquivos do mês
   anterior.
3. Rode:

   ```bash
   python merge_mes.py
   ```

   Isso funde os novos itens em `agenda_data.json` sem perder os meses já carregados — o
   seletor de mês no app passa a mostrar o novo período automaticamente.

## Empresa / estabelecimento → estado

O seletor "Empresa / estabelecimento" na barra lateral é gerado a partir da coluna `FILTRO`
(coluna I) da planilha `../Filtro.xlsx` (aba "IE e IE ST"). Ao escolher uma empresa, o campo
"Estado" é preenchido automaticamente com a UF daquele estabelecimento (extraída da coluna
`UF`, formato "CIDADE - UF").

Se a planilha mudar (novo estabelecimento, empresa encerrada, mudança de UF), regenere
`empresas.json`:

```bash
python -c "
import json, openpyxl
wb = openpyxl.load_workbook('../Filtro.xlsx', data_only=True)
ws = wb['IE e IE ST']
registros = []
for codigo, cnpj, nome, ie, uf_cidade, estado, tipo, situacao, filtro in ws.iter_rows(min_row=8, values_only=True):
    if not filtro:
        continue
    cidade, _, uf = str(uf_cidade).rpartition(' - ')
    registros.append({'codigo': codigo, 'cnpj': cnpj, 'nome': nome, 'ie': ie,
                       'cidade': cidade.strip(), 'uf': uf.strip().upper(), 'filtro': filtro.strip()})
registros.sort(key=lambda r: r['codigo'])
json.dump(registros, open('empresas.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(registros), 'registros')
"
```

Estados presentes no `Filtro.xlsx` mas sem agenda carregada (hoje: SP e TO) mostram um aviso
no app em vez da lista de obrigações — para cobri-los, é preciso primeiro extrair os PDFs
desses estados como qualquer outro (ver "Atualizar todo mês").

## Estrutura

- `app.py` — o app Streamlit.
- `agenda_data.json` — dados consolidados de todos os meses carregados (usado pelo app).
- `empresas.json` — lista de empresas/estabelecimentos extraída de `../Filtro.xlsx`, usada
  pelo seletor "Empresa / estabelecimento".
- `dados_brutos/agenda_<UF>.json` — última extração por estado/federal, ponto de partida
  para o próximo `merge_mes.py`.
- `merge_mes.py` — funde um novo mês em `agenda_data.json`.
- `favoritos.json` — gerado automaticamente ao favoritar itens no app (não versionar).

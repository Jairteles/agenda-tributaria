# Agenda Tributária

App Streamlit com o calendário de vencimentos de ICMS (20 estados) e obrigações federais,
compilado a partir das agendas mensais da Econet. Destaca os itens de ICMS, permite buscar,
favoritar e filtrar pelos próximos 7 dias.

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

## Estrutura

- `app.py` — o app Streamlit.
- `agenda_data.json` — dados consolidados de todos os meses carregados (usado pelo app).
- `dados_brutos/agenda_<UF>.json` — última extração por estado/federal, ponto de partida
  para o próximo `merge_mes.py`.
- `merge_mes.py` — funde um novo mês em `agenda_data.json`.
- `favoritos.json` — gerado automaticamente ao favoritar itens no app (não versionar).

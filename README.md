# Monitor de cotacao de aluguel de carros

Aplicacao pessoal em Python para monitorar diariamente cotacoes de aluguel de carro nas locadoras Localiza e Movida, sempre com foco na agencia do Aeroporto de Porto Seguro/BA.

## 1. Visao geral do projeto

O projeto automatiza uma simulacao de aluguel com Playwright, consolida as 3 opcoes mais baratas encontradas por locadora, salva screenshots, gera saidas locais em JSON/Markdown e envia um resumo para um grupo do Telegram.

O fluxo foi desenhado para uso pessoal/familiar, sem foco comercial, e para rodar tanto localmente quanto no GitHub Actions em repositorio publico.

## 2. Tecnologias usadas

- Python 3.12
- Playwright
- requests
- pytest
- python-dotenv
- GitHub Actions

## 3. Estrutura de pastas

```text
.
|-- .github/
|   `-- workflows/
|       `-- daily_rental_monitor.yml
|-- app/
|   |-- main.py
|   |-- config.py
|   |-- logger.py
|   |-- models.py
|   |-- constants.py
|   |-- scrapers/
|   |   |-- base_scraper.py
|   |   |-- localiza.py
|   |   `-- movida.py
|   |-- services/
|   |   |-- report_service.py
|   |   |-- screenshot_service.py
|   |   `-- telegram_service.py
|   `-- utils/
|       |-- formatters.py
|       |-- helpers.py
|       `-- parsers.py
|-- logs/
|-- output/
|   |-- screenshots/
|   `-- errors/
|-- tests/
|   |-- conftest.py
|   |-- test_helpers.py
|   |-- test_parsers.py
|   |-- test_report_service.py
|   `-- test_screenshot_logic.py
|-- .env.example
|-- .gitignore
`-- requirements.txt
```

## 4. Como instalar localmente

Crie um ambiente virtual e instale as dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 5. Como instalar Playwright

Depois de instalar as dependencias Python:

```bash
python -m playwright install chromium
```

No GitHub Actions o workflow ja instala o Chromium automaticamente.

## 6. Como configurar o bot do Telegram

1. Fale com o `@BotFather`.
2. Crie um bot com o comando `/newbot`.
3. Guarde o token gerado.
4. Adicione o bot ao grupo que recebera as mensagens.
5. Dê permissao para o bot enviar mensagens e fotos no grupo.

Se quiser facilitar a leitura de mensagens do grupo pelo bot, ajuste a privacidade com `@BotFather` quando necessario.

## 7. Como descobrir o `chat_id` do grupo

Uma forma simples:

1. Adicione o bot ao grupo.
2. Envie uma mensagem qualquer no grupo.
3. Abra no navegador:

```text
https://api.telegram.org/botSEU_TOKEN/getUpdates
```

4. Procure o campo `chat`.
5. O `id` do grupo costuma ser um numero negativo.

## 8. Como rodar localmente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Preencha ao menos:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Depois execute:

```bash
python -m app.main
```

Para ver o navegador durante a automacao, ajuste:

```env
HEADLESS=false
```

## 9. Como ativar o GitHub Actions

O workflow ja esta em:

```text
.github/workflows/daily_rental_monitor.yml
```

Ele executa diariamente e tambem pode ser disparado manualmente com `workflow_dispatch`.

O cron configurado esta em UTC. O ambiente define `TZ=America/Sao_Paulo` para padronizar logs, arquivos e comportamento da aplicacao.

## 10. Como configurar secrets no GitHub

No repositorio:

1. Abra `Settings`.
2. Va em `Secrets and variables`.
3. Abra `Actions`.
4. Crie os secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

Nao versione `.env` com valores reais.

## 11. Como funcionam as screenshots

O projeto salva screenshots em:

- `output/screenshots/`
- `output/errors/`

Arquivos esperados:

- `localiza_2026-09-12_1400_to_2026-09-19_1100.png`
- `movida_2026-09-12_1400_to_2026-09-19_1100.png`
- `localiza_error_YYYYMMDD_HHMMSS.png`
- `movida_error_YYYYMMDD_HHMMSS.png`

Se possivel, a automacao tenta capturar a area de resultados. Caso nao consiga com seguranca, faz screenshot da pagina inteira.

As screenshots tambem sao usadas no envio para o Telegram e nos artifacts do GitHub Actions.

## 12. Como funcionam os fallbacks de seletores

Os scrapers usam uma abordagem defensiva para reduzir fragilidade em mudancas de layout.

Funcoes principais:

- `find_first_visible(page, selectors)`
- `click_with_fallback(page, selectors)`
- `fill_with_fallback(page, selectors, value)`
- `find_nth_visible(page, selectors, index)`
- `fill_nth_with_fallback(page, selectors, index, value)`

Ordem usada, quando aplicavel:

1. `get_by_role`
2. `get_by_label`
3. `get_by_placeholder`
4. busca por texto
5. CSS selector ou XPath como ultimo recurso

Isso e usado principalmente para:

- campo de local/agencia
- datas
- horarios
- botao de buscar
- lista de resultados
- area da screenshot

## 13. Limitacoes conhecidas

- Sites de locadoras mudam layout com frequencia e podem exigir manutencao dos seletores.
- O GitHub Actions roda em IP compartilhado; isso pode aumentar chances de bloqueio, captcha ou pagina parcial.
- A validacao de adicionais opcionais e `best-effort`. Quando nao for possivel garantir a ausencia de extras no fluxo visivel, o sistema registra observacao clara.
- Se a agencia retornada nao puder ser validada claramente como aeroporto, a coleta daquela locadora e considerada invalida.
- A Movida pode eventualmente responder com pagina de manutencao ou fluxo diferente do homepage.
- Os testes do projeto sao unitarios e nao fazem acesso real aos sites.

## 14. Como trocar datas/local no futuro

Basta alterar as variaveis:

- `RENTAL_PICKUP_LOCATION`
- `RENTAL_PICKUP_DATE`
- `RENTAL_PICKUP_TIME`
- `RENTAL_RETURN_DATE`
- `RENTAL_RETURN_TIME`

Exemplo:

```env
RENTAL_PICKUP_LOCATION=Aeroporto de Porto Seguro
RENTAL_PICKUP_DATE=20/12/2026
RENTAL_PICKUP_TIME=10:00
RENTAL_RETURN_DATE=27/12/2026
RENTAL_RETURN_TIME=09:00
```

Se no futuro quiser trocar o aeroporto fixo, atualize:

- as variaveis de ambiente
- palavras-chave de validacao em `app/constants.py`
- seletores especificos, se necessario

## 15. Observacoes sobre uso em repositorio publico

- Nao coloque tokens, chat IDs reais ou qualquer credencial no codigo.
- O `.env.example` esta sem valores reais.
- O `.gitignore` ignora `.env`, logs e saidas geradas.
- Use GitHub Secrets para tudo que for sensivel.
- O repositorio e publico apenas para aproveitar a execucao gratuita do GitHub Actions, mas o uso continua sendo pessoal/familiar.

## Configuracao por ambiente

Variaveis suportadas:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `RENTAL_PICKUP_LOCATION`
- `RENTAL_PICKUP_DATE`
- `RENTAL_PICKUP_TIME`
- `RENTAL_RETURN_DATE`
- `RENTAL_RETURN_TIME`
- `HEADLESS`
- `TIMEZONE`
- `PLAYWRIGHT_TIMEOUT_MS`
- `MAX_RETRIES`
- `SCREENSHOT_FULL_PAGE`

## Saidas locais

A cada execucao, a aplicacao atualiza:

- `logs/app.log`
- `output/latest_quote.json`
- `output/latest_quote.md`
- `output/screenshots/`
- `output/errors/`

O JSON inclui:

- parametros usados na cotacao
- resultado da Localiza
- resultado da Movida
- erros gerais
- horario da execucao
- caminhos das screenshots

## Testes

Execute:

```bash
python -m pytest -q
```

Cobertura basica atual:

- formatacao da mensagem para Telegram
- ordenacao das 3 opcoes mais baratas
- parsing de preco em reais
- comportamento com uma locadora falhando
- invalidacao quando a agencia nao parece ser aeroporto
- funcoes de fallback de seletores
- escolha de screenshot valida para envio

## Como acompanhar as execucoes no GitHub

1. Abra a aba `Actions` do repositorio.
2. Selecione o workflow `Daily Rental Monitor`.
3. Consulte os logs da execucao.
4. Baixe os artifacts quando houver necessidade de auditoria.

Os artifacts incluem `logs/` e `output/`, o que ajuda a investigar falhas de seletor, manutencao do site ou capturas de erro.

## Observacoes de manutencao

- Se o site mudar layout, revise primeiro `app/constants.py`.
- Se o problema for em um passo especifico do fluxo, revise `app/scrapers/localiza.py` ou `app/scrapers/movida.py`.
- Se o problema for so no parsing, revise `app/scrapers/base_scraper.py` e `app/utils/parsers.py`.
- Se o problema for so no envio ao Telegram, revise `app/services/telegram_service.py`.


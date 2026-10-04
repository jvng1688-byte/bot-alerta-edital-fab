# Bot Alerta Edital FAB/EEAR

Bot Telegram que monitora editais de concursos da Aeronautica (EEAR, EPCAR, QOCON, CFS) e envia alertas automaticos.

## Funcionalidades
- Monitora DOU (Diario Oficial da Uniao) e site oficial da FAB
- Filtra por palavras-chave: EEAR, EPCAR, QOCON, CFS, FAB, especialidades tecnicas
- Verificacao automatica a cada 30 min (configuravel)
- Alertas formatados no Telegram com link direto
- Deploy gratis no Railway/Render

## Stack
- Python 3.11+
- python-telegram-bot 21.x
- Playwright (raspagem JS)
- APScheduler (agendamento)
- Railway/Render (deploy)

## Configuracao Local

### 1. Clone e instale
```bash
git clone https://github.com/jvng16688/bot-alerta-edital-fab.git
cd bot-alerta-edital-fab
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Variaveis de ambiente
Copie `.env.example` para `.env` e preencha:
```env
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
CHECK_INTERVAL_MINUTES=30
```

### 3. Rode local
```bash
python main.py
```

## Deploy no Railway (Gratis)
1. Crie conta em railway.app (login com GitHub)
2. "New Project" -> "Deploy from GitHub repo" -> selecione este repo
3. Em **Variables**, adicione: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, CHECK_INTERVAL_MINUTES
4. Deploy automatico

## Deploy no Render (Alternativa Gratis)
1. Conecte repo no render.com
2. Build Command: `pip install -r requirements.txt && playwright install chromium`
3. Start Command: `python main.py`
4. Adicione as mesmas Environment Variables

## Como obter Telegram Token e Chat ID
1. **Token:** Converse com @BotFather -> /newbot -> siga instrucoes
2. **Chat ID:** Converse com @userinfobot -> copia seu ID numerico
   - Para grupo: adicione o bot no grupo e mande /start -> use o ID negativo do grupo

## Licenca
MIT - Use livremente para estudos e portfolio.
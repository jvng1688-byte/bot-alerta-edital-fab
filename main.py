"""
Bot Telegram - Alerta Edital FAB/EEAR
Monitora DOU/gov.br por editais de concursos militares (EEAR, EPCAR, QOCON, CFS)
e envia alertas formatados no Telegram.

Stack: python-telegram-bot, Playwright, APScheduler, Railway (deploy gratis)
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict

import aiohttp
from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))

KEYWORDS = [
    "EEAR", "EPCAR", "QOCON", "CFS", "FAB", "Aeronautica",
    "Estagio de Adaptacao", "Oficial", "Sargento", "Controle de Trafego Aereo",
    "Meteorologia", "Comunicacoes", "Eletronica", "Mecanica", "Armamento"
]

MONITOR_URLS = [
    "https://www.in.gov.br/consulta/-/buscar/dou?q=*",
    "https://www.gov.br/fab/pt-br/assuntos/concursos-e-selecoes",
    "https://www.fab.mil.br/concursos"
]

seen_editais = set()


async def fetch_dou_editais() -> List[Dict]:
    editais = []
    try:
        async with aiohttp.ClientSession() as session:
            for url in MONITOR_URLS[:1]:
                async with session.get(url, timeout=30) as resp:
                    html = await resp.text()
                    if any(kw.lower() in html.lower() for kw in KEYWORDS):
                        editais.append({
                            "titulo": "Edital encontrado no DOU",
                            "url": url,
                            "data": datetime.now().strftime("%d/%m/%Y"),
                            "fonte": "DOU - Imprensa Nacional"
                        })
    except Exception as e:
        logger.error(f"Erro ao buscar DOU: {e}")
    return editais


async def fetch_fab_site() -> List[Dict]:
    editais = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.fab.mil.br/concursos", wait_until="networkidle", timeout=60000)
            cards = await page.query_selector_all(".concurso-card, .card-concurso, article, .item-lista")
            for card in cards:
                text = await card.inner_text()
                if any(kw.lower() in text.lower() for kw in KEYWORDS):
                    link_el = await card.query_selector("a")
                    link = await link_el.get_attribute("href") if link_el else "https://www.fab.mil.br/concursos"
                    if link and not link.startswith("http"):
                        link = f"https://www.fab.mil.br{link}"
                    editais.append({
                        "titulo": text[:200].strip(),
                        "url": link,
                        "data": datetime.now().strftime("%d/%m/%Y"),
                        "fonte": "FAB - Concursos"
                    })
            await browser.close()
    except Exception as e:
        logger.error(f"Erro ao raspar FAB: {e}")
    return editais


async def check_new_editais() -> List[Dict]:
    global seen_editais
    all_editais = []
    all_editais.extend(await fetch_dou_editais())
    all_editais.extend(await fetch_fab_site())
    novos = []
    for edital in all_editais:
        identifier = f"{edital['titulo'][:50]}|{edital['url']}"
        if identifier not in seen_editais:
            seen_editais.add(identifier)
            novos.append(edital)
    return novos


def format_edital_message(edital: Dict) -> str:
    return (
        f"🚨 **NOVO EDITAL DETECTADO**\n\n"
        f"📋 **{edital['titulo']}**\n"
        f"📅 Data: {edital['data']}\n"
        f"🔗 Fonte: {edital['fonte']}\n"
        f"🌐 Link: {edital['url']}\n\n"
        f"#FAB #EEAR #EPCAR #QOCON #ConcursoMilitar"
    )


async def send_alert(context: ContextTypes.DEFAULT_TYPE, editais: List[Dict]):
    for edital in editais:
        message = format_edital_message(edital)
        keyboard = [[InlineKeyboardButton("🔗 Abrir Edital", url=edital['url'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="Markdown",
                reply_markup=reply_markup,
                disable_web_page_preview=False
            )
            logger.info(f"Alerta enviado: {edital['titulo'][:50]}")
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {e}")


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Iniciando verificacao programada...")
    novos = await check_new_editais()
    if novos:
        logger.info(f"{len(novos)} novo(s) edital(is) encontrado(s)")
        await send_alert(context, novos)
    else:
        logger.info("Nenhum edital novo")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Bot Alerta Edital FAB/EEAR ativo!**\n\n"
        "Monitoro editais de concursos da Aeronautica (EEAR, EPCAR, QOCON, CFS) "
        "e envio alertas automaticos aqui.\n\n"
        "Comandos:\n"
        "/status - Ver status do bot\n"
        "/check - Verificacao manual agora\n"
        "/help - Esta mensagem"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ **Bot rodando**\n"
        f"⏰ Verificacao a cada {CHECK_INTERVAL_MINUTES} min\n"
        f"📋 Editais ja vistos: {len(seen_editais)}\n"
        f"🕐 Ultima verificacao: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )


async def manual_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Verificando agora...")
    novos = await check_new_editais()
    if novos:
        await send_alert(context, novos)
        await update.message.reply_text(f"✅ {len(novos)} novo(s) edital(is) encontrado(s) e alertado(s)!")
    else:
        await update.message.reply_text("📭 Nenhum edital novo no momento.")


def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_TOKEN e TELEGRAM_CHAT_ID sao obrigatorios no .env")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("check", manual_check))
    application.add_handler(CommandHandler("help", start))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_check,
        trigger=IntervalTrigger(minutes=CHECK_INTERVAL_MINUTES),
        args=[application],
        id="edital_check",
        replace_existing=True
    )
    scheduler.start()
    
    logger.info("Bot iniciado! Verificando a cada %d minutos", CHECK_INTERVAL_MINUTES)
    
    asyncio.get_event_loop().create_task(scheduled_check(application))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
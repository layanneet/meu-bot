import json
import os
import asyncio
from flask import Flask, request

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =====================
# CONFIGURAÇÕES
# =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk")
WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL",
    "https://meu-bot-production-df5c.up.railway.app"
)

DATA_FILE = "dados.json"

# =====================
# APP TELEGRAM
# =====================
application = Application.builder().token(BOT_TOKEN).build()

# =====================
# FLASK
# =====================
app = Flask(__name__)

# =====================
# UTILIDADES
# =====================
def carregar_dados():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def garantir_usuario(dados, user_id):
    if user_id not in dados:
        dados[user_id] = {
            "saldo": 0,
            "cartoes": {}
        }

# =====================
# COMANDOS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot Financeiro\n\n"
        "Comandos disponíveis:\n"
        "/saldo\n"
        "/entrada VALOR\n"
        "/saida VALOR\n"
        "/gastocartao NOME VALOR\n"
        "/reset\n"
        "/resetcartao NOME\n"
        "/apagarcartao NOME"
    )

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    garantir_usuario(dados, uid)

    texto = f"💰 Saldo: R$ {dados[uid]['saldo']:.2f}\n\n💳 Cartões:\n"
    if not dados[uid]["cartoes"]:
        texto += "Nenhum cartão cadastrado."
    else:
        for nome, valor in dados[uid]["cartoes"].items():
            texto += f"- {nome}: R$ {valor:.2f}\n"

    await update.message.reply_text(texto)

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
    except:
        await update.message.reply_text("Uso: /entrada VALOR")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    garantir_usuario(dados, uid)

    dados[uid]["saldo"] += valor
    salvar_dados(dados)

    await update.message.reply_text(f"✅ Entrada registrada: R$ {valor:.2f}")

async def saida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
    except:
        await update.message.reply_text("Uso: /saida VALOR")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    garantir_usuario(dados, uid)

    dados[uid]["saldo"] -= valor
    salvar_dados(dados)

    await update.message.reply_text(f"❌ Saída registrada: R$ {valor:.2f}")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /gastocartao NOME VALOR")
        return

    nome = context.args[0]
    try:
        valor = float(context.args[1])
    except:
        await update.message.reply_text("Valor inválido.")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    garantir_usuario(dados, uid)

    if "cartoes" not in dados[uid]:
        dados[uid]["cartoes"] = {}

    dados[uid]["cartoes"][nome] = dados[uid]["cartoes"].get(nome, 0) + valor
    salvar_dados(dados)

    await update.message.reply_text(
        f"💳 Gasto no cartão {nome}: R$ {valor:.2f}"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    uid = str(update.effective_user.id)

    dados[uid] = {
        "saldo": 0,
        "cartoes": {}
    }
    salvar_dados(dados)

    await update.message.reply_text("🔄 Tudo foi resetado.")

async def resetcartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /resetcartao NOME")
        return

    nome = context.args[0]
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    garantir_usuario(dados, uid)

    if nome in dados[uid]["cartoes"]:
        dados[uid]["cartoes"][nome] = 0
        salvar_dados(dados)
        await update.message.reply_text(f"🔄 Cartão {nome} resetado.")
    else:
        await update.message.reply_text("Cartão não encontrado.")

async def apagarcartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /apagarcartao NOME")
        return

    nome = context.args[0]
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    garantir_usuario(dados, uid)

    if nome in dados[uid]["cartoes"]:
        del dados[uid]["cartoes"][nome]
        salvar_dados(dados)
        await update.message.reply_text(f"🗑️ Cartão {nome} apagado.")
    else:
        await update.message.reply_text("Cartão não encontrado.")

# =====================
# REGISTRO DOS HANDLERS
# =====================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("saldo", saldo))
application.add_handler(CommandHandler("entrada", entrada))
application.add_handler(CommandHandler("saida", saida))
application.add_handler(CommandHandler("gastocartao", gastocartao))
application.add_handler(CommandHandler("reset", reset))
application.add_handler(CommandHandler("resetcartao", resetcartao))
application.add_handler(CommandHandler("apagarcartao", apagarcartao))

# =====================
# WEBHOOK (FLASK SÍNCRONO)
# =====================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
def index():
    return "Bot financeiro rodando 🚀"

# =====================
# START
# =====================
if __name__ == "__main__":
    async def main():
        await application.initialize()
        await application.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
        await application.start()

    asyncio.run(main())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

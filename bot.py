import os
import json
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ================= CONFIG =================
TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
WEBHOOK_URL = "https://meu-bot-production-df5c.up.railway.app"

ADMINS = [5507658531, 5364076144]

DB_FILE = "dados.json"

# ================= BANCO =================
def carregar_dados():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def get_user(dados, user_id):
    user_id = str(user_id)
    if user_id not in dados:
        dados[user_id] = {
            "saldo": 0.0,
            "cartoes": {}
        }
    if "cartoes" not in dados[user_id]:
        dados[user_id]["cartoes"] = {}
    return dados[user_id]

def parse_valor(v):
    return float(v.replace(",", ".").replace("R$", "").strip())

# ================= COMANDOS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/saldo\n"
        "/addsaldo valor\n"
        "/gastocartao nome valor descrição\n"
        "/cartoes\n"
        "/resetgeral\n"
        "/resetcartoes\n"
        "/apagarconta id"
    )

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    user = get_user(dados, update.effective_user.id)
    await update.message.reply_text(f"💰 Saldo: R$ {user['saldo']:.2f}")

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = parse_valor(context.args[0])
    dados = carregar_dados()
    user = get_user(dados, update.effective_user.id)
    user["saldo"] += valor
    salvar_dados(dados)
    await update.message.reply_text("✅ Saldo adicionado")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Uso correto:\n/gastocartao NOME VALOR DESCRIÇÃO"
        )
        return

    nome = context.args[0]
    valor = parse_valor(context.args[1])
    descricao = " ".join(context.args[2:])

    dados = carregar_dados()
    user = get_user(dados, update.effective_user.id)

    if nome not in user["cartoes"]:
        user["cartoes"][nome] = 0.0

    user["cartoes"][nome] += valor
    salvar_dados(dados)

    await update.message.reply_text(
        f"💳 Cartão {nome}\n"
        f"Valor: R$ {valor:.2f}\n"
        f"Descrição: {descricao}"
    )

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    user = get_user(dados, update.effective_user.id)

    if not user["cartoes"]:
        await update.message.reply_text("Nenhum cartão registrado.")
        return

    texto = "💳 Cartões:\n"
    for nome, total in user["cartoes"].items():
        texto += f"- {nome}: R$ {total:.2f}\n"

    await update.message.reply_text(texto)

async def resetgeral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    salvar_dados({})
    await update.message.reply_text("🔥 Reset geral feito")

async def resetcartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    user = get_user(dados, update.effective_user.id)
    user["cartoes"] = {}
    salvar_dados(dados)
    await update.message.reply_text("💳 Cartões resetados")

async def apagarconta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    user_id = context.args[0]
    dados = carregar_dados()
    if user_id in dados:
        del dados[user_id]
        salvar_dados(dados)
        await update.message.reply_text("🗑 Conta apagada")

# ================= APP =================
app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("saldo", saldo))
application.add_handler(CommandHandler("addsaldo", addsaldo))
application.add_handler(CommandHandler("gastocartao", gastocartao))
application.add_handler(CommandHandler("cartoes", cartoes))
application.add_handler(CommandHandler("resetgeral", resetgeral))
application.add_handler(CommandHandler("resetcartoes", resetcartoes))
application.add_handler(CommandHandler("apagarconta", apagarconta))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "ok"

@app.route("/")
def index():
    return "Bot ativo"

async def set_webhook():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=8080)

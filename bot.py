import os
import json
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =====================
# CONFIGURAÇÕES
# =====================
TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
WEBHOOK_URL = "https://meu-bot-production-df5c.up.railway.app"

ADMINS = [5507658531, 5364076144]

ARQUIVO = "dados.json"

# =====================
# BANCO DE DADOS
# =====================
def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def init_usuario(user_id):
    dados = carregar_dados()
    if str(user_id) not in dados:
        dados[str(user_id)] = {
            "saldo": 0,
            "gastos": [],
            "cartoes": {}
        }
        salvar_dados(dados)

# =====================
# BOT
# =====================
app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

MENU = ReplyKeyboardMarkup(
    [
        ["💰 Saldo", "➕ Entrada"],
        ["➖ Gasto", "💳 Gasto Cartão"],
        ["🔄 Reset Geral"],
    ],
    resize_keyboard=True
)

# =====================
# COMANDOS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_usuario(user_id)
    await update.message.reply_text(
        "🤖 Bot financeiro ativo!",
        reply_markup=MENU
    )

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    user = dados[str(update.effective_user.id)]
    await update.message.reply_text(f"💰 Saldo: R$ {user['saldo']:.2f}")

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.split(" ")[1])
        dados = carregar_dados()
        user = dados[str(update.effective_user.id)]
        user["saldo"] += valor
        salvar_dados(dados)
        await update.message.reply_text("✅ Entrada adicionada")
    except:
        await update.message.reply_text("Use: ➕ Entrada 100")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.split(" ")[1])
        dados = carregar_dados()
        user = dados[str(update.effective_user.id)]
        user["saldo"] -= valor
        user["gastos"].append(valor)
        salvar_dados(dados)
        await update.message.reply_text("❌ Gasto registrado")
    except:
        await update.message.reply_text("Use: ➖ Gasto 50")

async def gasto_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, nome, valor = update.message.text.split(" ")
        valor = float(valor)

        dados = carregar_dados()
        user = dados[str(update.effective_user.id)]

        if "cartoes" not in user:
            user["cartoes"] = {}

        if nome not in user["cartoes"]:
            user["cartoes"][nome] = 0

        user["cartoes"][nome] += valor
        salvar_dados(dados)

        await update.message.reply_text(
            f"💳 Gasto no cartão {nome}: R$ {valor:.2f}"
        )
    except Exception as e:
        await update.message.reply_text(
            "Use: 💳 Gasto Cartão NUBANK 120"
        )

async def reset_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    dados = carregar_dados()
    dados[str(update.effective_user.id)] = {
        "saldo": 0,
        "gastos": [],
        "cartoes": {}
    }
    salvar_dados(dados)
    await update.message.reply_text("🔄 Reset geral feito")

# =====================
# HANDLERS
# =====================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Regex("Saldo"), saldo))
application.add_handler(MessageHandler(filters.Regex("Entrada"), entrada))
application.add_handler(MessageHandler(filters.Regex("Gasto Cartão"), gasto_cartao))
application.add_handler(MessageHandler(filters.Regex("Gasto"), gasto))
application.add_handler(MessageHandler(filters.Regex("Reset"), reset_geral))

# =====================
# WEBHOOK (FLASK)
# =====================
@app.route("/", methods=["GET"])
def index():
    return "Bot ativo"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

# =====================
# START
# =====================
if __name__ == "__main__":
    application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

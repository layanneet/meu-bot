import os
import json
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ================= CONFIG =================

TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USERS_PERMITIDOS = {
    5364076144: "Layanne",
    5507658531: "Júlio César"
}

DATA_FILE = "dados.json"

# ================= DADOS =================

def carregar_dados():
    if not os.path.exists(DATA_FILE):
        dados = {
            "saldo": 0.0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "contas_fixas": {},
            "parcelamentos_cartao": [],
            "parcelamentos_externos": []
        }
        salvar_dados(dados)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def autorizado(update: Update):
    return update.effective_user.id in USERS_PERMITIDOS

# ================= BOT =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    keyboard = [
        [InlineKeyboardButton("➕ Entrada", callback_data="entrada"),
         InlineKeyboardButton("💸 Gasto", callback_data="gasto")],
        [InlineKeyboardButton("💳 Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("🧾 Contas", callback_data="contas")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Reset Mês", callback_data="reset")]
    ]
    await update.message.reply_text(
        "🏦 Assistente Financeiro",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    valor = float(context.args[0].replace(",", "."))
    desc = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] += valor
    dados["entradas"].append({
        "valor": valor,
        "descricao": desc,
        "data": datetime.now().isoformat()
    })
    salvar_dados(dados)
    await update.message.reply_text(f"✅ Entrada registrada: R$ {valor:.2f}")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    valor = float(context.args[0].replace(",", "."))
    desc = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] -= valor
    dados["gastos"].append({
        "valor": valor,
        "descricao": desc,
        "data": datetime.now().isoformat()
    })
    salvar_dados(dados)
    await update.message.reply_text(f"💸 Gasto registrado: R$ {valor:.2f}")

async def novo_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = " ".join(context.args[:-1])
    limite = float(context.args[-1].replace(",", "."))
    dados = carregar_dados()
    dados["cartoes"][nome] = {
        "limite": limite,
        "gastos": []
    }
    salvar_dados(dados)
    await update.message.reply_text(f"💳 Cartão {nome} criado")

async def gasto_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = " ".join(context.args[:-2])
    valor = float(context.args[-2].replace(",", "."))
    desc = context.args[-1]
    dados = carregar_dados()
    if nome not in dados["cartoes"]:
        await update.message.reply_text("❌ Cartão não encontrado")
        return
    usado = sum(g["valor"] for g in dados["cartoes"][nome]["gastos"])
    if usado + valor > dados["cartoes"][nome]["limite"]:
        await update.message.reply_text("🚨 Limite excedido")
        return
    dados["cartoes"][nome]["gastos"].append({
        "valor": valor,
        "descricao": desc,
        "data": datetime.now().isoformat()
    })
    salvar_dados(dados)
    await update.message.reply_text(f"💳 Gasto no cartão {nome}: R$ {valor:.2f}")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    msg = ""
    for nome, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        msg += (
            f"💳 {nome}\n"
            f"Limite: {c['limite']}\n"
            f"Usado: {usado}\n"
            f"Disponível: {c['limite']-usado}\n\n"
        )
    await update.message.reply_text(msg or "Nenhum cartão")

async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = " ".join(context.args[:-1])
    valor = float(context.args[-1].replace(",", "."))
    dados = carregar_dados()
    dados["contas_fixas"][nome] = valor
    salvar_dados(dados)
    await update.message.reply_text(f"🧾 Conta {nome} cadastrada")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    total_gastos = sum(g["valor"] for g in dados["gastos"])
    total_cartoes = sum(
        sum(g["valor"] for g in c["gastos"])
        for c in dados["cartoes"].values()
    )
    contas = sum(dados["contas_fixas"].values())
    msg = (
        f"📊 Resumo\n\n"
        f"Saldo: {dados['saldo']}\n"
        f"Gastos: {total_gastos}\n"
        f"Cartões: {total_cartoes}\n"
        f"Contas fixas: {contas}\n"
        f"Sobra: {dados['saldo'] - contas}"
    )
    await update.message.reply_text(msg)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    dados["gastos"] = []
    for c in dados["cartoes"].values():
        c["gastos"] = []
    salvar_dados(dados)
    await update.message.reply_text("♻️ Mês resetado")

# ================= WEBHOOK =================

app_flask = Flask(__name__)

@app_flask.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

async def main():
    global application
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("entrada", entrada))
    application.add_handler(CommandHandler("gasto", gasto))
    application.add_handler(CommandHandler("novocartao", novo_cartao))
    application.add_handler(CommandHandler("gastocartao", gasto_cartao))
    application.add_handler(CommandHandler("cartoes", cartoes))
    application.add_handler(CommandHandler("conta", conta))
    application.add_handler(CommandHandler("resumo", resumo))
    application.add_handler(CommandHandler("resetmes", reset))

    await application.bot.set_webhook(f"{WEBHOOK_URL}/")
    await application.initialize()
    await application.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

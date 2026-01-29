import os
import json
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# ================= CONFIG =================

TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
WEBHOOK_URL = "https://meu-bot-production-df5c.up.railway.app"

USUARIOS = [5364076144, 5507658531]
DATA_FILE = "dados.json"

# ================= DADOS =================

def estrutura_padrao():
    return {
        "saldo": 0,
        "entradas": [],
        "gastos": [],
        "cartoes": {},
        "contas": {},
        "parcelamentos": [],
        "emprestimos": []
    }

def carregar_dados():
    if not os.path.exists(DATA_FILE):
        dados = estrutura_padrao()
        salvar_dados(dados)
        return dados

    with open(DATA_FILE, "r") as f:
        dados = json.load(f)

    # FORÇA TODAS AS CHAVES (corrige JSON antigo)
    base = estrutura_padrao()
    for k in base:
        dados.setdefault(k, base[k])

    salvar_dados(dados)
    return dados

def salvar_dados(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def parse_valor(v):
    return float(v.replace(",", "."))

# ================= SEGURANÇA =================

def autorizado(update: Update):
    return update.effective_user.id in USUARIOS

# ================= MENU =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    teclado = [
        [InlineKeyboardButton("➕ Entrada", callback_data="entrada")],
        [InlineKeyboardButton("💸 Gasto", callback_data="gasto")],
        [InlineKeyboardButton("💳 Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Reset mês", callback_data="resetmes")]
    ]

    await update.message.reply_text(
        "🏦 Menu Financeiro",
        reply_markup=InlineKeyboardMarkup(teclado)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    textos = {
        "entrada": "/entrada <valor> <descrição>",
        "gasto": "/gasto <valor> <descrição>",
        "cartoes": "/novocartao <nome> <limite>\n/gastocartao <nome> <valor> <descrição>\n/cartoes",
        "resumo": "/resumo",
        "resetmes": "/resetmes"
    }

    await q.edit_message_text(textos.get(q.data, ""))

# ================= ENTRADA =================

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])

    dados = carregar_dados()
    dados["saldo"] += valor
    dados["entradas"].append({"valor": valor, "descricao": desc})
    salvar_dados(dados)

    await update.message.reply_text(f"✅ Entrada R${valor:.2f}")

# ================= GASTO =================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])

    dados = carregar_dados()
    dados["saldo"] -= valor
    dados["gastos"].append({"valor": valor, "descricao": desc})
    salvar_dados(dados)

    await update.message.reply_text(f"💸 Gasto R${valor:.2f}")

# ================= CARTÕES =================

async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    limite = parse_valor(context.args[-1])
    nome = " ".join(context.args[:-1])

    dados = carregar_dados()
    dados["cartoes"][nome] = {"limite": limite, "gastos": []}
    salvar_dados(dados)

    await update.message.reply_text(f"💳 Cartão {nome} criado")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    valor = None
    idx = None

    for i, arg in enumerate(context.args):
        try:
            valor = parse_valor(arg)
            idx = i
            break
        except:
            continue

    if valor is None:
        await update.message.reply_text("❌ Valor inválido")
        return

    nome = " ".join(context.args[:idx])
    desc = " ".join(context.args[idx + 1:])

    dados = carregar_dados()

    if nome not in dados["cartoes"]:
        await update.message.reply_text("❌ Cartão não encontrado")
        return

    cartao = dados["cartoes"][nome]
    usado = sum(g["valor"] for g in cartao["gastos"])

    if usado + valor > cartao["limite"]:
        await update.message.reply_text("🚫 Limite estourado")
        return

    cartao["gastos"].append({"valor": valor, "descricao": desc})
    salvar_dados(dados)

    await update.message.reply_text(f"💳 {nome}: R${valor:.2f}")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()

    if not dados["cartoes"]:
        await update.message.reply_text("Nenhum cartão cadastrado")
        return

    msg = []
    for n, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        msg.append(
            f"{n}\nLimite: {c['limite']:.2f}\nUsado: {usado:.2f}\n"
        )

    await update.message.reply_text("\n".join(msg))

# ================= RESUMO =================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    await update.message.reply_text(
        f"📊 Saldo: R${dados['saldo']:.2f}"
    )

# ================= RESET =================

async def resetmes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    dados["gastos"] = []
    for c in dados["cartoes"].values():
        c["gastos"] = []
    salvar_dados(dados)
    await update.message.reply_text("♻️ Mês resetado")

# ================= APP =================

flask_app = Flask(__name__)

application: Application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buttons))
application.add_handler(CommandHandler("entrada", entrada))
application.add_handler(CommandHandler("gasto", gasto))
application.add_handler(CommandHandler("novocartao", novocartao))
application.add_handler(CommandHandler("gastocartao", gastocartao))
application.add_handler(CommandHandler("cartoes", cartoes))
application.add_handler(CommandHandler("resumo", resumo))
application.add_handler(CommandHandler("resetmes", resetmes))

@flask_app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

if __name__ == "__main__":
    async def main():
        await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
        flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

    asyncio.run(main())

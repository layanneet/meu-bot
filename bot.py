import os
import json
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

USUARIOS = [5364076144, 5507658531]  # Layanne e Júlio
DATA_FILE = "dados.json"

# ================= DADOS =================

def salvar_dados(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def carregar_dados():
    if not os.path.exists(DATA_FILE):
        dados = {
            "saldo": 0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "contas": {},
            "parcelamentos": [],
            "emprestimos": []
        }
        salvar_dados(dados)
        return dados

    with open(DATA_FILE, "r") as f:
        dados = json.load(f)

    dados.setdefault("saldo", 0)
    dados.setdefault("entradas", [])
    dados.setdefault("gastos", [])
    dados.setdefault("cartoes", {})
    dados.setdefault("contas", {})
    dados.setdefault("parcelamentos", [])
    dados.setdefault("emprestimos", [])

    return dados

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
        [InlineKeyboardButton("🧾 Contas", callback_data="contas")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Reset mês", callback_data="resetmes")],
    ]

    await update.message.reply_text(
        "🏦 *Menu Financeiro*",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    textos = {
        "entrada": "/entrada <valor> <descrição>",
        "gasto": "/gasto <valor> <descrição>",
        "cartoes": "/novocartao <nome> <limite>\n/gastocartao <nome> <valor> <descrição>\n/cartoes",
        "contas": "/conta <nome> <valor>",
        "resumo": "/resumo",
        "resetmes": "/resetmes"
    }

    await q.edit_message_text(textos.get(q.data, ""))

# ================= ENTRADAS =================

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if not context.args:
        await update.message.reply_text("Use: /entrada <valor> <descrição>")
        return

    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])

    dados = carregar_dados()
    dados["saldo"] += valor
    dados["entradas"].append({"valor": valor, "descricao": desc})
    salvar_dados(dados)

    await update.message.reply_text(f"✅ Entrada registrada: R${valor:.2f}")

# ================= GASTO =================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if not context.args:
        await update.message.reply_text("Use: /gasto <valor> <descrição>")
        return

    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])

    dados = carregar_dados()
    dados["saldo"] -= valor
    dados["gastos"].append({"valor": valor, "descricao": desc})
    salvar_dados(dados)

    await update.message.reply_text(f"💸 Gasto registrado: R${valor:.2f}")

# ================= CARTÕES =================

async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use: /novocartao <nome> <limite>")
        return

    limite = parse_valor(context.args[-1])
    nome = " ".join(context.args[:-1])

    dados = carregar_dados()
    dados["cartoes"][nome] = {"limite": limite, "gastos": []}
    salvar_dados(dados)

    await update.message.reply_text(f"💳 Cartão {nome} criado (R${limite:.2f})")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Use: /gastocartao <nome do cartão> <valor> <descrição opcional>"
        )
        return

    valor = None
    valor_index = None

    for i, arg in enumerate(context.args):
        try:
            valor = float(arg.replace(",", "."))
            valor_index = i
            break
        except ValueError:
            continue

    if valor is None:
        await update.message.reply_text("❌ Valor inválido.")
        return

    nome = " ".join(context.args[:valor_index]).strip()
    descricao = " ".join(context.args[valor_index + 1:]).strip()

    dados = carregar_dados()

    if nome not in dados["cartoes"]:
        await update.message.reply_text("❌ Cartão não encontrado.")
        return

    cartao = dados["cartoes"][nome]
    usado = sum(g["valor"] for g in cartao["gastos"])

    if usado + valor > cartao["limite"]:
        await update.message.reply_text("🚫 Limite do cartão estourado.")
        return

    cartao["gastos"].append({"valor": valor, "descricao": descricao})
    salvar_dados(dados)

    await update.message.reply_text(
        f"💳 Gasto no cartão *{nome}*\nR${valor:.2f}",
        parse_mode="Markdown"
    )

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    if not dados["cartoes"]:
        await update.message.reply_text("Nenhum cartão cadastrado.")
        return

    msg = ["💳 *Cartões*"]
    for nome, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        disp = c["limite"] - usado
        msg.append(f"\n{nome}\nLimite: {c['limite']:.2f}\nUsado: {usado:.2f}\nDisponível: {disp:.2f}")

    await update.message.reply_text("\n".join(msg), parse_mode="Markdown")

# ================= RESUMO =================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    msg = (
        f"📊 *Resumo*\n\n"
        f"Saldo: R${dados['saldo']:.2f}\n"
        f"Gastos: R${sum(g['valor'] for g in dados['gastos']):.2f}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ================= RESET =================

async def resetmes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    dados["gastos"] = []
    for c in dados["cartoes"].values():
        c["gastos"] = []
    salvar_dados(dados)
    await update.message.reply_text("♻️ Mês resetado.")

# ================= APP =================

app = Flask(__name__)

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

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    await application.update_queue.put(Update.de_json(data, application.bot))
    return "ok"

if __name__ == "__main__":
    application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

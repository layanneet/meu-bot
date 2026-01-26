import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# ================= CONFIG =================
TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
WEBHOOK_URL = "https://SEU-DOMINIO.up.railway.app"
USUARIOS = [5364076144, 5507658531]
DATA_FILE = "dados.json"

# =============== DADOS ====================
def init_dados():
    if not os.path.exists(DATA_FILE):
        dados = {
            "saldo": 0.0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "contas": {}
        }
        salvar_dados(dados)

def carregar_dados():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def autorizado(user_id):
    return user_id in USUARIOS

def parse_valor(v):
    return float(v.replace(",", "."))

# =============== MENU =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    teclado = [
        [InlineKeyboardButton("➕ Entrada", callback_data="entrada")],
        [InlineKeyboardButton("💸 Gasto", callback_data="gasto")],
        [InlineKeyboardButton("💳 Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("🧾 Contas", callback_data="contas")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Reset Mês", callback_data="reset")]
    ]
    await update.message.reply_text(
        "💰 Menu Financeiro",
        reply_markup=InlineKeyboardMarkup(teclado)
    )

async def botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    textos = {
        "entrada": "/entrada <valor> <descrição>",
        "gasto": "/gasto <valor> <descrição>",
        "cartoes": "/novocartao <nome> <limite>\n/gastocartao <nome> <valor> <desc>\n/cartoes",
        "contas": "/conta <nome> <valor>",
        "resumo": "/resumo",
        "reset": "/resetmes"
    }
    await q.edit_message_text(textos.get(q.data, ""))

# =============== ENTRADA ==================
async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    try:
        valor = parse_valor(context.args[0])
        desc = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Uso: /entrada <valor> <descrição>")
        return
    dados = carregar_dados()
    dados["saldo"] += valor
    dados["entradas"].append({
        "valor": valor,
        "descricao": desc,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"✅ Entrada registrada: R$ {valor:.2f}")

# =============== GASTO ====================
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    try:
        valor = parse_valor(context.args[0])
        desc = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Uso: /gasto <valor> <descrição>")
        return
    dados = carregar_dados()
    dados["saldo"] -= valor
    dados["gastos"].append({
        "valor": valor,
        "descricao": desc,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"💸 Gasto registrado: R$ {valor:.2f}")

# =============== CARTÕES ==================
async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    try:
        nome = " ".join(context.args[:-1])
        limite = parse_valor(context.args[-1])
    except:
        await update.message.reply_text("Uso: /novocartao <nome> <limite>")
        return
    dados = carregar_dados()
    dados["cartoes"][nome] = {"limite": limite, "gastos": []}
    salvar_dados(dados)
    await update.message.reply_text(f"💳 Cartão {nome} criado com limite R$ {limite:.2f}")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    try:
        nome = " ".join(context.args[:-2])
        valor = parse_valor(context.args[-2])
        desc = context.args[-1]
    except:
        await update.message.reply_text("Uso: /gastocartao <nome> <valor> <desc>")
        return
    dados = carregar_dados()
    if nome not in dados["cartoes"]:
        await update.message.reply_text("❌ Cartão não existe")
        return
    usado = sum(g["valor"] for g in dados["cartoes"][nome]["gastos"])
    if usado + valor > dados["cartoes"][nome]["limite"]:
        await update.message.reply_text("🚫 Limite insuficiente")
        return
    dados["cartoes"][nome]["gastos"].append({
        "valor": valor,
        "descricao": desc,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"💳 Gasto no {nome}: R$ {valor:.2f}")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    msg = []
    for nome, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        msg.append(
            f"💳 {nome}\nLimite: {c['limite']:.2f}\nUsado: {usado:.2f}\nDisponível: {c['limite']-usado:.2f}\n"
        )
    await update.message.reply_text("\n".join(msg) if msg else "Nenhum cartão.")

# =============== CONTAS ===================
async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    try:
        nome = " ".join(context.args[:-1])
        valor = parse_valor(context.args[-1])
    except:
        await update.message.reply_text("Uso: /conta <nome> <valor>")
        return
    dados = carregar_dados()
    dados["contas"][nome] = valor
    salvar_dados(dados)
    await update.message.reply_text(f"🧾 Conta {nome}: R$ {valor:.2f}")

# =============== RESUMO ===================
async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    total_cartoes = sum(
        sum(g["valor"] for g in c["gastos"])
        for c in dados["cartoes"].values()
    )
    total_contas = sum(dados["contas"].values())
    msg = (
        f"📊 RESUMO\n"
        f"Saldo: R$ {dados['saldo']:.2f}\n"
        f"Gastos: R$ {sum(g['valor'] for g in dados['gastos']):.2f}\n"
        f"Cartões: R$ {total_cartoes:.2f}\n"
        f"Contas: R$ {total_contas:.2f}"
    )
    await update.message.reply_text(msg)

# =============== RESET ====================
async def resetmes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    dados["gastos"] = []
    for c in dados["cartoes"].values():
        c["gastos"] = []
    salvar_dados(dados)
    await update.message.reply_text("♻️ Mês resetado")

# =============== APP ======================
init_dados()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("novocartao", novocartao))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("cartoes", cartoes))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("resetmes", resetmes))
app.add_handler(CallbackQueryHandler(botoes))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    url_path=TOKEN,
    webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
)

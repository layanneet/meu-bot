import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USUARIOS = [5364076144, 5507658531]
DATA_FILE = "dados.json"

# ============== DADOS =====================
def init_dados():
    if not os.path.exists(DATA_FILE):
        dados = {
            "saldo": 0.0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "contas": {}
        }
        salvar(dados)

def carregar():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def salvar(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def autorizado(user_id):
    return user_id in USUARIOS

def parse_valor(txt):
    return float(txt.replace(",", "."))

# ============== MENU ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    teclado = [
        [InlineKeyboardButton("➕ Entrada", callback_data="entrada")],
        [InlineKeyboardButton("💸 Gasto", callback_data="gasto")],
        [InlineKeyboardButton("💳 Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("🧾 Contas", callback_data="contas")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Reset mês", callback_data="reset")]
    ]
    await update.message.reply_text(
        "💰 **Menu Financeiro**",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    textos = {
        "entrada": "/entrada <valor> <descrição>",
        "gasto": "/gasto <valor> <descrição>",
        "cartoes": (
            "/novocartao <nome> <limite>\n"
            "/gastocartao <nome> <valor>\n"
            "/cartoes"
        ),
        "contas": "/conta <nome> <valor>",
        "resumo": "/resumo",
        "reset": "/resetmes"
    }
    await q.edit_message_text(textos[q.data])

# ============== ENTRADA ===================
async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    if len(context.args) < 1:
        return
    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])
    dados = carregar()
    dados["saldo"] += valor
    dados["entradas"].append({
        "valor": valor,
        "desc": desc,
        "data": str(datetime.now())
    })
    salvar(dados)
    await update.message.reply_text(f"Entrada registrada: R$ {valor:.2f}")

# ============== GASTO =====================
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    if len(context.args) < 1:
        return
    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])
    dados = carregar()
    dados["saldo"] -= valor
    dados["gastos"].append({
        "valor": valor,
        "desc": desc,
        "data": str(datetime.now())
    })
    salvar(dados)
    await update.message.reply_text(f"Gasto registrado: R$ {valor:.2f}")

# ============== CARTÕES ===================
async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    nome = " ".join(context.args[:-1])
    limite = parse_valor(context.args[-1])
    dados = carregar()
    dados["cartoes"][nome] = {"limite": limite, "gastos": []}
    salvar(dados)
    await update.message.reply_text(f"Cartão {nome} criado")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    nome = " ".join(context.args[:-1])
    valor = parse_valor(context.args[-1])
    dados = carregar()
    if nome not in dados["cartoes"]:
        await update.message.reply_text("Cartão não existe")
        return
    usado = sum(g["valor"] for g in dados["cartoes"][nome]["gastos"])
    if usado + valor > dados["cartoes"][nome]["limite"]:
        await update.message.reply_text("Limite excedido")
        return
    dados["cartoes"][nome]["gastos"].append({
        "valor": valor,
        "data": str(datetime.now())
    })
    salvar(dados)
    await update.message.reply_text(f"Gasto no {nome}: R$ {valor:.2f}")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    msg = []
    for n, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        msg.append(
            f"💳 {n}\nLimite: {c['limite']}\nUsado: {usado}\nDisponível: {c['limite']-usado}"
        )
    await update.message.reply_text("\n\n".join(msg) if msg else "Sem cartões")

# ============== CONTAS ====================
async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = " ".join(context.args[:-1])
    valor = parse_valor(context.args[-1])
    dados = carregar()
    dados["contas"][nome] = valor
    salvar(dados)
    await update.message.reply_text(f"Conta {nome} salva")

# ============== RESUMO ====================
async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    total_cartao = sum(
        sum(g["valor"] for g in c["gastos"])
        for c in dados["cartoes"].values()
    )
    contas = sum(dados["contas"].values())
    msg = (
        f"💰 Saldo: {dados['saldo']:.2f}\n"
        f"💳 Cartões: {total_cartao:.2f}\n"
        f"🧾 Contas: {contas:.2f}"
    )
    await update.message.reply_text(msg)

# ============== RESET =====================
async def resetmes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    dados["gastos"] = []
    dados["entradas"] = []
    for c in dados["cartoes"].values():
        c["gastos"] = []
    salvar(dados)
    await update.message.reply_text("Mês resetado")

# ============== INIT ======================
init_dados()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("novocartao", novocartao))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("cartoes", cartoes))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("resetmes", resetmes))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    url_path=TOKEN,
    webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
)

import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")

USERS = {
    5364076144: "Layanne",
    5507658531: "Julio"
}

ARQUIVO = "dados.json"

# ================= BASE =================

def autorizado(user_id):
    return user_id in USERS

def carregar():
    if not os.path.exists(ARQUIVO):
        return {
            "gastos": [],
            "rendas": [],
            "categorias": [],
            "contas": {},
            "cartoes": {},
            "orcamento": 0
        }
    with open(ARQUIVO, "r") as f:
        return json.load(f)

def salvar(dados):
    with open(ARQUIVO, "w") as f:
        json.dump(dados, f, indent=2)

# ================= COMANDOS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    await update.message.reply_text("💰 Bot financeiro ativo")

# ---------- GASTOS ----------
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    if len(context.args) < 1:
        await update.message.reply_text("Use: /gasto valor categoria")
        return

    try:
        valor = float(context.args[0])
    except:
        await update.message.reply_text("Valor inválido")
        return

    categoria = context.args[1] if len(context.args) > 1 else "geral"

    dados = carregar()

    if categoria not in dados["categorias"]:
        dados["categorias"].append(categoria)

    dados["gastos"].append({
        "user": update.effective_user.id,
        "valor": valor,
        "categoria": categoria,
        "data": datetime.now().strftime("%Y-%m-%d")
    })

    salvar(dados)
    await update.message.reply_text("✅ Gasto registrado")

# ---------- RENDAS ----------
async def renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Use: /renda valor")
        return

    try:
        valor = float(context.args[0])
    except:
        await update.message.reply_text("Valor inválido")
        return

    dados = carregar()
    dados["rendas"].append({
        "user": update.effective_user.id,
        "valor": valor,
        "data": datetime.now().strftime("%Y-%m-%d")
    })

    salvar(dados)
    await update.message.reply_text("💵 Renda registrada")

# ---------- ORÇAMENTO ----------
async def orcamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Use: /orcamento valor")
        return

    try:
        valor = float(context.args[0])
    except:
        await update.message.reply_text("Valor inválido")
        return

    dados = carregar()
    dados["orcamento"] = valor
    salvar(dados)

    await update.message.reply_text("🎯 Orçamento definido")

# ---------- CONTAS ----------
async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Use: /conta nome valor")
        return

    nome = context.args[0]

    try:
        valor = float(context.args[1])
    except:
        await update.message.reply_text("Valor inválido")
        return

    dados = carregar()
    dados["contas"][nome] = valor
    salvar(dados)

    await update.message.reply_text("📄 Conta adicionada")

async def contas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()

    if not dados["contas"]:
        await update.message.reply_text("Nenhuma conta cadastrada")
        return

    texto = "📄 Contas do mês\n\n"
    total = 0

    for nome, valor in dados["contas"].items():
        texto += f"{nome}: {valor}\n"
        total += valor

    texto += f"\nTotal: {total}"
    await update.message.reply_text(texto)

# ---------- CARTÕES ----------
async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Use: /novocartao nome limite")
        return

    nome = context.args[0]

    try:
        limite = float(context.args[1])
    except:
        await update.message.reply_text("Limite inválido")
        return

    dados = carregar()
    dados["cartoes"][nome] = {
        "limite": limite,
        "gastos": 0
    }

    salvar(dados)
    await update.message.reply_text("💳 Cartão criado")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Use: /gastocartao nome valor")
        return

    nome = context.args[0]

    try:
        valor = float(context.args[1])
    except:
        await update.message.reply_text("Valor inválido")
        return

    dados = carregar()

    if nome not in dados["cartoes"]:
        await update.message.reply_text("Cartão não encontrado")
        return

    dados["cartoes"][nome]["gastos"] += valor
    salvar(dados)

    if dados["cartoes"][nome]["gastos"] > dados["cartoes"][nome]["limite"]:
        await update.message.reply_text("⚠️ Limite do cartão ultrapassado")
    else:
        await update.message.reply_text("💳 Gasto no cartão registrado")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()

    if not dados["cartoes"]:
        await update.message.reply_text("Nenhum cartão cadastrado")
        return

    texto = "💳 Cartões\n\n"
    for nome, c in dados["cartoes"].items():
        texto += f"{nome}: {c['gastos']} / {c['limite']}\n"

    await update.message.reply_text(texto)

# ---------- RESUMO ----------
async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    texto = "📊 Resumo Geral\n\n"

    total_gastos = 0
    for uid, nome in USERS.items():
        soma = sum(g["valor"] for g in dados["gastos"] if g["user"] == uid)
        texto += f"{nome}: {soma}\n"
        total_gastos += soma

    total_rendas = sum(r["valor"] for r in dados["rendas"])

    texto += f"\n💵 Renda total: {total_rendas}"
    texto += f"\n💸 Gastos totais: {total_gastos}"
    texto += f"\n💰 Saldo: {total_rendas - total_gastos}"

    await update.message.reply_text(texto)

# ================= BOT =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("renda", renda))
app.add_handler(CommandHandler("orcamento", orcamento))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CommandHandler("contas", contas))
app.add_handler(CommandHandler("novocartao", novocartao))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("cartoes", cartoes))
app.add_handler(CommandHandler("resumo", resumo))

app.run_polling()

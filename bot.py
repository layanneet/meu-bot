import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

USERS = {
    5364076144: "Layanne",
    5507658531: "Julio"
}

ARQUIVO = "dados.json"

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

def autorizado(user_id):
    return user_id in USERS

# ---------------- COMANDOS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    await update.message.reply_text("💰 Bot financeiro ativo")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    dados = carregar()
    valor = float(context.args[0])
    categoria = context.args[1] if len(context.args) > 1 else "geral"

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

async def renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    dados = carregar()
    valor = float(context.args[0])
    dados["rendas"].append({
        "user": update.effective_user.id,
        "valor": valor,
        "data": datetime.now().strftime("%Y-%m-%d")
    })
    salvar(dados)
    await update.message.reply_text("💵 Renda registrada")

async def orcamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    dados["orcamento"] = float(context.args[0])
    salvar(dados)
    await update.message.reply_text("🎯 Orçamento definido")

async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    nome = context.args[0]
    valor = float(context.args[1])
    dados["contas"][nome] = valor
    salvar(dados)
    await update.message.reply_text("📄 Conta adicionada")

async def contas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    texto = ""
    total = 0
    for n, v in dados["contas"].items():
        texto += f"{n}: {v}\n"
        total += v
    texto += f"\nTotal: {total}"
    await update.message.reply_text(texto or "Nenhuma conta")

async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    nome = context.args[0]
    limite = float(context.args[1])
    dados["cartoes"][nome] = {
        "limite": limite,
        "gastos": 0
    }
    salvar(dados)
    await update.message.reply_text("💳 Cartão criado")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    nome = context.args[0]
    valor = float(context.args[1])
    dados["cartoes"][nome]["gastos"] += valor
    salvar(dados)

    if dados["cartoes"][nome]["gastos"] > dados["cartoes"][nome]["limite"]:
        await update.message.reply_text("⚠️ Limite ultrapassado")
    else:
        await update.message.reply_text("💳 Gasto no cartão registrado")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    texto = ""
    for n, c in dados["cartoes"].items():
        texto += f"{n}: {c['gastos']}/{c['limite']}\n"
    await update.message.reply_text(texto or "Nenhum cartão")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    texto = "📊 Resumo Geral\n\n"

    total_gastos = 0
    for uid, nome in USERS.items():
        soma = sum(g["valor"] for g in dados["gastos"] if g["user"] == uid)
        texto += f"{nome}: {soma}\n"
        total_gastos += soma

    total_rendas = sum(r["valor"] for r in dados["rendas"])
    texto += f"\nRenda total: {total_rendas}"
    texto += f"\nGastos totais: {total_gastos}"
    texto += f"\nSaldo: {total_rendas - total_gastos}"

    await update.message.reply_text(texto)

# ---------------- BOT ----------------

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

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

# ========= CONFIG =========
TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
WEBHOOK_URL = "https://meu-bot-production-df5c.up.railway.app"
DATA_FILE = "dados.json"
USUARIOS = [5364076144, 5507658531]

# ========= DADOS =========
def init_dados():
    if not os.path.exists(DATA_FILE):
        dados = {
            "saldo": 0.0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "parcelamentos_cartao": [],
            "contas": {},
            "emprestimos": [],
            "mes_ref": datetime.now().strftime("%Y-%m")
        }
        salvar_dados(dados)

def carregar_dados():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def autorizado(update: Update):
    return update.effective_user and update.effective_user.id in USUARIOS

def parse_valor(v):
    return float(v.replace(",", "."))

# ========= MENU =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    teclado = [
        [InlineKeyboardButton("➕ Entrada", callback_data="help_entrada"),
         InlineKeyboardButton("💸 Gasto", callback_data="help_gasto")],
        [InlineKeyboardButton("💳 Cartões", callback_data="help_cartoes"),
         InlineKeyboardButton("🧾 Contas", callback_data="help_contas")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo"),
         InlineKeyboardButton("♻️ Reset Mês", callback_data="resetmes")]
    ]
    await update.message.reply_text(
        "Menu Financeiro 💰",
        reply_markup=InlineKeyboardMarkup(teclado)
    )

async def menu_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    textos = {
        "help_entrada": "/entrada valor descrição",
        "help_gasto": "/gasto valor descrição",
        "help_cartoes": "/novocartao nome limite\n/gastocartao nome valor descrição\n/cartoes",
        "help_contas": "/conta nome valor",
    }
    if q.data in textos:
        await q.edit_message_text(textos[q.data])

# ========= ENTRADA =========
async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /entrada valor descrição")
        return
    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] += valor
    dados["entradas"].append({"valor": valor, "desc": desc})
    salvar_dados(dados)
    await update.message.reply_text(f"Entrada registrada: R$ {valor:.2f}")

# ========= GASTO =========
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /gasto valor descrição")
        return
    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] -= valor
    dados["gastos"].append({"valor": valor, "desc": desc})
    salvar_dados(dados)
    await update.message.reply_text(f"Gasto registrado: R$ {valor:.2f}")

# ========= CARTÕES =========
async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /novocartao nome limite")
        return
    nome = " ".join(context.args[:-1])
    limite = parse_valor(context.args[-1])
    dados = carregar_dados()
    dados["cartoes"][nome] = {"limite": limite, "gastos": []}
    salvar_dados(dados)
    await update.message.reply_text(f"Cartão {nome} criado com limite R$ {limite:.2f}")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /gastocartao nome valor descrição")
        return
    valor = parse_valor(context.args[-2])
    nome = " ".join(context.args[:-2])
    desc = context.args[-1]
    dados = carregar_dados()
    if nome not in dados["cartoes"]:
        await update.message.reply_text("Cartão não existe.")
        return
    usado = sum(g["valor"] for g in dados["cartoes"][nome]["gastos"])
    if usado + valor > dados["cartoes"][nome]["limite"]:
        await update.message.reply_text("Limite insuficiente.")
        return
    dados["cartoes"][nome]["gastos"].append({"valor": valor, "desc": desc})
    salvar_dados(dados)
    await update.message.reply_text(f"Gasto no cartão {nome}: R$ {valor:.2f}")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    msg = []
    for n, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        msg.append(f"💳 {n}\nLimite: {c['limite']:.2f}\nUsado: {usado:.2f}\nDisp: {c['limite']-usado:.2f}")
    await update.message.reply_text("\n\n".join(msg) if msg else "Nenhum cartão.")

# ========= CONTAS =========
async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /conta nome valor")
        return
    nome = " ".join(context.args[:-1])
    valor = parse_valor(context.args[-1])
    dados = carregar_dados()
    dados["contas"][nome] = valor
    salvar_dados(dados)
    await update.message.reply_text(f"Conta {nome} cadastrada.")

# ========= EMPRÉSTIMOS =========
async def emprestimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /emprestimo nome total parcelas descrição")
        return
    nome = context.args[0]
    total = parse_valor(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:])
    dados = carregar_dados()
    dados["emprestimos"].append({
        "nome": nome,
        "total": total,
        "parcelas": parcelas,
        "restantes": parcelas,
        "parcela_valor": round(total/parcelas, 2),
        "desc": desc
    })
    salvar_dados(dados)
    await update.message.reply_text("Empréstimo registrado.")

async def emprestimos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    msg = []
    for e in dados["emprestimos"]:
        msg.append(f"{e['nome']} - {e['restantes']}x R$ {e['parcela_valor']:.2f}")
    await update.message.reply_text("\n".join(msg) if msg else "Nenhum empréstimo.")

# ========= RESET =========
async def resetmes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    for e in list(dados["emprestimos"]):
        dados["saldo"] -= e["parcela_valor"]
        e["restantes"] -= 1
        if e["restantes"] <= 0:
            dados["emprestimos"].remove(e)
    for c in dados["cartoes"].values():
        c["gastos"] = []
    salvar_dados(dados)
    await update.message.reply_text("Mês resetado.")

# ========= RESUMO =========
async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    d = carregar_dados()
    total_cartao = sum(sum(g["valor"] for g in c["gastos"]) for c in d["cartoes"].values())
    total_contas = sum(d["contas"].values())
    total_emp = sum(e["parcela_valor"] for e in d["emprestimos"])
    msg = (
        f"💰 Saldo: R$ {d['saldo']:.2f}\n"
        f"💳 Cartões: R$ {total_cartao:.2f}\n"
        f"🧾 Contas: R$ {total_contas:.2f}\n"
        f"📉 Empréstimos: R$ {total_emp:.2f}\n"
        f"📊 Sobra: R$ {d['saldo'] - total_contas - total_emp:.2f}"
    )
    await update.message.reply_text(msg)

# ========= MAIN =========
init_dados()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu_help))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("novocartao", novocartao))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("cartoes", cartoes))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CommandHandler("emprestimo", emprestimo))
app.add_handler(CommandHandler("emprestimos", emprestimos))
app.add_handler(CommandHandler("resetmes", resetmes))
app.add_handler(CommandHandler("resumo", resumo))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    url_path=TOKEN,
    webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
  )

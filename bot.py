import os
import json
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN", "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://meu-bot-production-df5c.up.railway.app")

USUARIOS_PERMITIDOS = [5364076144, 5507658531]  # Layanne e Júlio
DADOS_ARQ = "dados.json"
GRUPO = "financeiro_unico"

app_flask = Flask(__name__)

# ================= DADOS =================
def carregar():
    if not os.path.exists(DADOS_ARQ):
        return {}
    with open(DADOS_ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar(d):
    with open(DADOS_ARQ, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def grupo(d):
    d.setdefault(GRUPO, {
        "saldo": 0,
        "cartoes": {},
        "parcelamentos": [],
        "emprestimos": [],
        "contas": [],
        "historico": [],
        "mes": datetime.now().strftime("%m/%Y")
    })
    return d[GRUPO]

def valor(v):
    return float(v.replace(",", "."))

def ok(uid):
    return uid in USUARIOS_PERMITIDOS

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update.effective_user.id):
        return
    teclado = [
        ["/addcartao", "/cartoes"],
        ["/parcelado", "/parcelamentos"],
        ["/emprestimo", "/emprestimos"],
        ["/addconta", "/resumo"],
        ["/resetmes"]
    ]
    await update.message.reply_text(
        "💰 Assistente Financeiro",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# ================= CARTÕES =================
async def addcartao(update, context):
    d = carregar()
    g = grupo(d)
    nome = context.args[0]
    limite = valor(context.args[1])
    g["cartoes"][nome] = {"limite": limite, "fatura": 0}
    salvar(d)
    await update.message.reply_text("💳 Cartão adicionado.")

async def cartoes(update, context):
    g = grupo(carregar())
    if not g["cartoes"]:
        await update.message.reply_text("Nenhum cartão.")
        return
    msg = "💳 Cartões:\n"
    for i, (n, c) in enumerate(g["cartoes"].items(), 1):
        msg += f"{i}. {n} — Fatura R$ {c['fatura']:.2f}\n"
    await update.message.reply_text(msg)

async def gastocartao(update, context):
    d = carregar()
    g = grupo(d)
    nome = context.args[0]
    valor_g = valor(context.args[1])
    desc = " ".join(context.args[2:])

    if nome not in g["cartoes"]:
        await update.message.reply_text("Cartão não encontrado.")
        return

    g["cartoes"][nome]["fatura"] += valor_g
    g["historico"].append({
        "tipo": "cartao",
        "usuario": update.effective_user.first_name,
        "valor": valor_g,
        "desc": desc
    })
    salvar(d)
    await update.message.reply_text("💳 Gasto no cartão registrado.")

async def excluircartao(update, context):
    d = carregar()
    g = grupo(d)
    idx = int(context.args[0]) - 1
    nome = list(g["cartoes"].keys())[idx]
    del g["cartoes"][nome]
    salvar(d)
    await update.message.reply_text("Cartão removido.")

# ================= PARCELADO =================
async def parcelado(update, context):
    d = carregar()
    g = grupo(d)
    cartao = context.args[0]
    total = valor(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:])

    g["parcelamentos"].append({
        "cartao": cartao,
        "valor": total / parcelas,
        "restantes": parcelas,
        "desc": desc
    })
    salvar(d)
    await update.message.reply_text("🧾 Parcelamento criado.")

async def parcelamentos(update, context):
    g = grupo(carregar())
    msg = "🧾 Parcelamentos:\n"
    for i, p in enumerate(g["parcelamentos"], 1):
        msg += f"{i}. {p['desc']} — {p['restantes']}x R$ {p['valor']:.2f}\n"
    await update.message.reply_text(msg)

async def cancelarparcelado(update, context):
    d = carregar()
    g = grupo(d)
    idx = int(context.args[0]) - 1
    g["parcelamentos"].pop(idx)
    salvar(d)
    await update.message.reply_text("Parcelamento cancelado.")

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    d = carregar()
    g = grupo(d)
    total = valor(context.args[0])
    desc = " ".join(context.args[1:])
    g["emprestimos"].append({"valor": total, "desc": desc})
    salvar(d)
    await update.message.reply_text("📉 Empréstimo adicionado.")

async def emprestimos(update, context):
    g = grupo(carregar())
    msg = "📉 Empréstimos:\n"
    for i, e in enumerate(g["emprestimos"], 1):
        msg += f"{i}. {e['desc']} — R$ {e['valor']:.2f}\n"
    await update.message.reply_text(msg)

async def cancelaremprestimo(update, context):
    d = carregar()
    g = grupo(d)
    g["emprestimos"].pop(int(context.args[0]) - 1)
    salvar(d)
    await update.message.reply_text("Empréstimo removido.")

# ================= CONTAS =================
async def addconta(update, context):
    d = carregar()
    g = grupo(d)
    nome = context.args[0]
    valor_c = valor(context.args[1])
    g["contas"].append({"nome": nome, "valor": valor_c})
    salvar(d)
    await update.message.reply_text("📌 Conta adicionada.")

async def excluirconta(update, context):
    d = carregar()
    g = grupo(d)
    g["contas"].pop(int(context.args[0]) - 1)
    salvar(d)
    await update.message.reply_text("Conta removida.")

# ================= RESET =================
async def resetmes(update, context):
    d = carregar()
    g = grupo(d)

    for p in list(g["parcelamentos"]):
        g["cartoes"][p["cartao"]]["fatura"] += p["valor"]
        p["restantes"] -= 1
        if p["restantes"] <= 0:
            g["parcelamentos"].remove(p)

    for c in g["contas"]:
        g["saldo"] -= c["valor"]

    g["mes"] = datetime.now().strftime("%m/%Y")
    salvar(d)
    await update.message.reply_text("🔄 Mês avançado.")

async def reset_geral(update, context):
    salvar({})
    await update.message.reply_text("⚠️ RESET TOTAL feito.")

# ================= RESUMOS =================
async def resumo(update, context):
    g = grupo(carregar())
    msg = f"📊 RESUMO {g['mes']}\nSaldo: R$ {g['saldo']:.2f}\n"
    msg += "\n💳 Cartões:\n"
    for n, c in g["cartoes"].items():
        msg += f"{n}: R$ {c['fatura']:.2f}\n"
    await update.message.reply_text(msg)

async def dividas(update, context):
    g = grupo(carregar())
    total = sum(e["valor"] for e in g["emprestimos"])
    await update.message.reply_text(f"💸 Dívida total: R$ {total:.2f}")

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

handlers = {
    "start": start,
    "addcartao": addcartao,
    "cartoes": cartoes,
    "gastocartao": gastocartao,
    "excluircartao": excluircartao,
    "parcelado": parcelado,
    "parcelamentos": parcelamentos,
    "cancelarparcelado": cancelarparcelado,
    "emprestimo": emprestimo,
    "emprestimos": emprestimos,
    "cancelaremprestimo": cancelaremprestimo,
    "addconta": addconta,
    "excluirconta": excluirconta,
    "resetmes": resetmes,
    "reset_geral": reset_geral,
    "resumo": resumo,
    "dividas": dividas
}

for c, f in handlers.items():
    application.add_handler(CommandHandler(c, f))

@app_flask.route("/", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )

import os
import json
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN", "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USUARIOS_PERMITIDOS = [5364076144, 5507658531]  # Layanne e Júlio
DADOS_ARQ = "dados.json"

app_flask = Flask(__name__)

# ================= DADOS =================
def carregar_dados():
    if not os.path.exists(DADOS_ARQ):
        return {}
    with open(DADOS_ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DADOS_ARQ, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def usuario_ok(user_id):
    return user_id in USUARIOS_PERMITIDOS

def valor_num(v):
    return float(v.replace(",", "."))

# ================= BOT =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_ok(update.effective_user.id):
        return

    teclado = [
        ["/entrada", "/gasto"],
        ["/novocartao", "/cartoes"],
        ["/parcelado", "/parcelamentos"],
        ["/emprestimo", "/emprestimos"],
        ["/conta", "/resetmes"],
        ["/resumo"]
    ]

    await update.message.reply_text(
        "💰 Assistente Financeiro",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# ================= ENTRADA / GASTO =================
async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, {"saldo": 0, "historico": [], "cartoes": {}, "parcelas": [], "emprestimos": [], "contas": []})

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) if len(context.args) > 1 else "Entrada"

    dados[uid]["saldo"] += valor
    dados[uid]["historico"].append({"tipo": "entrada", "valor": valor, "desc": desc})

    salvar_dados(dados)
    await update.message.reply_text(f"✅ Entrada registrada: R$ {valor:.2f}")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) if len(context.args) > 1 else "Gasto"

    dados[uid]["saldo"] -= valor
    dados[uid]["historico"].append({"tipo": "gasto", "valor": valor, "desc": desc})

    salvar_dados(dados)
    await update.message.reply_text(f"❌ Gasto registrado: R$ {valor:.2f}")

# ================= CARTÕES =================
async def novocartao(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    nome = context.args[0]
    limite = valor_num(context.args[1])

    dados[uid]["cartoes"][nome] = {"limite": limite, "fatura": 0}

    salvar_dados(dados)
    await update.message.reply_text(f"💳 Cartão {nome} criado.")

async def cartoes(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    msg = "💳 Cartões:\n"
    for c, info in dados[uid]["cartoes"].items():
        msg += f"{c}: Fatura R$ {info['fatura']:.2f} / Limite R$ {info['limite']:.2f}\n"

    await update.message.reply_text(msg)

# ================= PARCELADO CARTÃO =================
async def parcelado(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    cartao = context.args[0]
    total = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) if len(context.args) > 3 else "Parcelado"

    valor_parcela = total / parcelas

    dados[uid]["parcelas"].append({
        "cartao": cartao,
        "valor": valor_parcela,
        "restantes": parcelas,
        "desc": desc
    })

    salvar_dados(dados)
    await update.message.reply_text(f"🧾 Parcelado criado: {parcelas}x R$ {valor_parcela:.2f}")

async def parcelamentos(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    msg = "🧾 Parcelamentos:\n"
    for p in dados[uid]["parcelas"]:
        msg += f"{p['desc']} - {p['restantes']} meses - R$ {p['valor']:.2f}\n"

    await update.message.reply_text(msg)

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    nome = context.args[0]
    total = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) if len(context.args) > 3 else nome

    dados[uid]["emprestimos"].append({
        "nome": nome,
        "valor": total / parcelas,
        "restantes": parcelas,
        "desc": desc
    })

    salvar_dados(dados)
    await update.message.reply_text("📉 Empréstimo registrado.")

async def emprestimos(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    msg = "📉 Empréstimos:\n"
    for e in dados[uid]["emprestimos"]:
        msg += f"{e['desc']} - {e['restantes']} meses - R$ {e['valor']:.2f}\n"

    await update.message.reply_text(msg)

# ================= CONTAS =================
async def conta(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    nome = context.args[0]
    valor = valor_num(context.args[1])

    dados[uid]["contas"].append({"nome": nome, "valor": valor})

    salvar_dados(dados)
    await update.message.reply_text("📌 Conta fixa registrada.")

# ================= RESET MENSAL =================
async def resetmes(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    # Parcelas cartão
    for p in list(dados[uid]["parcelas"]):
        dados[uid]["cartoes"][p["cartao"]]["fatura"] += p["valor"]
        p["restantes"] -= 1
        if p["restantes"] <= 0:
            dados[uid]["parcelas"].remove(p)

    # Empréstimos
    for e in list(dados[uid]["emprestimos"]):
        dados[uid]["saldo"] -= e["valor"]
        e["restantes"] -= 1
        if e["restantes"] <= 0:
            dados[uid]["emprestimos"].remove(e)

    # Contas
    for c in dados[uid]["contas"]:
        dados[uid]["saldo"] -= c["valor"]

    salvar_dados(dados)
    await update.message.reply_text("🔄 Mês avançado com sucesso.")

# ================= RESUMO =================
async def resumo(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    d = dados[uid]
    msg = f"""
📊 RESUMO
Saldo: R$ {d['saldo']:.2f}

💳 Cartões:
"""
    for c, info in d["cartoes"].items():
        msg += f"{c}: R$ {info['fatura']:.2f}\n"

    msg += "\n📉 Empréstimos:\n"
    for e in d["emprestimos"]:
        msg += f"{e['desc']} ({e['restantes']} meses)\n"

    await update.message.reply_text(msg)

# ================= FLASK WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("entrada", entrada))
application.add_handler(CommandHandler("gasto", gasto))
application.add_handler(CommandHandler("novocartao", novocartao))
application.add_handler(CommandHandler("cartoes", cartoes))
application.add_handler(CommandHandler("parcelado", parcelado))
application.add_handler(CommandHandler("parcelamentos", parcelamentos))
application.add_handler(CommandHandler("emprestimo", emprestimo))
application.add_handler(CommandHandler("emprestimos", emprestimos))
application.add_handler(CommandHandler("conta", conta))
application.add_handler(CommandHandler("resetmes", resetmes))
application.add_handler(CommandHandler("resumo", resumo))

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

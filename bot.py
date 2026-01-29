import os
import json
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN", "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USUARIOS_PERMITIDOS = [5364076144, 5507658531]
DADOS_ARQ = "dados.json"

app_flask = Flask(__name__)

# ================= UTIL =================
def carregar_dados():
    if not os.path.exists(DADOS_ARQ):
        return {}
    with open(DADOS_ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DADOS_ARQ, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def usuario_ok(uid):
    return uid in USUARIOS_PERMITIDOS

def valor_num(v):
    return float(v.replace(",", "."))

def base_usuario(dados, uid):
    dados.setdefault(uid, {
        "saldo": 0,
        "historico": [],
        "cartoes": {},
        "parcelas": [],
        "emprestimos": [],
        "contas": []
    })

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_ok(update.effective_user.id):
        return
    teclado = [
        ["/entrada", "/gasto"],
        ["/novocartao", "/cartoes"],
        ["/parcelado", "/parcelamentos"],
        ["/emprestimo", "/emprestimos"],
        ["/conta", "/contas"],
        ["/resetmes", "/resumo"]
    ]
    await update.message.reply_text(
        "💰 Assistente Financeiro",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# ================= ENTRADA / GASTO =================
async def entrada(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    if not context.args:
        await update.message.reply_text("Uso: /entrada valor descrição")
        return

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Entrada"

    dados[uid]["saldo"] += valor
    dados[uid]["historico"].append({"tipo": "entrada", "valor": valor, "desc": desc})

    salvar_dados(dados)
    await update.message.reply_text(f"✅ Entrada R$ {valor:.2f}")

async def gasto(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    if not context.args:
        await update.message.reply_text("Uso: /gasto valor descrição")
        return

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Gasto"

    dados[uid]["saldo"] -= valor
    dados[uid]["historico"].append({"tipo": "gasto", "valor": valor, "desc": desc})

    salvar_dados(dados)
    await update.message.reply_text(f"❌ Gasto R$ {valor:.2f}")

# ================= CARTÕES =================
async def novocartao(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    nome = context.args[0]
    limite = valor_num(context.args[1])

    dados[uid]["cartoes"][nome] = {"limite": limite, "fatura": 0}
    salvar_dados(dados)

    await update.message.reply_text(f"💳 Cartão {nome} criado")

async def cartoes(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    msg = "💳 Cartões:\n"
    for n, c in dados[uid]["cartoes"].items():
        msg += f"{n} | Fatura R$ {c['fatura']:.2f} | Limite R$ {c['limite']:.2f}\n"

    await update.message.reply_text(msg or "Nenhum cartão")

# ================= PARCELADO =================
async def parcelado(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    cartao = context.args[0]
    total = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) or "Parcelado"

    dados[uid]["parcelas"].append({
        "cartao": cartao,
        "valor": total / parcelas,
        "restantes": parcelas,
        "desc": desc
    })

    salvar_dados(dados)
    await update.message.reply_text("🧾 Parcelado criado")

async def parcelamentos(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    msg = "🧾 Parcelamentos:\n"
    for i, p in enumerate(dados[uid]["parcelas"], 1):
        msg += f"{i}️⃣ {p['desc']} - {p['restantes']}x R$ {p['valor']:.2f}\n"

    await update.message.reply_text(msg or "Nenhum parcelamento")

async def cancelarparcelado(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    idx = int(context.args[0]) - 1
    dados[uid]["parcelas"].pop(idx)

    salvar_dados(dados)
    await update.message.reply_text("🗑️ Parcelamento removido")

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    nome = context.args[0]
    total = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) or nome

    dados[uid]["emprestimos"].append({
        "nome": nome,
        "valor": total / parcelas,
        "restantes": parcelas,
        "desc": desc
    })

    salvar_dados(dados)
    await update.message.reply_text("📉 Empréstimo criado")

async def emprestimos(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    msg = "📉 Empréstimos:\n"
    for i, e in enumerate(dados[uid]["emprestimos"], 1):
        msg += f"{i}️⃣ {e['desc']} - {e['restantes']}x R$ {e['valor']:.2f}\n"

    await update.message.reply_text(msg or "Nenhum empréstimo")

async def cancelaremprestimo(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    idx = int(context.args[0]) - 1
    dados[uid]["emprestimos"].pop(idx)

    salvar_dados(dados)
    await update.message.reply_text("🗑️ Empréstimo removido")

# ================= CONTAS =================
async def conta(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    dados[uid]["contas"].append({
        "nome": context.args[0],
        "valor": valor_num(context.args[1])
    })

    salvar_dados(dados)
    await update.message.reply_text("📌 Conta adicionada")

async def contas(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    msg = "📌 Contas:\n"
    for i, c in enumerate(dados[uid]["contas"], 1):
        msg += f"{i}️⃣ {c['nome']} R$ {c['valor']:.2f}\n"

    await update.message.reply_text(msg or "Nenhuma conta")

async def excluirconta(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    idx = int(context.args[0]) - 1
    dados[uid]["contas"].pop(idx)

    salvar_dados(dados)
    await update.message.reply_text("🗑️ Conta removida")

# ================= RESET =================
async def resetmes(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    for p in list(dados[uid]["parcelas"]):
        dados[uid]["cartoes"][p["cartao"]]["fatura"] += p["valor"]
        p["restantes"] -= 1
        if p["restantes"] <= 0:
            dados[uid]["parcelas"].remove(p)

    for e in list(dados[uid]["emprestimos"]):
        dados[uid]["saldo"] -= e["valor"]
        e["restantes"] -= 1
        if e["restantes"] <= 0:
            dados[uid]["emprestimos"].remove(e)

    for c in dados[uid]["contas"]:
        dados[uid]["saldo"] -= c["valor"]

    salvar_dados(dados)
    await update.message.reply_text("🔄 Mês avançado")

# ================= RESUMO =================
async def resumo(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    base_usuario(dados, uid)

    d = dados[uid]
    msg = f"📊 RESUMO\nSaldo: R$ {d['saldo']:.2f}\n"
    await update.message.reply_text(msg)

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("entrada", entrada))
application.add_handler(CommandHandler("gasto", gasto))
application.add_handler(CommandHandler("novocartao", novocartao))
application.add_handler(CommandHandler("cartoes", cartoes))
application.add_handler(CommandHandler("parcelado", parcelado))
application.add_handler(CommandHandler("parcelamentos", parcelamentos))
application.add_handler(CommandHandler("cancelarparcelado", cancelarparcelado))
application.add_handler(CommandHandler("emprestimo", emprestimo))
application.add_handler(CommandHandler("emprestimos", emprestimos))
application.add_handler(CommandHandler("cancelaremprestimo", cancelaremprestimo))
application.add_handler(CommandHandler("conta", conta))
application.add_handler(CommandHandler("contas", contas))
application.add_handler(CommandHandler("excluirconta", excluirconta))
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

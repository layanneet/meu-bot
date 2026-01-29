import os
import json
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USUARIOS_PERMITIDOS = [5364076144, 5507658531]
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

def usuario_ok(uid):
    return uid in USUARIOS_PERMITIDOS

def valor_num(v):
    return float(v.replace(",", "."))

def init_user(dados, uid):
    dados.setdefault(uid, {
        "saldo": 0,
        "historico": [],
        "cartoes": {},
        "parcelas": [],
        "emprestimos": [],
        "contas": []
    })

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
async def entrada(update, context):
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /entrada 100 descrição")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Entrada"

    dados[uid]["saldo"] += valor
    dados[uid]["historico"].append({"tipo": "entrada", "valor": valor, "desc": desc})

    salvar_dados(dados)
    await update.message.reply_text(f"✅ Entrada registrada: R$ {valor:.2f}")

async def gasto(update, context):
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /gasto 50 descrição")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Gasto"

    dados[uid]["saldo"] -= valor
    dados[uid]["historico"].append({"tipo": "gasto", "valor": valor, "desc": desc})

    salvar_dados(dados)
    await update.message.reply_text(f"❌ Gasto registrado: R$ {valor:.2f}")

# ================= CARTÕES =================
async def novocartao(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /novocartao nome limite")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    nome = context.args[0]
    limite = valor_num(context.args[1])

    dados[uid]["cartoes"][nome] = {"limite": limite, "fatura": 0}
    salvar_dados(dados)

    await update.message.reply_text(f"💳 Cartão {nome} criado.")

async def cartoes(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    if not dados[uid]["cartoes"]:
        await update.message.reply_text("Nenhum cartão cadastrado.")
        return

    msg = "💳 Cartões:\n"
    for c, i in dados[uid]["cartoes"].items():
        msg += f"{c}: R$ {i['fatura']:.2f} / {i['limite']:.2f}\n"

    await update.message.reply_text(msg)

# ================= PARCELADO =================
async def parcelado(update, context):
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /parcelado cartao total parcelas descrição")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    cartao = context.args[0]
    total = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) or "Parcelado"

    valor_p = total / parcelas

    dados[uid]["parcelas"].append({
        "cartao": cartao,
        "valor": valor_p,
        "restantes": parcelas,
        "desc": desc
    })

    salvar_dados(dados)
    await update.message.reply_text(f"🧾 {parcelas}x de R$ {valor_p:.2f}")

async def parcelamentos(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    if not dados[uid]["parcelas"]:
        await update.message.reply_text("Nenhum parcelamento ativo.")
        return

    msg = "🧾 Parcelamentos:\n"
    for p in dados[uid]["parcelas"]:
        msg += f"{p['desc']} - {p['restantes']}x R$ {p['valor']:.2f}\n"

    await update.message.reply_text(msg)

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /emprestimo nome total parcelas")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    nome = context.args[0]
    total = valor_num(context.args[1])
    parcelas = int(context.args[2])

    dados[uid]["emprestimos"].append({
        "desc": nome,
        "valor": total / parcelas,
        "restantes": parcelas
    })

    salvar_dados(dados)
    await update.message.reply_text("📉 Empréstimo registrado.")

async def emprestimos(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    if not dados[uid]["emprestimos"]:
        await update.message.reply_text("Nenhum empréstimo ativo.")
        return

    msg = "📉 Empréstimos:\n"
    for e in dados[uid]["emprestimos"]:
        msg += f"{e['desc']} - {e['restantes']}x\n"

    await update.message.reply_text(msg)

# ================= RESET =================
async def resetmes(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

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
    await update.message.reply_text("🔄 Mês avançado.")

# ================= RESUMO =================
async def resumo(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    d = dados[uid]
    msg = f"📊 RESUMO\nSaldo: R$ {d['saldo']:.2f}\n\n💳 Cartões:\n"
    for c, i in d["cartoes"].items():
        msg += f"{c}: R$ {i['fatura']:.2f}\n"

    await update.message.reply_text(msg)

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

handlers = [
    ("start", start), ("entrada", entrada), ("gasto", gasto),
    ("novocartao", novocartao), ("cartoes", cartoes),
    ("parcelado", parcelado), ("parcelamentos", parcelamentos),
    ("emprestimo", emprestimo), ("emprestimos", emprestimos),
    ("resetmes", resetmes), ("resumo", resumo),
]

for cmd, fn in handlers:
    application.add_handler(CommandHandler(cmd, fn))

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

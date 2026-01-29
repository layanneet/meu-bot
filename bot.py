import os
import json
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
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

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        ["/entrada", "/gasto"],
        ["/gastocartao"],
        ["/novocartao", "/cartoes"],
        ["/parcelado", "/parcelamentos"],
        ["/emprestimo", "/emprestimos"],
        ["/conta", "/excluirconta"],
        ["/resetmes", "/resetgeral"],
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

    await update.message.reply_text(f"✅ Entrada R$ {valor:.2f}")

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

    await update.message.reply_text(f"❌ Gasto R$ {valor:.2f}")

# ================= CARTÃO =================
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

    await update.message.reply_text(f"💳 Cartão {nome} criado")

async def gastocartao(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /gastocartao cartao valor descrição")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    cartao = context.args[0]
    valor = valor_num(context.args[1])
    desc = " ".join(context.args[2:]) or "Gasto cartão"

    if cartao not in dados[uid]["cartoes"]:
        await update.message.reply_text("❌ Cartão não encontrado")
        return

    dados[uid]["cartoes"][cartao]["fatura"] += valor
    salvar_dados(dados)

    await update.message.reply_text(f"💳 Gasto R$ {valor:.2f} no {cartao}")

async def cartoes(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    if not dados[uid]["cartoes"]:
        await update.message.reply_text("Nenhum cartão cadastrado")
        return

    msg = "💳 Cartões:\n"
    for c, i in dados[uid]["cartoes"].items():
        msg += f"{c}: {i['fatura']:.2f}/{i['limite']:.2f}\n"

    await update.message.reply_text(msg)

# ================= PARCELADO =================
async def parcelado(update, context):
    if len(context.args) < 4:
        await update.message.reply_text("Uso: /parcelado cartao valor parcelas descrição")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    cartao = context.args[0]
    valor = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:])

    if cartao not in dados[uid]["cartoes"]:
        await update.message.reply_text("❌ Cartão não encontrado")
        return

    dados[uid]["parcelas"].append({
        "cartao": cartao,
        "valor": valor / parcelas,
        "restantes": parcelas,
        "desc": desc
    })

    salvar_dados(dados)
    await update.message.reply_text(f"📦 Parcelado em {parcelas}x no {cartao}")

async def parcelamentos(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    if not dados[uid]["parcelas"]:
        await update.message.reply_text("Nenhum parcelamento ativo")
        return

    msg = "📦 Parcelamentos:\n"
    for p in dados[uid]["parcelas"]:
        msg += f"{p['desc']} - {p['restantes']}x de {p['valor']:.2f}\n"

    await update.message.reply_text(msg)

# ================= EMPRÉSTIMO =================
async def emprestimo(update, context):
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /emprestimo valor parcelas descrição")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    valor = valor_num(context.args[0])
    parcelas = int(context.args[1])
    desc = " ".join(context.args[2:])

    dados[uid]["saldo"] += valor
    dados[uid]["emprestimos"].append({
        "valor": valor / parcelas,
        "restantes": parcelas,
        "desc": desc
    })

    salvar_dados(dados)
    await update.message.reply_text(f"💸 Empréstimo registrado em {parcelas}x")

async def emprestimos(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    if not dados[uid]["emprestimos"]:
        await update.message.reply_text("Nenhum empréstimo ativo")
        return

    msg = "💸 Empréstimos:\n"
    for e in dados[uid]["emprestimos"]:
        msg += f"{e['desc']} - {e['restantes']}x de {e['valor']:.2f}\n"

    await update.message.reply_text(msg)

# ================= CONTAS =================
async def conta(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /conta nome valor")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    dados[uid]["contas"].append({
        "nome": context.args[0],
        "valor": valor_num(context.args[1])
    })

    salvar_dados(dados)
    await update.message.reply_text("📄 Conta adicionada")

async def excluirconta(update, context):
    if not context.args:
        await update.message.reply_text("Uso: /excluirconta nome")
        return

    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    nome = context.args[0]
    dados[uid]["contas"] = [c for c in dados[uid]["contas"] if c["nome"] != nome]
    salvar_dados(dados)

    await update.message.reply_text(f"🗑️ Conta {nome} removida")

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
    await update.message.reply_text("🔄 Mês avançado")

async def resetgeral(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)

    dados[uid] = {
        "saldo": 0,
        "historico": [],
        "cartoes": {},
        "parcelas": [],
        "emprestimos": [],
        "contas": []
    }

    salvar_dados(dados)
    await update.message.reply_text("🔥 RESET GERAL feito")

# ================= RESUMO =================
async def resumo(update, context):
    dados = carregar_dados()
    uid = str(update.effective_user.id)
    init_user(dados, uid)

    d = dados[uid]
    msg = f"📊 Saldo: R$ {d['saldo']:.2f}\n"

    await update.message.reply_text(msg)

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

handlers = [
    ("start", start),
    ("entrada", entrada),
    ("gasto", gasto),
    ("gastocartao", gastocartao),
    ("novocartao", novocartao),
    ("cartoes", cartoes),
    ("parcelado", parcelado),
    ("parcelamentos", parcelamentos),
    ("emprestimo", emprestimo),
    ("emprestimos", emprestimos),
    ("conta", conta),
    ("excluirconta", excluirconta),
    ("resetmes", resetmes),
    ("resetgeral", resetgeral),
    ("resumo", resumo)
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

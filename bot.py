import os
import json
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USUARIOS = {
    5364076144: "Layanne",
    5507658531: "Júlio"
}

CASAL_ID = "casal_financeiro"
DADOS_ARQ = "dados.json"

app = Flask(__name__)

# ================= UTIL =================
def mes_ano():
    return datetime.now().strftime("%m/%Y")

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

def init_mes(dados):
    dados.setdefault(CASAL_ID, {})
    dados[CASAL_ID].setdefault(mes_ano(), {
        "saldo": 0,
        "cartoes": [],
        "parcelados": [],
        "emprestimos": [],
        "contas": [],
        "historico": []
    })

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return

    teclado = [
        ["/entrada", "/gasto"],
        ["/addcartao", "/cartoes"],
        ["/gastocartao", "/parcelado"],
        ["/parcelamentos", "/emprestimos"],
        ["/addconta", "/resumo"],
        ["/resetmes", "/reset_geral"]
    ]

    await update.message.reply_text(
        "💰 Assistente Financeiro do Casal",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# ================= ENTRADA / GASTO =================
async def entrada(update, context):
    if not context.args:
        return await update.message.reply_text("Uso: /entrada VALOR DESCRIÇÃO")

    dados = carregar_dados()
    init_mes(dados)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Entrada"
    autor = USUARIOS[update.effective_user.id]

    dados[CASAL_ID][mes_ano()]["saldo"] += valor
    dados[CASAL_ID][mes_ano()]["historico"].append(
        {"tipo": "entrada", "valor": valor, "desc": desc, "autor": autor}
    )

    salvar_dados(dados)
    await update.message.reply_text(f"✅ Entrada R$ {valor:.2f}")

async def gasto(update, context):
    if not context.args:
        return await update.message.reply_text("Uso: /gasto VALOR DESCRIÇÃO")

    dados = carregar_dados()
    init_mes(dados)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Gasto"
    autor = USUARIOS[update.effective_user.id]

    dados[CASAL_ID][mes_ano()]["saldo"] -= valor
    dados[CASAL_ID][mes_ano()]["historico"].append(
        {"tipo": "gasto", "valor": valor, "desc": desc, "autor": autor}
    )

    salvar_dados(dados)
    await update.message.reply_text(f"❌ Gasto R$ {valor:.2f}")

# ================= CARTÕES =================
async def addcartao(update, context):
    dados = carregar_dados()
    init_mes(dados)

    nome = context.args[0]
    limite = valor_num(context.args[1])

    dados[CASAL_ID][mes_ano()]["cartoes"].append({
        "nome": nome,
        "limite": limite,
        "fatura": 0,
        "dono": USUARIOS[update.effective_user.id]
    })

    salvar_dados(dados)
    await update.message.reply_text("💳 Cartão adicionado.")

async def cartoes(update, context):
    dados = carregar_dados()
    init_mes(dados)

    cartoes = dados[CASAL_ID][mes_ano()]["cartoes"]
    if not cartoes:
        return await update.message.reply_text("Nenhum cartão cadastrado.")

    msg = "💳 CARTÕES:\n"
    for i, c in enumerate(cartoes, 1):
        msg += f"{i}. {c['nome']} | Limite {c['limite']:.2f} | Fatura {c['fatura']:.2f} | {c['dono']}\n"

    await update.message.reply_text(msg)

async def gastocartao(update, context):
    dados = carregar_dados()
    init_mes(dados)

    cartao = context.args[0]
    valor = valor_num(context.args[1])
    desc = " ".join(context.args[2:]) or "Gasto cartão"

    for c in dados[CASAL_ID][mes_ano()]["cartoes"]:
        if c["nome"].lower() == cartao.lower():
            c["fatura"] += valor
            salvar_dados(dados)
            return await update.message.reply_text("💳 Gasto lançado.")

    await update.message.reply_text("Cartão não encontrado.")

# ================= PARCELADO =================
async def parcelado(update, context):
    dados = carregar_dados()
    init_mes(dados)

    cartao = context.args[0]
    valor = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) or "Parcelado"

    dados[CASAL_ID][mes_ano()]["parcelados"].append({
        "cartao": cartao,
        "valor": valor,
        "parcelas": parcelas,
        "desc": desc,
        "autor": USUARIOS[update.effective_user.id]
    })

    salvar_dados(dados)
    await update.message.reply_text("🧾 Parcelamento criado.")

async def parcelamentos(update, context):
    dados = carregar_dados()
    init_mes(dados)

    p = dados[CASAL_ID][mes_ano()]["parcelados"]
    if not p:
        return await update.message.reply_text("Nenhum parcelamento.")

    msg = "🧾 PARCELAMENTOS:\n"
    for i, x in enumerate(p, 1):
        msg += f"{i}. {x['desc']} | {x['parcelas']}x | R$ {x['valor']:.2f} | {x['autor']}\n"

    await update.message.reply_text(msg)

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    dados = carregar_dados()
    init_mes(dados)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Empréstimo"

    dados[CASAL_ID][mes_ano()]["emprestimos"].append({
        "valor": valor,
        "desc": desc,
        "autor": USUARIOS[update.effective_user.id]
    })

    salvar_dados(dados)
    await update.message.reply_text("💸 Empréstimo registrado.")

async def emprestimos(update, context):
    dados = carregar_dados()
    init_mes(dados)

    e = dados[CASAL_ID][mes_ano()]["emprestimos"]
    if not e:
        return await update.message.reply_text("Nenhum empréstimo.")

    msg = "💸 EMPRÉSTIMOS:\n"
    for i, x in enumerate(e, 1):
        msg += f"{i}. {x['desc']} | R$ {x['valor']:.2f} | {x['autor']}\n"

    await update.message.reply_text(msg)

# ================= RESET =================
async def resetmes(update, context):
    dados = carregar_dados()
    init_mes(dados)

    for p in dados[CASAL_ID][mes_ano()]["parcelados"]:
        for c in dados[CASAL_ID][mes_ano()]["cartoes"]:
            if c["nome"] == p["cartao"]:
                c["fatura"] += p["valor"] / p["parcelas"]

    salvar_dados(dados)
    await update.message.reply_text("🔄 Mês avançado.")

async def reset_geral(update, context):
    salvar_dados({})
    await update.message.reply_text("⚠️ Tudo foi zerado.")

# ================= RESUMO =================
async def resumo(update, context):
    dados = carregar_dados()
    init_mes(dados)

    d = dados[CASAL_ID][mes_ano()]
    msg = f"📊 RESUMO {mes_ano()}\nSaldo: R$ {d['saldo']:.2f}\n"

    for c in d["cartoes"]:
        msg += f"💳 {c['nome']}: R$ {c['fatura']:.2f}\n"

    await update.message.reply_text(msg)

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

handlers = {
    "start": start,
    "entrada": entrada,
    "gasto": gasto,
    "addcartao": addcartao,
    "cartoes": cartoes,
    "gastocartao": gastocartao,
    "parcelado": parcelado,
    "parcelamentos": parcelamentos,
    "emprestimo": emprestimo,
    "emprestimos": emprestimos,
    "resetmes": resetmes,
    "reset_geral": reset_geral,
    "resumo": resumo
}

for cmd, func in handlers.items():
    application.add_handler(CommandHandler(cmd, func))

@app.route("/", methods=["POST"])
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

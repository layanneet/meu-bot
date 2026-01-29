import os
import json
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DADOS_ARQ = "dados.json"

CASAL_ID = "financeiro_layanne_julio"

USUARIOS = {
    5364076144: "Layanne",
    5507658531: "Júlio"
}

app_flask = Flask(__name__)

# ================= UTIL =================
def mes_ano():
    return datetime.now().strftime("%Y-%m")

def autor(update):
    return USUARIOS.get(update.effective_user.id, "Desconhecido")

def valor_num(v):
    return float(v.replace(",", "."))

# ================= DADOS =================
def carregar_dados():
    if not os.path.exists(DADOS_ARQ):
        return {}
    with open(DADOS_ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DADOS_ARQ, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def init_mes(dados):
    dados.setdefault(CASAL_ID, {})
    dados[CASAL_ID].setdefault(mes_ano(), {
        "historico": [],
        "cartoes": [],
        "parcelados": [],
        "contas": [],
        "emprestimos": []
    })

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        ["/entrada", "/gasto"],
        ["/addcartao", "/gastocartao"],
        ["/parcelado", "/cancelarparcelado"],
        ["/addconta", "/excluirconta"],
        ["/emprestimo", "/cancelaremprestimo"],
        ["/resumo", "/dividas"],
        ["/resetmes", "/reset_geral"]
    ]
    await update.message.reply_text(
        "💚 Controle Financeiro do Casal",
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

    dados[CASAL_ID][mes_ano()]["historico"].append({
        "tipo": "entrada",
        "valor": valor,
        "desc": desc,
        "autor": autor(update)
    })

    salvar_dados(dados)
    await update.message.reply_text("✅ Entrada registrada")

async def gasto(update, context):
    if not context.args:
        return await update.message.reply_text("Uso: /gasto VALOR DESCRIÇÃO")

    dados = carregar_dados()
    init_mes(dados)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Gasto"

    dados[CASAL_ID][mes_ano()]["historico"].append({
        "tipo": "gasto",
        "valor": valor,
        "desc": desc,
        "autor": autor(update)
    })

    salvar_dados(dados)
    await update.message.reply_text("❌ Gasto registrado")

# ================= CARTÕES =================
async def addcartao(update, context):
    if len(context.args) < 2:
        return await update.message.reply_text("Uso: /addcartao NOME LIMITE")

    dados = carregar_dados()
    init_mes(dados)

    dados[CASAL_ID][mes_ano()]["cartoes"].append({
        "nome": context.args[0],
        "limite": valor_num(context.args[1]),
        "dono": autor(update),
        "fatura": 0
    })

    salvar_dados(dados)
    await update.message.reply_text("💳 Cartão adicionado")

async def gastocartao(update, context):
    if len(context.args) < 2:
        return await update.message.reply_text("Uso: /gastocartao CARTAO VALOR DESC")

    dados = carregar_dados()
    init_mes(dados)

    cartao = context.args[0]
    valor = valor_num(context.args[1])
    desc = " ".join(context.args[2:]) or "Gasto cartão"

    for c in dados[CASAL_ID][mes_ano()]["cartoes"]:
        if c["nome"] == cartao:
            c["fatura"] += valor
            dados[CASAL_ID][mes_ano()]["historico"].append({
                "tipo": "gasto_cartao",
                "valor": valor,
                "desc": desc,
                "autor": autor(update)
            })
            salvar_dados(dados)
            return await update.message.reply_text("💳 Gasto no cartão registrado")

    await update.message.reply_text("Cartão não encontrado")

async def excluircartao(update, context):
    idx = int(context.args[0]) - 1
    dados = carregar_dados()
    init_mes(dados)
    dados[CASAL_ID][mes_ano()]["cartoes"].pop(idx)
    salvar_dados(dados)
    await update.message.reply_text("🗑️ Cartão removido")

# ================= PARCELADO =================
async def parcelado(update, context):
    cartao = context.args[0]
    valor = valor_num(context.args[1])
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) or "Parcelado"

    dados = carregar_dados()
    init_mes(dados)

    dados[CASAL_ID][mes_ano()]["parcelados"].append({
        "cartao": cartao,
        "valor": valor,
        "parcelas": parcelas,
        "desc": desc,
        "autor": autor(update)
    })

    salvar_dados(dados)
    await update.message.reply_text("🧾 Parcelado criado")

async def cancelarparcelado(update, context):
    idx = int(context.args[0]) - 1
    dados = carregar_dados()
    init_mes(dados)
    dados[CASAL_ID][mes_ano()]["parcelados"].pop(idx)
    salvar_dados(dados)
    await update.message.reply_text("❌ Parcelado cancelado")

# ================= CONTAS =================
async def addconta(update, context):
    nome = context.args[0]
    valor = valor_num(context.args[1])

    dados = carregar_dados()
    init_mes(dados)

    dados[CASAL_ID][mes_ano()]["contas"].append({
        "nome": nome,
        "valor": valor,
        "autor": autor(update)
    })

    salvar_dados(dados)
    await update.message.reply_text("📌 Conta adicionada")

async def excluirconta(update, context):
    idx = int(context.args[0]) - 1
    dados = carregar_dados()
    init_mes(dados)
    dados[CASAL_ID][mes_ano()]["contas"].pop(idx)
    salvar_dados(dados)
    await update.message.reply_text("🗑️ Conta removida")

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:])

    dados = carregar_dados()
    init_mes(dados)

    dados[CASAL_ID][mes_ano()]["emprestimos"].append({
        "valor": valor,
        "desc": desc,
        "autor": autor(update)
    })

    salvar_dados(dados)
    await update.message.reply_text("💸 Empréstimo registrado")

async def cancelaremprestimo(update, context):
    idx = int(context.args[0]) - 1
    dados = carregar_dados()
    init_mes(dados)
    dados[CASAL_ID][mes_ano()]["emprestimos"].pop(idx)
    salvar_dados(dados)
    await update.message.reply_text("❌ Empréstimo removido")

# ================= RESET =================
async def resetmes(update, context):
    await update.message.reply_text("🔄 Novo mês iniciará automaticamente")

async def reset_geral(update, context):
    salvar_dados({})
    await update.message.reply_text("⚠️ Todos os dados apagados")

# ================= RESUMOS =================
async def resumo(update, context):
    dados = carregar_dados()
    init_mes(dados)

    total = sum(i["valor"] for i in dados[CASAL_ID][mes_ano()]["historico"] if "gasto" in i["tipo"])

    await update.message.reply_text(f"📊 Resumo {mes_ano()}\nTotal gastos: R$ {total:.2f}")

async def dividas(update, context):
    dados = carregar_dados()
    init_mes(dados)

    pessoas = {}
    for h in dados[CASAL_ID][mes_ano()]["historico"]:
        if "gasto" in h["tipo"]:
            pessoas[h["autor"]] = pessoas.get(h["autor"], 0) + h["valor"]

    msg = "💸 Dívidas:\n"
    for p, v in pessoas.items():
        msg += f"{p}: R$ {v:.2f}\n"

    msg += f"\nTotal: R$ {sum(pessoas.values()):.2f}"
    await update.message.reply_text(msg)

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

for c, f in {
    "start": start,
    "entrada": entrada,
    "gasto": gasto,
    "addcartao": addcartao,
    "gastocartao": gastocartao,
    "excluircartao": excluircartao,
    "parcelado": parcelado,
    "cancelarparcelado": cancelarparcelado,
    "addconta": addconta,
    "excluirconta": excluirconta,
    "emprestimo": emprestimo,
    "cancelaremprestimo": cancelaremprestimo,
    "resetmes": resetmes,
    "reset_geral": reset_geral,
    "resumo": resumo,
    "dividas": dividas
}.items():
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

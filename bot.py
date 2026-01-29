import os
import json
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DADOS_ARQ = "dados.json"

CASAL_ID = "layanne_julio"

USUARIOS = {
    5364076144: "Layanne",
    5507658531: "Júlio"
}

app_flask = Flask(__name__)

# ================= UTIL =================
def mes_atual():
    return datetime.now().strftime("%Y-%m")

def valor_num(v):
    return float(v.replace(",", "."))

def autor(update):
    return USUARIOS.get(update.effective_user.id, "Desconhecido")

# ================= DADOS =================
def carregar_dados():
    if not os.path.exists(DADOS_ARQ):
        return {}
    with open(DADOS_ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DADOS_ARQ, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def init_casal(dados):
    dados.setdefault(CASAL_ID, {
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
        ["/dividas", "/resumomensal"],
        ["/gastoslayanne", "/gastosjulio"]
    ]
    await update.message.reply_text(
        "💚 Assistente Financeiro do Casal",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# ================= ENTRADA / GASTO =================
async def entrada(update, context):
    if not context.args:
        await update.message.reply_text("Uso: /entrada 100 descrição")
        return

    dados = carregar_dados()
    init_casal(dados)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Entrada"

    dados[CASAL_ID]["saldo"] += valor
    dados[CASAL_ID]["historico"].append({
        "tipo": "entrada",
        "valor": valor,
        "desc": desc,
        "autor": autor(update),
        "mes": mes_atual()
    })

    salvar_dados(dados)
    await update.message.reply_text("✅ Entrada registrada")

async def gasto(update, context):
    if not context.args:
        await update.message.reply_text("Uso: /gasto 50 descrição")
        return

    dados = carregar_dados()
    init_casal(dados)

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) or "Gasto"

    dados[CASAL_ID]["saldo"] -= valor
    dados[CASAL_ID]["historico"].append({
        "tipo": "gasto",
        "valor": valor,
        "desc": desc,
        "autor": autor(update),
        "mes": mes_atual()
    })

    salvar_dados(dados)
    await update.message.reply_text("❌ Gasto registrado")

# ================= CARTÃO =================
async def novocartao(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /novocartao nome limite")
        return

    dados = carregar_dados()
    init_casal(dados)

    nome = context.args[0]
    limite = valor_num(context.args[1])

    dados[CASAL_ID]["cartoes"][nome] = {
        "limite": limite,
        "fatura": 0,
        "dono": autor(update)
    }

    salvar_dados(dados)
    await update.message.reply_text("💳 Cartão cadastrado")

async def gastocartao(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /gastocartao cartao valor")
        return

    dados = carregar_dados()
    init_casal(dados)

    cartao = context.args[0]
    valor = valor_num(context.args[1])

    if cartao not in dados[CASAL_ID]["cartoes"]:
        await update.message.reply_text("Cartão não encontrado")
        return

    dados[CASAL_ID]["cartoes"][cartao]["fatura"] += valor
    dados[CASAL_ID]["historico"].append({
        "tipo": "gasto_cartao",
        "valor": valor,
        "desc": cartao,
        "autor": autor(update),
        "mes": mes_atual()
    })

    salvar_dados(dados)
    await update.message.reply_text("💳 Gasto no cartão registrado")

# ================= DIVIDAS =================
async def dividas(update, context):
    dados = carregar_dados()
    init_casal(dados)

    div = {}

    for h in dados[CASAL_ID]["historico"]:
        if h["tipo"].startswith("gasto"):
            div[h["autor"]] = div.get(h["autor"], 0) + h["valor"]

    total = sum(div.values())

    msg = "📉 DÍVIDAS:\n"
    for p, v in div.items():
        msg += f"{p}: R$ {v:.2f}\n"

    msg += f"\n💰 Total do casal: R$ {total:.2f}"
    await update.message.reply_text(msg)

# ================= GASTOS INDIVIDUAIS =================
async def gastos_pessoa(update, nome):
    dados = carregar_dados()
    init_casal(dados)

    msg = f"📊 Gastos de {nome}:\n"
    total = 0

    for h in dados[CASAL_ID]["historico"]:
        if h["autor"] == nome and h["tipo"].startswith("gasto"):
            msg += f"- {h['desc']} | R$ {h['valor']:.2f}\n"
            total += h["valor"]

    msg += f"\nTotal: R$ {total:.2f}"
    await update.message.reply_text(msg)

async def gastoslayanne(update, context):
    await gastos_pessoa(update, "Layanne")

async def gastosjulio(update, context):
    await gastos_pessoa(update, "Júlio")

# ================= RESUMO MENSAL =================
async def resumomensal(update, context):
    dados = carregar_dados()
    init_casal(dados)

    mes = mes_atual()
    gastos = {}

    for h in dados[CASAL_ID]["historico"]:
        if h["mes"] == mes and h["tipo"].startswith("gasto"):
            gastos[h["autor"]] = gastos.get(h["autor"], 0) + h["valor"]

    msg = f"📆 RESUMO {mes}\n"
    for p, v in gastos.items():
        msg += f"{p}: R$ {v:.2f}\n"

    msg += f"\nTotal do mês: R$ {sum(gastos.values()):.2f}"
    await update.message.reply_text(msg)

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

handlers = {
    "start": start,
    "entrada": entrada,
    "gasto": gasto,
    "gastocartao": gastocartao,
    "novocartao": novocartao,
    "dividas": dividas,
    "gastoslayanne": gastoslayanne,
    "gastosjulio": gastosjulio,
    "resumomensal": resumomensal
}

for cmd, fn in handlers.items():
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

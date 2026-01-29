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

def base_usuario():
    return {
        "saldo": 0,
        "historico": [],
        "cartoes": {},
        "parcelas": [],
        "emprestimos": [],
        "contas": []
    }

# ================= BOT =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_ok(update.effective_user.id):
        return

    teclado = [
        ["/entrada", "/gasto", "/gastocartao"],
        ["/novocartao", "/cartoes"],
        ["/parcelado", "/parcelamentos"],
        ["/emprestimo", "/emprestimos"],
        ["/conta", "/resetmes"],
        ["/resumo", "/resumomensal"],
        ["/dividas"],
        ["/reset_geral"]
    ]

    await update.message.reply_text(
        "💰 Assistente Financeiro",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# ================= ENTRADA / GASTO =================
async def entrada(update, context):
    if not context.args:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) if len(context.args) > 1 else "Entrada"

    dados[uid]["saldo"] += valor
    dados[uid]["historico"].append({
        "tipo": "entrada",
        "valor": valor,
        "desc": desc,
        "mes": datetime.now().strftime("%Y-%m")
    })

    salvar_dados(dados)
    await update.message.reply_text(f"✅ Entrada registrada: R$ {valor:.2f}")

async def gasto(update, context):
    if not context.args:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

    valor = valor_num(context.args[0])
    desc = " ".join(context.args[1:]) if len(context.args) > 1 else "Gasto"

    dados[uid]["saldo"] -= valor
    dados[uid]["historico"].append({
        "tipo": "gasto",
        "valor": valor,
        "desc": desc,
        "mes": datetime.now().strftime("%Y-%m")
    })

    salvar_dados(dados)
    await update.message.reply_text(f"❌ Gasto registrado: R$ {valor:.2f}")

# ================= CARTÕES =================
async def novocartao(update, context):
    if len(context.args) < 2:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

    nome = context.args[0]
    limite = valor_num(context.args[1])

    dados[uid]["cartoes"][nome] = {"limite": limite, "fatura": 0}

    salvar_dados(dados)
    await update.message.reply_text(f"💳 Cartão {nome} criado.")

async def cartoes(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

    msg = "💳 Cartões:\n"
    for c, info in dados[uid]["cartoes"].items():
        msg += f"{c}: Fatura R$ {info['fatura']:.2f} / Limite R$ {info['limite']:.2f}\n"

    await update.message.reply_text(msg or "Nenhum cartão cadastrado.")

async def gastocartao(update, context):
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /gastocartao cartao valor descrição")
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

    cartao = context.args[0]
    valor = valor_num(context.args[1])
    desc = " ".join(context.args[2:])

    if cartao not in dados[uid]["cartoes"]:
        await update.message.reply_text("❌ Cartão não encontrado.")
        return

    dados[uid]["cartoes"][cartao]["fatura"] += valor
    dados[uid]["historico"].append({
        "tipo": "gasto_cartao",
        "valor": valor,
        "desc": desc,
        "mes": datetime.now().strftime("%Y-%m")
    })

    salvar_dados(dados)
    await update.message.reply_text("💳 Gasto no cartão registrado.")

async def excluircartao(update, context):
    if not context.args:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()

    nome = context.args[0]
    if nome in dados[uid]["cartoes"]:
        del dados[uid]["cartoes"][nome]
        salvar_dados(dados)
        await update.message.reply_text("🗑️ Cartão excluído.")
    else:
        await update.message.reply_text("❌ Cartão não encontrado.")

# ================= PARCELADO =================
async def parcelado(update, context):
    if len(context.args) < 3:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

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

    await update.message.reply_text(msg or "Nenhum parcelamento.")

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    if len(context.args) < 3:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

    nome = context.args[0]
    total = valor_num(context.args[1])
    parcelas = int(context.args[2])

    dados[uid]["emprestimos"].append({
        "nome": nome,
        "valor": total / parcelas,
        "restantes": parcelas
    })

    salvar_dados(dados)
    await update.message.reply_text("📉 Empréstimo registrado.")

async def emprestimos(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

    msg = "📉 Empréstimos:\n"
    for e in dados[uid]["emprestimos"]:
        msg += f"{e['nome']} - {e['restantes']} meses - R$ {e['valor']:.2f}\n"

    await update.message.reply_text(msg or "Nenhum empréstimo.")

# ================= CONTAS =================
async def conta(update, context):
    if len(context.args) < 2:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados.setdefault(uid, base_usuario())

    nome = context.args[0]
    valor = valor_num(context.args[1])

    dados[uid]["contas"].append({"nome": nome, "valor": valor})
    salvar_dados(dados)

    await update.message.reply_text("📌 Conta fixa registrada.")

async def excluirconta(update, context):
    if not context.args:
        return

    uid = str(update.effective_user.id)
    dados = carregar_dados()

    nome = context.args[0]
    dados[uid]["contas"] = [c for c in dados[uid]["contas"] if c["nome"] != nome]

    salvar_dados(dados)
    await update.message.reply_text("🗑️ Conta excluída.")

# ================= RESET =================
async def resetmes(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()

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

async def reset_geral(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    dados[uid] = base_usuario()
    salvar_dados(dados)
    await update.message.reply_text("🧨 Reset geral concluído.")

# ================= RESUMOS =================
async def resumo(update, context):
    uid = str(update.effective_user.id)
    dados = carregar_dados()
    d = dados[uid]

    msg = f"📊 RESUMO\nSaldo: R$ {d['saldo']:.2f}\n\n💳 Cartões:\n"
    for c, info in d["cartoes"].items():
        msg += f"{c}: R$ {info['fatura']:.2f}\n"

    await update.message.reply_text(msg)

async def resumomensal(update, context):
    dados = carregar_dados()
    mes = datetime.now().strftime("%Y-%m")

    msg = f"📅 RESUMO {mes}\n"
    total = 0

    for uid, d in dados.items():
        soma = sum(h["valor"] for h in d["historico"] if h.get("mes") == mes and "gasto" in h["tipo"])
        msg += f"{uid}: R$ {soma:.2f}\n"
        total += soma

    msg += f"\n💰 Total do mês: R$ {total:.2f}"
    await update.message.reply_text(msg)

async def dividas(update, context):
    dados = carregar_dados()
    total = 0
    msg = "📉 DÍVIDAS\n"

    for uid, d in dados.items():
        soma = sum(h["valor"] for h in d["historico"] if "gasto" in h["tipo"])
        msg += f"{uid}: R$ {soma:.2f}\n"
        total += soma

    msg += f"\n💰 Total geral: R$ {total:.2f}"
    await update.message.reply_text(msg)

# ================= WEBHOOK =================
application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("entrada", entrada))
application.add_handler(CommandHandler("gasto", gasto))
application.add_handler(CommandHandler("gastocartao", gastocartao))
application.add_handler(CommandHandler("novocartao", novocartao))
application.add_handler(CommandHandler("cartoes", cartoes))
application.add_handler(CommandHandler("parcelado", parcelado))
application.add_handler(CommandHandler("parcelamentos", parcelamentos))
application.add_handler(CommandHandler("emprestimo", emprestimo))
application.add_handler(CommandHandler("emprestimos", emprestimos))
application.add_handler(CommandHandler("conta", conta))
application.add_handler(CommandHandler("excluirconta", excluirconta))
application.add_handler(CommandHandler("excluircartao", excluircartao))
application.add_handler(CommandHandler("resetmes", resetmes))
application.add_handler(CommandHandler("reset_geral", reset_geral))
application.add_handler(CommandHandler("resumo", resumo))
application.add_handler(CommandHandler("resumomensal", resumomensal))
application.add_handler(CommandHandler("dividas", dividas))

@app_flask.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
  )

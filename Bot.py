import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"

USUARIOS = [5507658531, 5364076144]
ARQUIVO = "dados.json"

# =========================
# DADOS
# =========================

def carregar():
    if not os.path.exists(ARQUIVO):
        dados = {
            "saldo": 0.0,
            "historico": [],
            "cartoes": {},
            "parcelamentos": [],
            "emprestimos": [],
            "contas": []
        }
        salvar(dados)
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def autorizado(user_id):
    return user_id in USUARIOS

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    teclado = [
        ["/resumo", "/saldo"],
        ["/cartoes", "/emprestimos"],
        ["/parcelamentos", "/resetmes"]
    ]
    await update.message.reply_text(
        "💰 Banco Virtual iniciado",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# =========================
# SALDO
# =========================

async def entrada(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    valor = float(context.args[0].replace(",", "."))
    desc = " ".join(context.args[1:]) if len(context.args) > 1 else "Entrada"
    dados["saldo"] += valor
    dados["historico"].append({"tipo": "entrada", "valor": valor, "desc": desc})
    salvar(dados)
    await update.message.reply_text(f"✅ Entrada R$ {valor:.2f}")

async def gasto(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    valor = float(context.args[0].replace(",", "."))
    desc = " ".join(context.args[1:]) if len(context.args) > 1 else "Gasto"
    dados["saldo"] -= valor
    dados["historico"].append({"tipo": "gasto", "valor": valor, "desc": desc})
    salvar(dados)
    await update.message.reply_text(f"💸 Gasto R$ {valor:.2f}")

async def saldo(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    await update.message.reply_text(f"💰 Saldo atual: R$ {dados['saldo']:.2f}")

# =========================
# CARTÕES
# =========================

async def novocartao(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    nome = context.args[0]
    limite = float(context.args[1].replace(",", "."))
    dados["cartoes"][nome] = {"limite": limite, "gastos": []}
    salvar(dados)
    await update.message.reply_text(f"💳 Cartão {nome} criado")

async def gastocartao(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    nome = context.args[0]
    valor = float(context.args[1].replace(",", "."))
    desc = " ".join(context.args[2:]) if len(context.args) > 2 else "Gasto cartão"

    if nome not in dados["cartoes"]:
        await update.message.reply_text("❌ Cartão não encontrado")
        return

    dados["cartoes"][nome]["gastos"].append({
        "valor": valor,
        "desc": desc
    })
    salvar(dados)
    await update.message.reply_text(f"💳 Gasto R$ {valor:.2f} no cartão {nome}")

async def cartoes(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    msg = "💳 Cartões:\n"
    for c, info in dados["cartoes"].items():
        fatura = sum(g["valor"] for g in info["gastos"])
        msg += f"{c}: R$ {fatura:.2f} / Limite R$ {info['limite']:.2f}\n"
    await update.message.reply_text(msg)

# =========================
# PARCELAMENTOS
# =========================

async def parcelado(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    nome = context.args[0]
    total = float(context.args[1].replace(",", "."))
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) if len(context.args) > 3 else "Parcelado"

    dados["parcelamentos"].append({
        "nome": nome,
        "parcela": total / parcelas,
        "restantes": parcelas,
        "desc": desc
    })
    salvar(dados)
    await update.message.reply_text("🧾 Parcelamento criado")

async def parcelamentos(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    msg = "🧾 Parcelamentos:\n"
    for p in dados["parcelamentos"]:
        msg += f"{p['nome']} - {p['restantes']}x R$ {p['parcela']:.2f}\n"
    await update.message.reply_text(msg)

# =========================
# EMPRÉSTIMOS
# =========================

async def emprestimo(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    nome = context.args[0]
    total = float(context.args[1].replace(",", "."))
    parcelas = int(context.args[2])
    desc = " ".join(context.args[3:]) if len(context.args) > 3 else "Empréstimo"

    dados["emprestimos"].append({
        "nome": nome,
        "parcela": total / parcelas,
        "restantes": parcelas,
        "desc": desc
    })
    salvar(dados)
    await update.message.reply_text("📉 Empréstimo registrado")

async def emprestimos(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    msg = "📉 Empréstimos:\n"
    for e in dados["emprestimos"]:
        msg += f"{e['nome']} - {e['restantes']}x R$ {e['parcela']:.2f}\n"
    await update.message.reply_text(msg)

# =========================
# RESET MENSAL
# =========================

async def resetmes(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()

    for p in dados["parcelamentos"][:]:
        dados["saldo"] -= p["parcela"]
        p["restantes"] -= 1
        if p["restantes"] <= 0:
            dados["parcelamentos"].remove(p)

    for e in dados["emprestimos"][:]:
        dados["saldo"] -= e["parcela"]
        e["restantes"] -= 1
        if e["restantes"] <= 0:
            dados["emprestimos"].remove(e)

    for c in dados["cartoes"].values():
        c["gastos"] = []

    salvar(dados)
    await update.message.reply_text("🔄 Mês resetado com sucesso")

# =========================
# RESUMO
# =========================

async def resumo(update, context):
    if not autorizado(update.effective_user.id): return
    dados = carregar()
    msg = f"📊 RESUMO\nSaldo: R$ {dados['saldo']:.2f}\n"
    msg += f"Cartões: {len(dados['cartoes'])}\n"
    msg += f"Parcelamentos: {len(dados['parcelamentos'])}\n"
    msg += f"Empréstimos: {len(dados['emprestimos'])}\n"
    await update.message.reply_text(msg)

# =========================
# APP
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("novocartao", novocartao))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("cartoes", cartoes))
app.add_handler(CommandHandler("parcelado", parcelado))
app.add_handler(CommandHandler("parcelamentos", parcelamentos))
app.add_handler(CommandHandler("emprestimo", emprestimo))
app.add_handler(CommandHandler("emprestimos", emprestimos))
app.add_handler(CommandHandler("resetmes", resetmes))
app.add_handler(CommandHandler("resumo", resumo))

app.run_polling()

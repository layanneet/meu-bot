import os
import json
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

TOKEN = os.getenv("TOKEN")

USUARIOS = [5364076144, 5507658531]
DATA_FILE = "dados.json"


def init_dados():
    if not os.path.exists(DATA_FILE):
        dados = {
            "saldo": 0.0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "contas": {},
            "parcelamentos": []
        }
        salvar_dados(dados)


def carregar_dados():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def salvar_dados(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def autorizado(update: Update):
    return update.effective_user.id in USUARIOS


def parse_valor(valor_str: str):
    return float(valor_str.replace(",", "."))


# ================= MENU =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    teclado = [
        [InlineKeyboardButton("➕ Entrada", callback_data="entrada")],
        [InlineKeyboardButton("💸 Gasto", callback_data="gasto")],
        [InlineKeyboardButton("💳 Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("🧾 Contas", callback_data="contas")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Reset mês", callback_data="reset")]
    ]
    await update.message.reply_text(
        "🏦 Organizador Financeiro",
        reply_markup=InlineKeyboardMarkup(teclado)
    )


async def botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    textos = {
        "entrada": "/entrada <valor> <descrição>",
        "gasto": "/gasto <valor> <descrição>",
        "cartoes": "/cartoes",
        "contas": "/conta <nome> <valor>",
        "resumo": "/resumo",
        "reset": "/resetmes"
    }
    await q.edit_message_text(textos.get(q.data, ""))


# ================= ENTRADAS =================

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if not context.args:
        return
    valor = parse_valor(context.args[0])
    descricao = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] += valor
    dados["entradas"].append({
        "valor": valor,
        "descricao": descricao,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"Entrada registrada: R$ {valor:.2f}")


# ================= GASTOS =================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if not context.args:
        return
    valor = parse_valor(context.args[0])
    descricao = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] -= valor
    dados["gastos"].append({
        "valor": valor,
        "descricao": descricao,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"Gasto registrado: R$ {valor:.2f}")


# ================= CARTÕES =================

async def novocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = " ".join(context.args[:-1])
    limite = parse_valor(context.args[-1])
    dados = carregar_dados()
    dados["cartoes"][nome] = {
        "limite": limite,
        "gastos": []
    }
    salvar_dados(dados)
    await update.message.reply_text(f"Cartão {nome} criado com limite R$ {limite:.2f}")


async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = " ".join(context.args[:-2])
    valor = parse_valor(context.args[-2])
    descricao = context.args[-1]
    dados = carregar_dados()
    if nome not in dados["cartoes"]:
        await update.message.reply_text("Cartão não encontrado.")
        return
    usado = sum(g["valor"] for g in dados["cartoes"][nome]["gastos"])
    limite = dados["cartoes"][nome]["limite"]
    if usado + valor > limite:
        await update.message.reply_text("Limite insuficiente.")
        return
    dados["cartoes"][nome]["gastos"].append({
        "valor": valor,
        "descricao": descricao,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"Gasto no {nome}: R$ {valor:.2f}")


async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    msg = []
    for nome, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        disp = c["limite"] - usado
        msg.append(
            f"💳 {nome}\nLimite: {c['limite']:.2f}\nUsado: {usado:.2f}\nDisponível: {disp:.2f}\n"
        )
    await update.message.reply_text("\n".join(msg) if msg else "Nenhum cartão.")


# ================= CONTAS =================

async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = " ".join(context.args[:-1])
    valor = parse_valor(context.args[-1])
    dados = carregar_dados()
    dados["contas"][nome] = valor
    salvar_dados(dados)
    await update.message.reply_text(f"Conta {nome} registrada: R$ {valor:.2f}")


# ================= PARCELAMENTOS =================

async def parcelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = context.args[0]
    total = parse_valor(context.args[1])
    parcelas = int(context.args[2])
    dados = carregar_dados()
    dados["parcelamentos"].append({
        "nome": nome,
        "total": total,
        "parcelas": parcelas,
        "paga": 0
    })
    salvar_dados(dados)
    await update.message.reply_text("Parcelamento registrado.")


# ================= RESUMO =================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    total_cartao = sum(
        sum(g["valor"] for g in c["gastos"])
        for c in dados["cartoes"].values()
    )
    total_contas = sum(dados["contas"].values())
    msg = (
        f"💰 Saldo: R$ {dados['saldo']:.2f}\n"
        f"💸 Gastos: R$ {sum(g['valor'] for g in dados['gastos']):.2f}\n"
        f"💳 Cartões: R$ {total_cartao:.2f}\n"
        f"🧾 Contas: R$ {total_contas:.2f}"
    )
    await update.message.reply_text(msg)


# ================= RESET =================

async def resetmes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    dados = carregar_dados()
    dados["gastos"] = []
    for c in dados["cartoes"].values():
        c["gastos"] = []
    salvar_dados(dados)
    await update.message.reply_text("Mês resetado.")


# ================= APP =================

init_dados()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(botoes))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("novocartao", novocartao))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("cartoes", cartoes))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CommandHandler("parcelar", parcelar))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("resetmes", resetmes))

if __name__ == "__main__":
    app.run_polling()

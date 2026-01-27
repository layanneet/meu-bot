import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"

USUARIOS = [
    5507658531,
    5364076144
]

ARQUIVO = "dados.json"


def carregar_dados():
    if not os.path.exists(ARQUIVO):
        dados = {
            "saldo": 0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "contas": {},
            "parcelas_cartao": [],
            "emprestimos": []
        }
        salvar_dados(dados)
        return dados
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_dados(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def autorizado(update: Update):
    return update.effective_user.id in USUARIOS


def valor_float(txt):
    return float(txt.replace(",", "."))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    teclado = [
        [InlineKeyboardButton("➕ Entrada", callback_data="entrada")],
        [InlineKeyboardButton("💸 Gasto", callback_data="gasto")],
        [InlineKeyboardButton("💳 Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("🧾 Contas", callback_data="contas")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Reset Mês", callback_data="reset")]
    ]

    await update.message.reply_text(
        "Assistente Financeiro",
        reply_markup=InlineKeyboardMarkup(teclado)
    )


async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    valor = valor_float(context.args[0])
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


async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    valor = valor_float(context.args[0])
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


async def novo_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return

    nome = " ".join(context.args[:-1])
    limite = valor_float(context.args[-1])

    dados = carregar_dados()
    dados["cartoes"][nome] = {
        "limite": limite,
        "gastos": []
  }

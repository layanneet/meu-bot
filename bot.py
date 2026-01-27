import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7ykI"

USUARIOS_PERMITIDOS = [
    5507658531,
    5364076144
]

ARQUIVO = "dados.json"

def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return {
            "saldo": 0,
            "entradas": [],
            "gastos": [],
            "cartoes": {},
            "contas_fixas": {},
            "parcelas_cartao": [],
            "emprestimos": []
        }
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def autorizado(update: Update):
    return update.effective_user.id in USUARIOS_PERMITIDOS

def parse_valor(txt):
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
    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] += valor
    dados["entradas"].append({
        "valor": valor,
        "descricao": desc,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"Entrada registrada: {valor:.2f}")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    valor = parse_valor(context.args[0])
    desc = " ".join(context.args[1:])
    dados = carregar_dados()
    dados["saldo"] -= valor
    dados["gastos"].append({
        "valor": valor,
        "descricao": desc,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text(f"Gasto registrado: {valor:.2f}")

async def novo_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text("Cartão criado")

async def gasto_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = context.args[0]
    valor = parse_valor(context.args[1])
    desc = " ".join(context.args[2:])
    dados = carregar_dados()
    cartao = dados["cartoes"].get(nome)
    if not cartao:
        await update.message.reply_text("Cartão não encontrado")
        return
    usado = sum(g["valor"] for g in cartao["gastos"])
    if usado + valor > cartao["limite"]:
        await update.message.reply_text("Limite excedido")
        return
    cartao["gastos"].append({
        "valor": valor,
        "descricao": desc,
        "data": str(datetime.now())
    })
    salvar_dados(dados)
    await update.message.reply_text("Gasto no cartão registrado")

async def cartoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    texto = ""
    for nome, c in dados["cartoes"].items():
        usado = sum(g["valor"] for g in c["gastos"])
        disp = c["limite"] - usado
        texto += f"{nome}\nLimite: {c['limite']}\nUsado: {usado}\nDisponível: {disp}\n\n"
    await update.message.reply_text(texto or "Nenhum cartão cadastrado")

async def parcela_cartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    nome = context.args[0]
    valor = parse_valor(context.args[1])
    meses = int(context.args[2])
    desc = "

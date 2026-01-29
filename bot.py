from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os
from datetime import datetime

ARQ = "dados.json"

# ===================== UTILIDADES =====================

def mes_atual():
    return datetime.now().strftime("%Y-%m")

def carregar():
    if not os.path.exists(ARQ):
        return {}
    with open(ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar(dados):
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def grupo(dados):
    gid = "grupo"
    if gid not in dados:
        dados[gid] = {
            "gastos": {},
            "cartoes": {},
            "parcelados": [],
            "emprestimos": [],
            "contas": []
        }
    return dados[gid]

# ===================== GASTOS =====================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    dados = carregar()
    g = grupo(dados)
    mes = mes_atual()

    g["gastos"].setdefault(mes, []).append({
        "user": update.effective_user.first_name,
        "valor": valor
    })

    salvar(dados)
    await update.message.reply_text(f"💸 Gasto registrado: R$ {valor:.2f}")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = context.args[0]
    valor = float(context.args[1])
    dados = carregar()
    g = grupo(dados)

    g["cartoes"].setdefault(nome, []).append({
        "mes": mes_atual(),
        "valor": valor,
        "user": update.effective_user.first_name
    })

    salvar(dados)
    await update.message.reply_text(f"💳 Gasto no cartão {nome}: R$ {valor:.2f}")

# ===================== PARCELADOS =====================

async def parcelado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = context.args[0]
    valor = float(context.args[1])
    parcelas = int(context.args[2])

    dados = carregar()
    g = grupo(dados)

    g["parcelados"].append({
        "cartao": nome,
        "valor": valor,
        "parcelas": parcelas,
        "restantes": parcelas,
        "user": update.effective_user.first_name
    })

    salvar(dados)
    await update.message.reply_text("📦 Parcelamento registrado")

async def cancelarparcelado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = int(context.args[0]) - 1
    dados = carregar()
    g = grupo(dados)

    if 0 <= idx < len(g["parcelados"]):
        g["parcelados"].pop(idx)
        salvar(dados)
        await update.message.reply_text("🗑️ Parcelamento excluído")
    else:
        await update.message.reply_text("❌ Número inválido")

# ===================== EMPRÉSTIMOS =====================

async def emprestimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    pessoa = update.effective_user.first_name

    dados = carregar()
    g = grupo(dados)

    g["emprestimos"].append({
        "user": pessoa,
        "valor": valor
    })

    salvar(dados)
    await update.message.reply_text("💰 Empréstimo registrado")

async def cancelaremprestimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = int(context.args[0]) - 1
    dados = carregar()
    g = grupo(dados)

    if 0 <= idx < len(g["emprestimos"]):
        g["emprestimos"].pop(idx)
        salvar(dados)
        await update.message.reply_text("🗑️ Empréstimo removido")
    else:
        await update.message.reply_text("❌ Número inválido")

# ===================== CONTAS FIXAS =====================

async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = context.args[0]
    valor = float(context.args[1])

    dados = carregar()
    g = grupo(dados)

    g["contas"].append({
        "nome": nome,
        "valor": valor
    })

    salvar(dados)
    await update.message.reply_text("📄 Conta fixa adicionada")

async def excluirconta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = int(context.args[0]) - 1
    dados = carregar()
    g = grupo(dados)

    if 0 <= idx < len(g["contas"]):
        g["contas"].pop(idx)
        salvar(dados)
        await update.message.reply_text("🗑️ Conta removida")
    else:
        await update.message.reply_text("❌ Número inválido")

# ===================== RESET =====================

async def reset_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    g = grupo(dados)
    mes = mes_atual()

    g["gastos"][mes] = []
    salvar(dados)
    await update.message.reply_text("🔄 Mês resetado")

async def reset_geral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salvar({})
    await update.message.reply_text("⚠️ Reset geral concluído")

# ===================== RESUMO =====================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = carregar()
    g = grupo(dados)
    mes = mes_atual()
    gastos = g["gastos"].get(mes, [])

    por_pessoa = {}
    total = 0

    for gto in gastos:
        user = gto["user"]
        valor = gto["valor"]
        por_pessoa[user] = por_pessoa.get(user, 0) + valor
        total += valor

    texto = f"📊 Resumo {mes}\n\n"

    for pessoa, valor in por_pessoa.items():
        texto += f"👤 {pessoa}: R$ {valor:.2f}\n"

    texto += f"\n💰 Total do mês: R$ {total:.2f}"

    await update.message.reply_text(texto)

# ===================== MAIN =====================

app = ApplicationBuilder().token("8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk").build()

app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("parcelado", parcelado))
app.add_handler(CommandHandler("cancelarparcelado", cancelarparcelado))
app.add_handler(CommandHandler("emprestimo", emprestimo))
app.add_handler(CommandHandler("cancelaremprestimo", cancelaremprestimo))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CommandHandler("excluirconta", excluirconta))
app.add_handler(CommandHandler("reset_mes", reset_mes))
app.add_handler(CommandHandler("reset_geral", reset_geral))
app.add_handler(CommandHandler("resumo", resumo))

app.run_polling()

import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# ================= CONFIG =================
TOKEN = os.getenv("8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk")

USUARIOS = [5364076144, 5507658531]  # você e o César
DATA_FILE = "dados.json"

# ================= DADOS =================
def inicializar_dados():
    if not os.path.exists(DATA_FILE):
        dados = {
            "contas": {},
            "cartoes": {},
            "gastos": []
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)

def carregar_dados():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return

    teclado = [
        [InlineKeyboardButton("➕ Registrar gasto", callback_data="add_gasto")],
        [InlineKeyboardButton("💳 Gasto no cartão", callback_data="cartao")],
        [InlineKeyboardButton("🏦 Cadastrar conta", callback_data="conta")],
        [InlineKeyboardButton("📊 Resumo", callback_data="resumo")],
        [InlineKeyboardButton("♻️ Resetar gastos", callback_data="resetar")]
    ]

    await update.message.reply_text(
        "📱 *Controle Financeiro*\nEscolha uma opção:",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

# ================= BOTÕES =================
async def botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mensagens = {
        "add_gasto": "Use:\n/gasto <valor> <descrição opcional>",
        "cartao": "Use:\n/gastocartao <nome do cartão> <valor>",
        "conta": "Use:\n/conta <nome da conta> <valor>",
        "resetar": "Use:\n/resetar",
    }

    if query.data == "resumo":
        dados = carregar_dados()
        texto = ["📊 *Resumo financeiro*"]

        if dados["contas"]:
            texto.append("\n🏦 Contas:")
            for nome, valor in dados["contas"].items():
                texto.append(f"- {nome}: R$ {valor:.2f}")

        if dados["cartoes"]:
            texto.append("\n💳 Cartões:")
            for nome, lista in dados["cartoes"].items():
                total = sum(i["valor"] for i in lista)
                texto.append(f"- {nome}: R$ {total:.2f}")

        if dados["gastos"]:
            total = sum(g["valor"] for g in dados["gastos"])
            texto.append(f"\n💸 Total de gastos: R$ {total:.2f}")

        await query.edit_message_text("\n".join(texto), parse_mode="Markdown")
        return

    await query.edit_message_text(mensagens.get(query.data, "Opção inválida"))

# ================= COMANDOS =================
def parse_valor(valor):
    return float(valor.replace(",", "."))

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    if not context.args:
        await update.message.reply_text("Use /gasto <valor> <descrição>")
        return

    try:
        valor = parse_valor(context.args[0])
    except:
        await update.message.reply_text("❌ Valor inválido")
        return

    descricao = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    dados = carregar_dados()
    dados["gastos"].append({
        "usuario": update.effective_user.id,
        "valor": valor,
        "descricao": descricao
    })
    salvar_dados(dados)

    await update.message.reply_text(f"✅ Gasto registrado: R$ {valor:.2f}")

async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use /gastocartao <nome cartão> <valor>")
        return

    nome = " ".join(context.args[:-1])
    try:
        valor = parse_valor(context.args[-1])
    except:
        await update.message.reply_text("❌ Valor inválido")
        return

    dados = carregar_dados()
    if nome not in dados["cartoes"]:
        await update.message.reply_text("❌ Cartão não cadastrado")
        return

    dados["cartoes"][nome].append({
        "usuario": update.effective_user.id,
        "valor": valor
    })
    salvar_dados(dados)

    await update.message.reply_text(f"💳 Gasto registrado no {nome}: R$ {valor:.2f}")

async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use /conta <nome> <valor>")
        return

    nome = " ".join(context.args[:-1])
    try:
        valor = parse_valor(context.args[-1])
    except:
        await update.message.reply_text("❌ Valor inválido")
        return

    dados = carregar_dados()
    dados["contas"][nome] = valor
    salvar_dados(dados)

    await update.message.reply_text(f"🏦 Conta {nome} cadastrada: R$ {valor:.2f}")

async def resetar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    dados = carregar_dados()
    dados["gastos"] = []
    dados["cartoes"] = {}
    salvar_dados(dados)
    await update.message.reply_text("♻️ Gastos e cartões resetados")

# ================= ALERTAS =================
async def alertas(context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    for user in USUARIOS:
        msg = ["⏰ *Lembrete financeiro*"]

        for nome, valor in dados["contas"].items():
            msg.append(f"🏦 {nome}: R$ {valor:.2f}")

        for nome, lista in dados["cartoes"].items():
            total = sum(i["valor"] for i in lista)
            msg.append(f"💳 {nome}: R$ {total:.2f}")

        await context.bot.send_message(user, "\n".join(msg), parse_mode="Markdown")

# ================= MAIN =================
def main():
    inicializar_dados()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("gastocartao", gastocartao))
    app.add_handler(CommandHandler("conta", conta))
    app.add_handler(CommandHandler("resetar", resetar))
    app.add_handler(CallbackQueryHandler(botoes))

    app.job_queue.run_repeating(alertas, interval=21600, first=20)

    print("🤖 Bot financeiro rodando")
    app.run_polling()

if __name__ == "__main__":
    main()

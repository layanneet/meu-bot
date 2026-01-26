import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
WEBHOOK_URL = "https://meu-bot-production-df5c.up.railway.app"

DATA_FILE = "dados.json"
USUARIOS = [5364076144, 5507658531]

# Inicializa dados
if not os.path.exists(DATA_FILE):
    dados_iniciais = {
        "contas": {},
        "cartoes": {},
        "gastos": []
    }
    with open(DATA_FILE, "w") as f:
        json.dump(dados_iniciais, f)

def carregar_dados():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f, indent=2)

# --- Comandos ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    teclado = [
        [InlineKeyboardButton("Adicionar Gasto", callback_data="add_gasto")],
        [InlineKeyboardButton("Gastos Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("Contas Mensais", callback_data="contas")],
        [InlineKeyboardButton("Resetar Gastos", callback_data="resetar")]
    ]
    markup = InlineKeyboardMarkup(teclado)
    await update.message.reply_text("Escolha uma opção:", reply_markup=markup)

# --- Callback dos botões ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "add_gasto":
        await query.edit_message_text("Use /gasto <valor> <descrição opcional>")
    elif query.data == "cartoes":
        await query.edit_message_text("Use /gastocartao <nome cartão> <valor>")
    elif query.data == "contas":
        await query.edit_message_text("Use /conta <nome conta> <valor>")
    elif query.data == "resetar":
        dados = carregar_dados()
        dados["gastos"] = []
        salvar_dados(dados)
        await query.edit_message_text("Gastos resetados!")

# --- Gasto comum ---
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    if not context.args:
        await update.message.reply_text("Use /gasto <valor> <descrição opcional>")
        return
    valor_str = context.args[0].replace(",", ".")
    try:
        valor = float(valor_str)
    except:
        await update.message.reply_text("Valor inválido.")
        return
    descricao = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    dados = carregar_dados()
    dados["gastos"].append({
        "usuario": update.effective_user.id,
        "valor": valor,
        "descricao": descricao
    })
    salvar_dados(dados)
    await update.message.reply_text(f"Gasto registrado: R${valor:.2f} {descricao}")

# --- Gasto cartão ---
async def gastocartao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use /gastocartao <nome cartão> <valor>")
        return
    nome = " ".join(context.args[:-1])
    valor_str = context.args[-1].replace(",", ".")
    try:
        valor = float(valor_str)
    except:
        await update.message.reply_text("Valor inválido.")
        return
    dados = carregar_dados()
    if nome not in dados["cartoes"]:
        await update.message.reply_text("Cartão não encontrado!")
        return
    dados["cartoes"][nome].append({
        "usuario": update.effective_user.id,
        "valor": valor
    })
    salvar_dados(dados)
    await update.message.reply_text(f"Gasto no cartão {nome} registrado: R${valor:.2f}")

# --- Adicionar conta ---
async def conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USUARIOS:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use /conta <nome conta> <valor>")
        return
    nome = " ".join(context.args[:-1])
    valor_str = context.args[-1].replace(",", ".")
    try:
        valor = float(valor_str)
    except:
        await update.message.reply_text("Valor inválido.")
        return
    dados = carregar_dados()
    dados["contas"][nome] = valor
    salvar_dados(dados)
    await update.message.reply_text(f"Conta {nome} registrada: R${valor:.2f}")

# --- Alertas automáticos ---
async def alertas(context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_dados()
    for user_id in USUARIOS:
        mensagens = ["💡 Lembrete de contas e cartões:"]
        if dados["contas"]:
            mensagens.append("Contas do mês:")
            for nome, valor in dados["contas"].items():
                mensagens.append(f"- {nome}: R${valor:.2f}")
        if dados["cartoes"]:
            mensagens.append("Gastos nos cartões:")
            for cartao, lista in dados["cartoes"].items():
                total = sum(item["valor"] for item in lista)
                mensagens.append(f"- {cartao}: R${total:.2f}")
        await context.bot.send_message(chat_id=user_id, text="\n".join(mensagens))

# --- Inicializar app ---
app = ApplicationBuilder().token(TOKEN).build()

# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CallbackQueryHandler(button))

# JobQueue para alertas
if app.job_queue:
    app.job_queue.run_repeating(alertas, interval=21600, first=10)  # 6h

# --- Webhook ---
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8443)),
    url_path=TOKEN,
    webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
)

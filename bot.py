import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

USUARIOS_PERMITIDOS = [
    5364076144,
    5507658531
]

NOMES = {
    "5364076144": "Layanne",
    "5507658531": "Júlio César"
}

ARQUIVO = "gastos.json"

def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def autorizado(user_id):
    return user_id in USUARIOS_PERMITIDOS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    await update.message.reply_text(
        "💑 Bot de Finanças\n\n"
        "/gasto valor categoria descrição\n"
        "/meusgastos\n"
        "/resumo\n"
        "/ajuda"
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    await update.message.reply_text(
        "Exemplo:\n"
        "/gasto 50 mercado almoço\n\n"
        "/meusgastos\n"
        "/resumo"
    )

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    try:
        valor = float(context.args[0])
        categoria = context.args[1]
        descricao = " ".join(context.args[2:])
    except:
        await update.message.reply_text(
            "Use assim:\n/gasto 50 mercado almoço"
        )
        return

    dados = carregar_dados()
    user_id = str(update.effective_user.id)
    mes = datetime.now().strftime("%Y-%m")

    dados.setdefault(mes, {})
    dados[mes].setdefault(user_id, [])
    dados[mes][user_id].append({
        "valor": valor,
        "categoria": categoria,
        "descricao": descricao
    })

    salvar_dados(dados)

    await update.message.reply_text(
        f"✅ Gasto registrado\n"
        f"💸 R$ {valor:.2f}\n"
        f"📂 {categoria}"
    )

async def meusgastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    dados = carregar_dados()
    user_id = str(update.effective_user.id)
    mes = datetime.now().strftime("%Y-%m")

    gastos = dados.get(mes, {}).get(user_id, [])
    total = sum(g["valor"] for g in gastos)

    await update.message.reply_text(
        f"👤 Seus gastos em {mes}\n"
        f"💸 Total: R$ {total:.2f}"
    )

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    dados = carregar_dados()
    mes = datetime.now().strftime("%Y-%m")

    mensagem = f"📊 Resumo do mês {mes}\n\n"
    total_geral = 0

    for user_id, gastos in dados.get(mes, {}).items():
        total_user = sum(g["valor"] for g in gastos)
        nome = NOMES.get(user_id, "Usuário")
        mensagem += f"{nome}: R$ {total_user:.2f}\n"
        total_geral += total_user

    mensagem += f"\n💰 Total do casal: R$ {total_geral:.2f}"

    await update.message.reply_text(mensagem)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("meusgastos", meusgastos))
app.add_handler(CommandHandler("resumo", resumo))

print("Bot iniciado")
app.run_polling()

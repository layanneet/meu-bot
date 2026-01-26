import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# 🔐 IDS AUTORIZADOS (VOCÊ E SEU MARIDO)
USUARIOS_PERMITIDOS = [
    5507658531,  # Layanne
    5364076144   # Júlio
]

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
        "💑 *Bot de Finanças do Casal*\n\n"
        "📌 Comandos disponíveis:\n"
        "/gasto valor categoria descrição\n"
        "/meusgastos\n"
        "/resumo\n"
        "/ajuda",
        parse_mode="Markdown"
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    await update.message.reply_text(
        "📝 *Como usar*\n\n"
        "Exemplo de gasto:\n"
        "`/gasto 50 alimentação almoço`\n\n"
        "📊 Ver seus gastos:\n"
        "`/meusgastos`\n\n"
        "📈 Resumo do casal:\n"
        "`/resumo`",
        parse_mode="Markdown"
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
            "❌ Use assim:\n/gasto 50 mercado compras"
        )
        return

    dados = carregar_dados()
    user = str(update.effective_user.id)
    mes = datetime.now().strftime("%Y-%m")

    dados.setdefault(mes, {})
    dados[mes].setdefault(user, [])
    dados[mes][user].append({
        "valor": valor,
        "categoria": categoria,
        "descricao": descricao
    })

    salvar_dados(dados)

    await update.message.reply_text(
        f"✅ *Gasto registrado*\n"
        f"💸 Valor: R$ {valor:.2f}\n"
        f"📂 Categoria: {categoria}\n"
        f"📝 {descricao}",
        parse_mode="Markdown"
    )

async def meusgastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    dados = carregar_dados()
    user = str(update.effective_user.id)
    mes = datetime.now().strftime("%Y-%m")

    gastos = dados.get(mes, {}).get(user, [])
    total = sum(g["valor"] for g in gastos)

    await update.message.reply_text(
        f"👤 *Seus gastos do mês ({mes})*\n"
        f"💸 Total: R$ {total:.2f}",
        parse_mode="Markdown"
    )

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    dados = carregar_dados()
    mes = datetime.now().strftime("%Y-%m")

    total = 0
    for user in dados.get(mes, {}).values():
        total += sum(g["valor"] for g in user)

    await update.message.reply_text(
        f"📊 *Resumo financeiro do casal*\n"
        f"🗓 Mês: {mes}\n"
        f"💸 Total gasto: R$ {total:.2f}",
        parse_mode="Markdown"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("meusgastos", meusgastos))
app.add_handler(CommandHandler("resumo", resumo))

print("Bot de finanças do casal iniciado...")
app.run_polling

import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# Armazenamento simples (memória)
gastos = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Bot de Finanças ativo!\n\n"
        "Comandos:\n"
        "/gasto valor categoria descrição\n"
        "/saldo\n"
        "/resumo"
    )

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        categoria = context.args[1]
        descricao = " ".join(context.args[2:])

        gastos.append(valor)

        await update.message.reply_text(
            f"✅ Gasto registrado!\n"
            f"💸 R$ {valor:.2f}\n"
            f"📂 {categoria}\n"
            f"📝 {descricao}"
        )
    except:
        await update.message.reply_text(
            "❌ Use assim:\n/gasto 25 alimentação almoço"
        )

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(gastos)
    await update.message.reply_text(f"💰 Total de gastos: R$ {total:.2f}")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(gastos)
    await update.message.reply_text(
        f"📊 Resumo financeiro:\n"
        f"Total gasto: R$ {total:.2f}"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("resumo", resumo))

print("Bot de finanças iniciado...")
app.run_polling()

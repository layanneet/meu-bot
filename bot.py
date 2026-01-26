import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "COLOQUE_SEU_TOKEN_AQUI"
ARQ = "dados.json"

USUARIOS = {
    5364076144: "Layanne",
    5507658531: "Julio"
}

# ---------- BASE ----------
def load():
    if not os.path.exists(ARQ):
        with open(ARQ, "w") as f:
            json.dump({}, f)
    with open(ARQ, "r") as f:
        return json.load(f)

def save(d):
    with open(ARQ, "w") as f:
        json.dump(d, f, indent=2)

def auth(update):
    return update.effective_user.id in USUARIOS

def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# ---------- MENU ----------
def menu_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Saldo", callback_data="saldo")],
        [InlineKeyboardButton("📄 Extrato", callback_data="extrato")],
        [InlineKeyboardButton("💳 Cartões", callback_data="cartoes")],
        [InlineKeyboardButton("🧾 Contas", callback_data="contas")],
        [InlineKeyboardButton("🎯 Metas", callback_data="metas")]
    ])

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return
    await update.message.reply_text(
        "🏦 Banco Digital Familiar\nEscolha uma opção:",
        reply_markup=menu_principal()
    )

# ---------- CALLBACKS + ALERTAS ----------
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update):
        return

    q = update.callback_query
    await q.answer()
    d = load()

    avisos = []

    for nome, conta in d.get("contas", {}).items():
        if not conta["paga"]:
            avisos.append(f"🔔 Conta em aberto: {nome} R$ {conta['valor']:.2f}")

    for nome, cartao in d.get("cartoes", {}).items():
        usado = sum(cartao["gastos"])
        if usado >= cartao["limite"] * 0.8:
            avisos.append(f"⚠️ Cartão {nome} acima de 80% do limite")

    alerta = "\n\n" + "\n".join(avisos) if avisos else ""

    if q.data == "saldo":
        await q.edit_message_text(
            f"💰 Saldo atual\nR$ {d.get('saldo',0):.2f}{alerta}",
            reply_markup=menu_principal()
        )

    elif q.data == "extrato":
        texto = "📄 Extrato\n\n"
        for e in d.get("extrato", [])[-10:]:
            texto += f"{e['data']} | {e['user']} | {e['tipo']} R$ {e['valor']:.2f}\n"
        await q.edit_message_text(
            (texto if d.get("extrato") else "Sem movimentações") + alerta,
            reply_markup=menu_principal()
        )

    elif q.data == "cartoes":
        texto = "💳 Cartões\n\n"
        for n,c in d.get("cartoes", {}).items():
            usado = sum(c["gastos"])
            texto += (
                f"{n}\n"
                f"Usado: R$ {usado:.2f}\n"
                f"Disponível: R$ {c['limite']-usado:.2f}\n\n"
            )
        await q.edit_message_text(
            (texto if d.get("cartoes") else "Nenhum cartão cadastrado") + alerta,
            reply_markup=menu_principal()
        )

    elif q.data == "contas":
        texto = "🧾 Contas\n\n"
        for n,c in d.get("contas", {}).items():
            texto += f"{n}: R$ {c['valor']:.2f} {'✅' if c['paga'] else '❌'}\n"
        await q.edit_message_text(
            (texto if d.get("contas") else "Nenhuma conta cadastrada") + alerta,
            reply_markup=menu_principal()
        )

    elif q.data == "metas":
        texto = "🎯 Metas\n\n"
        for n,v in d.get("metas", {}).items():
            texto += f"{n}: R$ {v:.2f}\n"
        await q.edit_message_text(
            (texto if d.get("metas") else "Nenhuma meta cadastrada") + alerta,
            reply_markup=menu_principal()
        )

# ---------- COMANDOS ----------
async def saldo(update, context):
    if not auth(update) or not context.args:
        return
    d = load()
    d["saldo"] = float(context.args[0])
    save(d)
    await update.message.reply_text("Saldo definido com sucesso")

async def entrada(update, context):
    if not auth(update) or not context.args:
        return
    v = float(context.args[0])
    d = load()
    d["saldo"] = d.get("saldo",0) + v
    d.setdefault("extrato", []).append({
        "tipo":"entrada",
        "valor":v,
        "user":USUARIOS[update.effective_user.id],
        "data":agora()
    })
    save(d)
    await update.message.reply_text("Entrada registrada")

async def gasto(update, context):
    if not auth(update) or not context.args:
        return
    v = float(context.args[0])
    d = load()
    d["saldo"] = d.get("saldo",0) - v
    d.setdefault("extrato", []).append({
        "tipo":"gasto",
        "valor":v,
        "user":USUARIOS[update.effective_user.id],
        "data":agora()
    })
    save(d)
    await update.message.reply_text("Gasto registrado")

async def cartao(update, context):
    if not auth(update) or len(context.args) < 2:
        return
    d = load()
    d.setdefault("cartoes", {})[context.args[0]] = {
        "limite": float(context.args[1]),
        "gastos": []
    }
    save(d)
    await update.message.reply_text("Cartão criado")

async def gastocartao(update, context):
    if not auth(update) or len(context.args) < 2:
        return
    d = load()
    d["cartoes"][context.args[0]]["gastos"].append(float(context.args[1]))
    save(d)
    await update.message.reply_text("Gasto no cartão registrado")

async def conta(update, context):
    if not auth(update) or len(context.args) < 2:
        return
    d = load()
    d.setdefault("contas", {})[context.args[0]] = {
        "valor": float(context.args[1]),
        "paga": False
    }
    save(d)
    await update.message.reply_text("Conta adicionada")

async def meta(update, context):
    if not auth(update) or len(context.args) < 2:
        return
    d = load()
    d.setdefault("metas", {})[context.args[0]] = float(context.args[1])
    save(d)
    await update.message.reply_text("Meta criada")

# ---------- APP ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callbacks))

app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("cartao", cartao))
app.add_handler(CommandHandler("gastocartao", gastocartao))
app.add_handler(CommandHandler("conta", conta))
app.add_handler(CommandHandler("meta", meta))

app.run_polling()

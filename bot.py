import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------- CONFIGURAÇÃO ----------
TOKEN = "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk"
ARQ = "dados.json"

USUARIOS = {
    5364076144: "Layanne",
    5507658531: "Julio"
}

# ---------- FUNÇÕES AUXILIARES ----------
def load():
    if not os.path.exists(ARQ):
        with open(ARQ, "w") as f:
            json.dump({"saldo":0,"extrato":[],"cartoes":{},"contas":{},"metas":{}}, f)
    with open(ARQ, "r") as f:
        return json.load(f)

def save(d):
    with open(ARQ, "w") as f:
        json.dump(d, f, indent=2)

def auth(update):
    return update.effective_user.id in USUARIOS

def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def parse_valor(valor_str):
    return float(valor_str.replace(",", "."))

# ---------- MENU PRINCIPAL ----------
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

# ---------- CALLBACKS ----------
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
        if usado >= cartao["limite"]*0.8:
            avisos.append(f"⚠️ Cartão {nome} acima de 80% do limite")

    alerta = "\n\n" + "\n".join(avisos) if avisos else ""

    if q.data == "saldo":
        texto = f"💰 Saldo total: R$ {d.get('saldo',0):.2f}\n\n"
        for uid, nome in USUARIOS.items():
            total_usuario = sum(e["valor"] for e in d.get("extrato",[]) if e["user_id"]==uid and e["tipo"]=="entrada") - sum(e["valor"] for e in d.get("extrato",[]) if e["user_id"]==uid and e["tipo"]=="gasto")
            texto += f"{nome}: R$ {total_usuario:.2f}\n"
        await q.edit_message_text(texto+alerta, reply_markup=menu_principal())

    elif q.data == "extrato":
        texto = "📄 Extrato\n\n"
        for e in d.get("extrato", [])[-10:]:
            usuario = USUARIOS.get(e["user_id"], "Desconhecido")
            texto += f"{e['data']} | {usuario} | {e['tipo']} R$ {e['valor']:.2f} - {e.get('desc','')}\n"
        await q.edit_message_text((texto if d.get("extrato") else "Sem movimentações")+alerta, reply_markup=menu_principal())

    elif q.data == "cartoes":
        texto = "💳 Cartões\n\n"
        for n,c in d.get("cartoes", {}).items():
            usado = sum(c["gastos"])
            texto += f"{n}\nUsado: R$ {usado:.2f}\nDisponível: R$ {c['limite']-usado:.2f}\n\n"
        await q.edit_message_text((texto if d.get("cartoes") else "Nenhum cartão cadastrado")+alerta, reply_markup=menu_principal())

    elif q.data == "contas":
        texto = "🧾 Contas\n\n"
        for n,c in d.get("contas", {}).items():
            texto += f"{n}: R$ {c['valor']:.2f} {'✅' if c['paga'] else '❌'}\n"
        await q.edit_message_text((texto if d.get("contas") else "Nenhuma conta cadastrada")+alerta, reply_markup=menu_principal())

    elif q.data == "metas":
        texto = "🎯 Metas\n\n"
        for n,v in d.get("metas", {}).items():
            texto += f"{n}: R$ {v:.2f}\n"
        await q.edit_message_text((texto if d.get("metas") else "Nenhuma meta cadastrada")+alerta, reply_markup=menu_principal())

# ---------- COMANDOS ----------
async def saldo(update, context):
    if not auth(update) or not context.args:
        return
    d = load()
    valor = parse_valor(context.args[-1])
    d["saldo"] = valor
    save(d)
    await update.message.reply_text(f"Saldo total definido: R$ {valor:.2f}")

async def entrada(update, context):
    if not auth(update) or len(context.args)<2:
        return
    valor = parse_valor(context.args[-1])
    nome = " ".join(context.args[:-1])
    uid = update.effective_user.id
    d = load()
    d["saldo"] = d.get("saldo",0) + valor
    d.setdefault("extrato",[]).append({"tipo":"entrada","valor":valor,"user":nome,"user_id":uid,"data":agora(),"desc":""})
    save(d)
    await update.message.reply_text(f"Entrada de R$ {valor:.2f} registrada para {nome}")

async def gasto(update, context):
    if not auth(update) or len(context.args)<2:
        return
    valor = parse_valor(context.args[-1])
    desc = " ".join(context.args[1:-1]) if len(context.args)>2 else ""
    uid = int(context.args[0])
    if uid not in USUARIOS:
        await update.message.reply_text("❌ Usuário não encontrado!")
        return
    nome = USUARIOS[uid]
    d = load()
    d["saldo"] = d.get("saldo",0) - valor
    d.setdefault("extrato",[]).append({"tipo":"gasto","valor":valor,"user":nome,"user_id":uid,"data":agora(),"desc":desc})
    save(d)
    await update.message.reply_text(f"Gasto de R$ {valor:.2f} registrado para {nome} ({desc})")

async def cartao(update, context):
    if not auth(update) or len(context.args)<2:
        return
    nome_cartao = " ".join(context.args[:-1])
    limite = parse_valor(context.args[-1])
    d = load()
    d.setdefault("cartoes",{})[nome_cartao] = {"limite":limite,"gastos":[]}
    save(d)
    await update.message.reply_text(f"Cartão '{nome_cartao}' criado com limite R$ {limite:.2f}")

async def gastocartao(update, context):
    if not auth(update) or len(context.args)<2:
        return
    nome_cartao = " ".join(context.args[:-1])
    valor = parse_valor(context.args[-1])
    d = load()
    if nome_cartao not in d.get("cartoes", {}):
        await update.message.reply_text(f"❌ Cartão '{nome_cartao}' não encontrado!")
        return
    d["cartoes"][nome_cartao]["gastos"].append(valor)
    save(d)
    await update.message.reply_text(f"Gasto de R$ {valor:.2f} registrado no cartão '{nome_cartao}'")

async def conta(update, context):
    if not auth(update) or len(context.args)<2:
        return
    nome_conta = " ".join(context.args[:-1])
    valor = parse_valor(context.args[-1])
    d = load()
    d.setdefault("contas",{})[nome_conta] = {"valor":valor,"paga":False}
    save(d)
    await update.message.reply_text(f"Conta '{nome_conta}' adicionada no valor R$ {valor:.2f}")

async def meta(update, context):
    if not auth(update) or len(context.args)<2:
        return
    nome_meta = " ".join(context.args[:-1])
    valor = parse_valor(context.args[-1])
    d = load()
    d.setdefault("metas",{})[nome_meta] = valor
    save(d)
    await update.message.reply_text(f"Meta '{nome_meta}' criada no valor R$ {valor:.2f}")

# ---------- INICIALIZAÇÃO DO BOT ----------
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

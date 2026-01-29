import os, json
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN", "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USUARIOS = [5364076144, 5507658531]
ARQ = "dados.json"

app = Flask(__name__)

# ================= DADOS =================
def load():
    if not os.path.exists(ARQ):
        return {
            "saldo": 0,
            "cartoes": [],
            "parcelados": [],
            "emprestimos": [],
            "contas": [],
            "historico": []
        }
    with open(ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def save(d):
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def ok(uid): return uid in USUARIOS
def num(v): return float(v.replace(",", "."))

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update.effective_user.id): return
    teclado = [
        ["/entrada", "/gasto"],
        ["/addcartao", "/cartoes"],
        ["/parcelado", "/parcelamentos"],
        ["/emprestimo", "/emprestimos"],
        ["/addconta", "/contas"],
        ["/resumo", "/dividas"],
        ["/resetmes", "/reset_geral"]
    ]
    await update.message.reply_text(
        "💰 Assistente Financeiro",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# ================= ENTRADA / GASTO =================
async def entrada(update, context):
    d = load()
    valor = num(context.args[0])
    d["saldo"] += valor
    save(d)
    await update.message.reply_text(f"✅ Entrada R$ {valor:.2f}")

async def gasto(update, context):
    d = load()
    valor = num(context.args[0])
    d["saldo"] -= valor
    save(d)
    await update.message.reply_text(f"❌ Gasto R$ {valor:.2f}")

# ================= CARTÕES =================
async def addcartao(update, context):
    d = load()
    d["cartoes"].append({
        "nome": context.args[0],
        "limite": num(context.args[1]),
        "fatura": 0
    })
    save(d)
    await update.message.reply_text("💳 Cartão adicionado")

async def cartoes(update, context):
    d = load()
    msg = "💳 CARTÕES:\n"
    for i, c in enumerate(d["cartoes"], 1):
        msg += f"{i}. {c['nome']} — R$ {c['fatura']:.2f}/{c['limite']:.2f}\n"
    await update.message.reply_text(msg)

async def excluircartao(update, context):
    d = load()
    i = int(context.args[0]) - 1
    d["cartoes"].pop(i)
    save(d)
    await update.message.reply_text("🗑️ Cartão removido")

# ================= PARCELADOS =================
async def parcelado(update, context):
    d = load()
    d["parcelados"].append({
        "cartao": context.args[0],
        "valor": num(context.args[1]),
        "restantes": int(context.args[2]),
        "desc": " ".join(context.args[3:])
    })
    save(d)
    await update.message.reply_text("🧾 Parcelado criado")

async def parcelamentos(update, context):
    d = load()
    msg = "🧾 PARCELAMENTOS:\n"
    for i, p in enumerate(d["parcelados"], 1):
        msg += f"{i}. {p['desc']} — {p['restantes']}x R$ {p['valor']:.2f}\n"
    await update.message.reply_text(msg)

async def cancelarparcelado(update, context):
    d = load()
    d["parcelados"].pop(int(context.args[0]) - 1)
    save(d)
    await update.message.reply_text("❌ Parcelado cancelado")

# ================= EMPRÉSTIMOS =================
async def emprestimo(update, context):
    d = load()
    d["emprestimos"].append({
        "valor": num(context.args[0]),
        "desc": " ".join(context.args[1:])
    })
    save(d)
    await update.message.reply_text("💸 Empréstimo registrado")

async def emprestimos(update, context):
    d = load()
    msg = "💸 EMPRÉSTIMOS:\n"
    for i, e in enumerate(d["emprestimos"], 1):
        msg += f"{i}. {e['desc']} — R$ {e['valor']:.2f}\n"
    await update.message.reply_text(msg)

async def cancelaremprestimo(update, context):
    d = load()
    d["emprestimos"].pop(int(context.args[0]) - 1)
    save(d)
    await update.message.reply_text("🗑️ Empréstimo removido")

# ================= CONTAS =================
async def addconta(update, context):
    d = load()
    d["contas"].append({
        "nome": context.args[0],
        "valor": num(context.args[1])
    })
    save(d)
    await update.message.reply_text("📌 Conta adicionada")

async def contas(update, context):
    d = load()
    msg = "📌 CONTAS:\n"
    for i, c in enumerate(d["contas"], 1):
        msg += f"{i}. {c['nome']} — R$ {c['valor']:.2f}\n"
    await update.message.reply_text(msg)

async def excluirconta(update, context):
    d = load()
    d["contas"].pop(int(context.args[0]) - 1)
    save(d)
    await update.message.reply_text("🗑️ Conta removida")

# ================= RESET =================
async def resetmes(update, context):
    d = load()
    for p in d["parcelados"]:
        p["restantes"] -= 1
    d["parcelados"] = [p for p in d["parcelados"] if p["restantes"] > 0]
    save(d)
    await update.message.reply_text("🔄 Mês resetado")

async def reset_geral(update, context):
    save(load().__class__())
    await update.message.reply_text("🚨 RESET TOTAL")

# ================= RESUMOS =================
async def resumo(update, context):
    d = load()
    await update.message.reply_text(f"📊 Saldo: R$ {d['saldo']:.2f}")

async def dividas(update, context):
    d = load()
    total = sum(e["valor"] for e in d["emprestimos"])
    await update.message.reply_text(f"💸 Dívidas totais: R$ {total:.2f}")

# ================= BOT =================
bot = ApplicationBuilder().token(TOKEN).build()

handlers = [
    start, entrada, gasto, addcartao, cartoes, excluircartao,
    parcelado, parcelamentos, cancelarparcelado,
    emprestimo, emprestimos, cancelaremprestimo,
    addconta, contas, excluirconta,
    resetmes, reset_geral, resumo, dividas
]

for h in handlers:
    bot.add_handler(CommandHandler(h.__name__, h))

@app.route("/", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot.bot)
    await bot.process_update(update)
    return "ok"

if __name__ == "__main__":
    bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
                 )

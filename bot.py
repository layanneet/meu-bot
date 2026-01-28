import os, json
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN", "8595111952:AAG3ixV_avi93HHjV9pv7kofWdqQ3hBp7yk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USUARIOS = [5364076144, 5507658531]
ARQ = "dados.json"

flask_app = Flask(__name__)

def carregar():
    if not os.path.exists(ARQ):
        return {}
    with open(ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar(d):
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def num(v): return float(v.replace(",", "."))

def init(d, u):
    d.setdefault(u, {
        "saldo": 0,
        "cartoes": {},
        "parcelados": [],
        "emprestimos": [],
        "contas": []
    })

def ok(update): return update.effective_user.id in USUARIOS

async def start(update, ctx):
    if not ok(update): return
    kb = [
        ["/entrada", "/gasto"],
        ["/novocartao", "/gastocartao"],
        ["/parcelado", "/emprestimo"],
        ["/cartoes", "/resumo"],
        ["/resetcartoes", "/resetgeral"]
    ]
    await update.message.reply_text("💰 Banco Digital", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def entrada(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id); init(d,u)
    v = num(ctx.args[0]); d[u]["saldo"] += v; salvar(d)
    await update.message.reply_text(f"➕ Entrada R$ {v:.2f}")

async def gasto(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id); init(d,u)
    v = num(ctx.args[0]); d[u]["saldo"] -= v; salvar(d)
    await update.message.reply_text(f"➖ Gasto R$ {v:.2f}")

async def novocartao(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id); init(d,u)
    nome = " ".join(ctx.args[:-1]); limite = num(ctx.args[-1])
    d[u]["cartoes"][nome] = {"limite": limite, "usado": 0}
    salvar(d); await update.message.reply_text("💳 Cartão criado")

async def gastocartao(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    nome = ctx.args[0]; valor = num(ctx.args[1])
    if nome not in d[u]["cartoes"]:
        await update.message.reply_text("❌ Cartão não existe"); return
    c = d[u]["cartoes"][nome]
    if c["usado"] + valor > c["limite"]:
        await update.message.reply_text("🚨 Limite estourado"); return
    c["usado"] += valor; salvar(d)
    await update.message.reply_text(f"💳 Gasto R$ {valor:.2f}")

async def parcelado(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    cartao = ctx.args[0]; total = num(ctx.args[1]); meses = int(ctx.args[2])
    desc = " ".join(ctx.args[3:])
    d[u]["parcelados"].append({"cartao":cartao,"valor":total/meses,"restantes":meses,"desc":desc})
    salvar(d); await update.message.reply_text("🧾 Parcelado criado")

async def emprestimo(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    nome = ctx.args[0]; total = num(ctx.args[1]); meses = int(ctx.args[2])
    desc = " ".join(ctx.args[3:])
    d[u]["emprestimos"].append({"nome":nome,"valor":total/meses,"restantes":meses,"desc":desc})
    salvar(d); await update.message.reply_text("📉 Empréstimo criado")

async def apagarconta(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    nome = " ".join(ctx.args)
    d[u]["contas"] = [c for c in d[u]["contas"] if c["nome"] != nome]
    salvar(d); await update.message.reply_text("🗑 Conta apagada")

async def apagarcartao(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    nome = " ".join(ctx.args)
    d[u]["cartoes"].pop(nome, None)
    salvar(d); await update.message.reply_text("🗑 Cartão apagado")

async def apagaremprestimo(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    nome = " ".join(ctx.args)
    d[u]["emprestimos"] = [e for e in d[u]["emprestimos"] if e["nome"] != nome]
    salvar(d); await update.message.reply_text("🗑 Empréstimo apagado")

async def apagarparcelado(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    desc = " ".join(ctx.args)
    d[u]["parcelados"] = [p for p in d[u]["parcelados"] if p["desc"] != desc]
    salvar(d); await update.message.reply_text("🗑 Parcelado apagado")

async def resetcartoes(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    for c in d[u]["cartoes"].values(): c["usado"] = 0
    salvar(d); await update.message.reply_text("♻️ Cartões zerados")

async def resetgeral(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    d[u]["saldo"] = 0; d[u]["parcelados"] = []; d[u]["emprestimos"] = []
    for c in d[u]["cartoes"].values(): c["usado"] = 0
    salvar(d); await update.message.reply_text("🚨 RESET TOTAL")

async def resumo(update, ctx):
    if not ok(update): return
    d = carregar(); u = str(update.effective_user.id)
    msg = f"📊 Saldo: R$ {d[u]['saldo']:.2f}\n"
    for c,v in d[u]["cartoes"].items():
        msg += f"{c}: {v['usado']}/{v['limite']}\n"
    await update.message.reply_text(msg)

app = ApplicationBuilder().token(TOKEN).build()

for cmd, func in {
    "start":start,"entrada":entrada,"gasto":gasto,"novocartao":novocartao,
    "gastocartao":gastocartao,"parcelado":parcelado,"emprestimo":emprestimo,
    "apagarconta":apagarconta,"apagarcartao":apagarcartao,
    "apagaremprestimo":apagaremprestimo,"apagarparcelado":apagarparcelado,
    "resetcartoes":resetcartoes,"resetgeral":resetgeral,"resumo":resumo
}.items():
    app.add_handler(CommandHandler(cmd, func))

@flask_app.route("/", methods=["POST"])
async def webhook():
    await app.process_update(Update.de_json(request.get_json(force=True), app.bot))
    return "ok"

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )

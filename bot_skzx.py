# Bot do SKZX: comandos /ban, /unban e /banlist + endpoint /banlist.json que o script lê
# (coloque https://SEU-SERVIDOR/banlist.json em SKZX_BANLIST_URL no script).
# Instalar: pip install discord.py aiohttp
# Variável de ambiente: DISCORD_TOKEN (token do bot, criado em discord.com/developers)
import os
import json
import discord
from discord import app_commands
from aiohttp import web

TOKEN = os.environ["DISCORD_TOKEN"]
PORT = int(os.environ.get("PORT", 8080))
ARQUIVO = "bans.json"


def carregar():
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar():
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(bans, f, ensure_ascii=False, indent=2)


bans = carregar()


class SKZXBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        app = web.Application()
        app.add_routes([web.get("/banlist.json", self.lista)])
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", PORT).start()

    async def lista(self, request):
        return web.json_response(
            {"banidos": [{"id": int(uid), "motivo": d["reason"]} for uid, d in bans.items()]}
        )


bot = SKZXBot()


@bot.tree.command(name="ban", description="Bane um usuário do SKZX")
@app_commands.describe(userid="UserId do Roblox", motivo="Motivo do banimento")
@app_commands.default_permissions(administrator=True)
async def ban(i: discord.Interaction, userid: str, motivo: str = "Não informado"):
    if not userid.isdigit():
        await i.response.send_message("UserId inválido (só números).", ephemeral=True)
        return
    bans[userid] = {"reason": motivo, "by": str(i.user)}
    salvar()
    await i.response.send_message(f"✅ `{userid}` banido: {motivo}", ephemeral=True)


@bot.tree.command(name="unban", description="Remove o banimento de um usuário")
@app_commands.describe(userid="UserId do Roblox")
@app_commands.default_permissions(administrator=True)
async def unban(i: discord.Interaction, userid: str):
    if bans.pop(userid, None):
        salvar()
        await i.response.send_message(f"✅ `{userid}` desbanido.", ephemeral=True)
    else:
        await i.response.send_message("Esse UserId não está banido.", ephemeral=True)


@bot.tree.command(name="banlist", description="Lista os usuários banidos")
@app_commands.default_permissions(administrator=True)
async def banlist(i: discord.Interaction):
    if not bans:
        await i.response.send_message("Ninguém banido.", ephemeral=True)
        return
    linhas = [f"`{uid}` — {d['reason']}" for uid, d in list(bans.items())[:25]]
    await i.response.send_message("\n".join(linhas), ephemeral=True)


bot.run(TOKEN)

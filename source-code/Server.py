import discord
from Network import Network

CHANNELS: dict = {
    "chat": 1024343901517123655,
    "questions-and-answers": 1025441734508941393,
    "terminal": 1025442786801111091,
    "default": 1025511904803831919,
}

CATEGORIS: dict = {
    "GLOBAL": 1024343901038985270,
    "SQUADS": 1025444416527278131,
}

ROLES: dict = {
    "Admin": 1025432915561168896,
    "Hacker": 1025436309851996191,
    "Squad-Lider": 1030199156947558510,
    "Squad-CoLider": 1030440951077929020,
    "Squad-Master": 1030574174512623616,
    "Squad-Recruit": 1030572112068485212,
}


class Server:

    network: Network = None
    channels: tuple = None

    async def __terminal__(self, channel: discord.TextChannel, author: discord.Member, args: tuple):
        pass

    async def __squad__(self, channel: discord.TextChannel, author: discord.Member, args: tuple):
        pass

    def __init__(self):
        self.network = Network()
        bot: discord.Client = None

        bot = discord.Client(intents=discord.Intents.all())

        @bot.event
        async def on_ready():
            pass

        async def on_message(message: discord.Message):
            author: discord.Member = None
            channel: discord.TextChannel = None
            args: list = None
            
            author = bot.get_user(message.author.id)
            channel = bot.get_channel(message.channel.id)
            
            if author.id == bot.user.id:
                return
            
            if channel.category_id == CATEGORIS["GLOBAL"] and channel.id != CHANNELS["terminal"]:
                return
            
            args = message.content.split()

            if channel.category_id == CATEGORIS["SQUADS"]:
                pass

            elif channel.id == CHANNELS["terminal"]:
                pass

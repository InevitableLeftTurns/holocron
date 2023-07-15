import discord
from util.tip import Tip
from discord.ext import commands

class SendConquestTips(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tip_storage = {
            # "sectors": {
            #     1: {
            #         "nodes": {},
            #         "boss": {
            #             "feats": [],
            #             "tips": []
            #         },
            #         "mini": {
            #             "feats": [],
            #             "tips": []
            #         },
            #         "feats": {
            #             1: ""  # through 4
            #         }
            #     },
            #     2: {},
            #     3: {},
            #     4: {},
            #     5: {}
            # }
            # "globals": {
            #     1: [],
            #     2: []  # through 8
            # }
        }
        self.create_tip_storage()
        self.dummy_populate()

    def create_tip_storage(self):
        self.tip_storage["sectors"] = {}
        for i in range(5):
            self.tip_storage["sectors"][i+1] = {}
            self.tip_storage["sectors"][i+1]["boss"] = {"feats": [], "tips": []}
            self.tip_storage["sectors"][i+1]["mini"] = {"feats": [], "tips": []}
            self.tip_storage["sectors"][i+1]["nodes"] = {}
            self.tip_storage["sectors"][i+1]["feats"] = {}
            self.tip_storage["globals"] = {}
            for j in range(4):
                self.tip_storage["sectors"][i+1]["feats"][j+1] = []
            for j in range(8):
                self.tip_storage["globals"][j+1] = []

    def dummy_populate(self):
        self.tip_storage["globals"][1].append(Tip("uaq", "this is a tip for g1"))

    """
    tip_location- 
    syntax: sector,sector number,node/mini/boss/feat,number (op)
    examples: s1m, s3b, s3n13, s2f4
    -or-
    syntax: global,number
    examples: g1, g4, g8
    """
    @commands.command(name="tips", aliases=["t"], description="Sends tips and tricks for the active conquest")
    async def send_tips(self, ctx: commands.Context, tip_location: str):
        if tip_location[0] == 'g':
            try:
                global_feat_num = int(tip_location[1])

                tips_to_send = ""
                tip: Tip
                for tip in self.tip_storage["globals"][global_feat_num]:
                    tips_to_send += f"**Tip from {tip.author}:**\n"
                    tips_to_send += tip.content + "\n\n"

                if len(tips_to_send) == 0:
                    tips_to_send = f"There are currently no tips for Global Feat {global_feat_num}."
                await ctx.author.send(tips_to_send)
                return

            except ValueError:
                await ctx.author.send("Queries for Global Feats must have the second character be the number of Global "
                                      "Feat you want tips for.")
                return

            except IndexError:
                await ctx.author.send("Queries for global feats must be in the format `g[number]`, where `number` is "
                                      "the number of the global feat that you want to look at.")
                return

            except KeyError:
                await ctx.author.send(f"There is no Global Feat associated with the number {global_feat_num}. Try a "
                                      f"number between and including 1 through 8.")

        elif tip_location[0] == 's':
            pass
        else:
            await ctx.author.send("Queries to tips must start with an `s` to identify a sector or `g` to identify"
                                  "global feats")


async def setup(bot):
    await bot.add_cog(SendConquestTips(bot))

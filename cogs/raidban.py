import discord
import datetime
import time
import time
import datetime

from discord import guild
from discord.ext import commands

import libs.config as config
from libs.embedmaker import officialEmbed

####################
# Config variables #
####################

raid_time = config.get_config("raid_threshold")["time"]
max_raid_users = config.get_config("raid_threshold")["users"]
staff_channel = config.get_config("channels")["staff_lounge"]

############
# COG Body #
############


def isTooYoung(created_at):
    now = datetime.date.today()
    diff = now - created_at

    return diff.days < 7


class RaidBan(commands.Cog, name="Staff Vote"):
    def __init__(self, bot):
        self.bot = bot
        self.alert_on = True
        self.auto_ban = True
        self.current_raiders = []
        self.first_user_time = None

    @commands.command(
        name="raidtoggle",
        description="Toggles the raid alert - on by default",
        hidden=True,
    )
    @commands.has_role(["Lead Mod", "admin"])
    async def raidtoggle(self, ctx):
        self.alert_on = not self.alert_on
        await ctx.send(f"Raid alerts => {self.alert_on}")

    @commands.command(
        name="banall", description="Bans all possible raiders", hidden=True
    )
    @commands.has_role(["Lead Mod", "admin"])
    async def banall(self, ctx):
        await self.ban_raiders(ctx)

    async def ban_raiders(self, channel):
        await channel.send(f"Banning all possible raiders under account limit.")

        for member in self.current_raiders:
            await member.ban()

        await channel.send("Done")

    @commands.Cog.listener()
    async def on_member_join(self, member):

        made_at = member.created_at.date()

        if isTooYoung(made_at):
            self.current_raiders.append(member)

            if self.first_user_time:
                if time.time() - self.first_user_time <= raid_time:
                    if len(self.current_raiders) >= max_raid_users and self.alert_on:
                        raider_info = [
                            f"{member.display_name} | {member.id} | {'Has default avatar' if not member.avatar else 'Has changed avatar'} | {made_at}"
                            for member in self.current_raiders
                        ]
                        embed = officialEmbed("Raid alert triggered")
                        embed.add_field(
                            name="Possible raiders:",
                            value="\n".join(raider_info),
                            inline=False,
                        )
                        channel = self.bot.get_channel(staff_channel)
                        await channel.send(embed=embed)
                        if self.auto_ban:
                            await self.banall(channel)
                    else:
                        self.first_user_time = None
                        self.current_raiders = []
            else:
                self.first_user_time = time.time()


def setup(bot):
    bot.add_cog(RaidAlerts(bot))

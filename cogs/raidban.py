import discord
import datetime
import time
import time
import datetime
import asyncio

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
age = config.get_config("raid_threshold")["age"]
picture = config.get_config("raid_threshold")["picture"]

############
# COG Body #
############


class RaidAlerts(commands.Cog, name="Raid Alerts"):
    def __init__(self, bot):
        self.bot = bot
        self.alert_on = True
        self.current_raiders = []
        self.first_user_time = None
        self.checks = {"Picture": picture, "Age": age}
        self.continue_banning = False

    def isTooYoung(self, created_at):
        now = datetime.date.today()
        diff = now - created_at

        return diff.days < self.checks["Age"]

    @commands.command(
        name="raidtoggle",
        description="Toggles the raid alert - on by default",
        hidden=True,
    )
    @commands.has_any_role("Lead Mod", "admin")
    async def raidtoggle(self, ctx):
        self.alert_on = not self.alert_on
        await ctx.send(f"Raid alerts => {self.alert_on}")

    @commands.command(
        name="ban_all", description="Bans all possible raiders", hidden=True
    )
    @commands.has_any_role("Lead Mod", "admin")
    async def ban_all(self, ctx):
        await ctx.send(
            f"{ctx.author.mention} confiming to this message will ban all raid users and any other users who join afterwards who fit the check until you deactivate it. Are you sure?",
            embed=self.get_raider_info(),
        )

        try:
            msg = await self.bot.wait_for(
                "message",
                check=lambda message: message.author == ctx.author,
                timeout=10,
            )
            await self.ban_raiders(ctx)
            await ctx.send("Done.")
            self.continue_banning = True
        except asyncio.TimeoutError:
            await ctx.send("Cancelled")

    @commands.command(name="check_set", description="Sets config", hidden=True)
    @commands.has_any_role("Lead Mod", "admin")
    async def check_set(self, ctx, image, age):

        self.checks["Picture"] = image
        self.checks["Age"] = age

        await ctx.send("Set sucesfully")

    async def ban_raiders(self, channel):
        for member in self.current_raiders:
            await member.ban()

    def get_raider_info(self):
        raider_info = [
            f"{member.display_name} | {member.id} | {'Has default avatar' if not member.avatar else 'Has changed avatar'} | {member.created_at.date()}"
            for member in self.current_raiders
        ]

        if not raider_info:
            raider_info = ["No raiders"]

        embed = officialEmbed("Raid alert triggered")
        embed.add_field(
            name="Possible raiders:",
            value="\n".join(raider_info),
            inline=False,
        )
        return embed

    @commands.command(name="deactivate_bans", description="Sets config", hidden=True)
    @commands.has_any_role("Lead Mod", "admin")
    async def deactivate_bans(self, ctx):
        self.continue_banning = False
        await ctx.send("Banning has been deactivated")

    @commands.Cog.listener()
    async def on_member_join(self, member):

        channel = self.bot.get_channel(staff_channel)

        if self.isTooYoung(member.created_at.date()):
            if self.continue_banning:
                if self.checks["Picture"] and member.avatar:
                    pass
                else:
                    await channel.send(
                        f"Banning {member.id} | {member.display_name} | {member.created_at.date()}"
                    )
                    await member.ban()
                return

            self.current_raiders.append(member)

            if self.first_user_time:
                if time.time() - self.first_user_time <= raid_time:
                    if len(self.current_raiders) >= max_raid_users and self.alert_on:
                        await channel.send(
                            "<@650476435269484549>", embed=self.get_raider_info()
                        )  # Ping muir in staff lounge

                    else:
                        self.first_user_time = None
                        self.current_raiders = []
            else:
                self.first_user_time = time.time()


def setup(bot):
    bot.add_cog(RaidAlerts(bot))

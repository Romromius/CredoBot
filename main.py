import sys
import os

import discord
from aiohttp.abc import HTTPException
from discord.ext import commands
import logging
import json

from sqlalchemy.exc import IntegrityError

from db.db_session import create_session, global_init
from db.__all_models import *

with open('config.json') as config_file:
    config = json.load(config_file)

level = logging.INFO
if '-debug' in sys.argv:
    level = logging.DEBUG

logging.basicConfig(level=level, handlers=[logging.FileHandler("credo_bot.log"),
                                           logging.StreamHandler()],
                    format="%(asctime)s\t[%(levelname)s]\t%(message)s")
logging.debug('Debug mode')
logging.info('Glory to the Watermelon!')

global_init('credobot.sqlite')

bot = commands.Bot("++", intents=discord.Intents.all())

admins: list[discord.User] = []

#  Bot functionality

@bot.event
async def on_ready():
    logging.info('Credobot started!')
    for i in config['ADMINS']:
        admins.append(await bot.fetch_user(i))
    logging.debug(f'Admin(s): {", ".join([str(i) for i in admins])}')


@bot.event
async def on_command_error(ctx: commands.Context, error):
    logging.error(error)
    await ctx.send(f'Error! {error}')


async def report_admins(message):
    for i in admins:
        await i.send(message)

async def get_discord_by_user(user: User):
    return await bot.fetch_user(user.discord_id)

def get_user_by_discord(discord_user: commands.Context.author) -> User:
    session = create_session()
    user = session.query(User).filter(User.discord_id == discord_user.id).first()
    return user

def is_logged(discord_id):
    session = create_session()
    user = session.query(User).filter(User.discord_id == discord_id).first()
    if user:
        return True
    else:
        return False

async def operate(sender: User, recipient: User,  amount: int | float, commentary: str):
    session = create_session()
    sender.add_money(-1 * amount, commentary)
    await (await get_discord_by_user(sender)).send(f'Operation. Transfer to {recipient.melon_id}: {commentary}')
    recipient.add_money(amount, commentary)
    await (await get_discord_by_user(recipient)).send(f'Operation. Transfer from {sender.melon_id}: {commentary}')
    logging.info(f'Operation. {sender.melon_id} > {amount} > {recipient.melon_id}')
    session.commit()


@bot.command()
async def ping(ctx: commands.Context):
    role = discord.utils.get(ctx.guild.roles, id=1124221236604579840)
    logging.debug('Ping-pong')
    if role in ctx.author.roles:
        await ctx.send(f'pong, my lord. I live at {os.getenv('COMPUTERNAME')}')
    else:
        await ctx.send('pong')


@bot.command()
async def login(ctx: commands.Context, watermelon_id, password):
    session = create_session()
    user = session.query(User).filter(User.melon_id == watermelon_id).first()
    if user:  # Пользователь найден...
        if user.discord_id:  # Но в него уже залогинились!
            if user.discord_id == ctx.author.id:  # Отбой, это он.
                await ctx.send(f'You are already logged in, {watermelon_id}')
            else:
                await ctx.send(f'{ctx.author.name} attempting to log in as {watermelon_id}!')
                await get_discord_by_user(user)
                logging.info(f'Warning! Unsuccessful attempt to log in {watermelon_id}')
        elif user.check_password(password):  # Пароль верный.
            await ctx.send(f'Welcome, {watermelon_id}.')
            user.discord_id = ctx.author.id
            session.commit()
            logging.info(f'{ctx.author.name} logged in as {watermelon_id}')
        else:  # Неверный пароль. Подозрительно.
            await ctx.send('Wrong password. You have been reported.\nIf you forgot your password, contact Government')
            await report_admins(f'User {ctx.author.name} tried to log in {watermelon_id} with wrong password.')
    else:  # Нет такого в БД.
        await ctx.send('This WatermelonID is unknown. You might ask Government to register you.')


@bot.command()
async def logout(ctx: commands.Context):
    session = create_session()
    user = session.query(User).filter(User.discord_id == ctx.author.id).first()
    if user:
        user.discord_id = None
        session.commit()
        await ctx.send('You have logged out.')
        logging.info(f'{user.melon_id} logged out')
    else:
        await ctx.send('You are unknown to me.')


@bot.command()
async def balance(ctx: commands.Context):
    user: User = get_user_by_discord(ctx.author)
    if user:
        await ctx.reply(f'Ваш баланс: {user.balance}')
    else:
        await ctx.reply(f'Please, log in first.')


@bot.command()
async def give(ctx: commands.Context, recipient, amount, *comment):
    session = create_session()
    sender = session.query(User).filter(User.discord_id == ctx.author.id).first()
    receiver = session.query(User).filter(User.melon_id == recipient).first()
    if not sender:
        await ctx.send('You are not logged in.')
        return
    if not receiver:
        await ctx.send('Recipient not found.')
        return

    await operate(sender, receiver, float(amount), ' '.join(comment))
    await ctx.send('Success')


@bot.command()
@commands.has_role('Правительство')
async def add_user(ctx: commands.Context, melon_id):
    session = create_session()
    try:
        user = User()
        user.melon_id = melon_id
        user.set_password('1111')
        session.add(user)
        session.commit()
        await ctx.send('Success.')
        logging.info(f'New user in database: {melon_id}')
    except IntegrityError:
        await ctx.send('This user already exists.')


@bot.command()
@commands.has_role('Правительство')
async def set_password(ctx: commands.Context, user: str, password: str):
    session = create_session()
    user: User | None = session.query(User).filter(User.melon_id == user).first()
    if not user:
        await ctx.send('User not found.')
        return
    user.set_password(password)
    session.commit()
    if user.discord_id:
        await (await bot.fetch_user(user.discord_id)).send('Ваш пароль изменен!')
    logging.info(f'{user.melon_id}\'s password has been changed')
    await ctx.send('Success.')


if __name__ == '__main__':
    logging.info('Starting Credobot...')
    logging.info("Running at " + os.getenv('COMPUTERNAME'))
    token = os.getenv('CREDOBOT_TOKEN')
    bot.run(str(token))

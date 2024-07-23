import discord
from discord.ext import commands
import yaml
import logging

# 設定ファイルを読み込み
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

TOKEN = config["token"]
VOICE_CHANNEL_IDS = config["voice_channel_ids"]
BOT_USER_IDS = config["bot_user_ids"]
log_channel_id = config['log_channel_id']

intents = discord.Intents.default()
intents.members = True  # メンバー情報を取得するために必要
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_voice_state_update(member, before, after):
    for channel_id in VOICE_CHANNEL_IDS:
        voice_channel = discord.utils.get(client.get_all_channels(), id=channel_id)
        if voice_channel:
            # チャンネル内にBOT_USER_IDSに一致するIDが1つでもいるか確認
            bot_in_channel = None
            for bot in voice_channel.members:
                if bot.id in BOT_USER_IDS:
                    bot_in_channel = bot
                    break
            if bot_in_channel and len(voice_channel.members) == 1:
                try:
                    # ボイスチャンネルから切断させる
                    await bot_in_channel.edit(voice_channel=None)
                except discord.Forbidden:
                    print(f"エラーで蹴れなかったよ！！")
                break

    if before.channel != after.channel:
        # 新しいVCに入った場合の処理
        if after.channel is not None and after.channel.id in map(int, VOICE_CHANNEL_IDS):
            # 新しいVCのメンバーリストを取得
            new_channel_members = after.channel.members

            # 新しいVCに誰もいなかった場合
            if len(new_channel_members) == 1:
                # ログ用のチャンネルを取得
                log_channel = client.get_channel(log_channel_id)
                if log_channel is not None:
                    await log_channel.send(f' {after.channel.name} で {member.name} がVCをはじめました。')
                else:
                    print("ログチャンネルが見つかりませんでした")




@client.event
async def on_ready():
    # ボットがログインしたときのイベント
    logging.info(f'{client.user}としてログインしました')

@client.event
async def on_disconnect():
    # ボットが切断されたときのイベント
    logging.warning('ボットが切断されました！')

@client.event
async def on_resumed():
    # ボットが再接続されたときのイベント
    logging.info('ボットが再接続されました！')


client.run(TOKEN)

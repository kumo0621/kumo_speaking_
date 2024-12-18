import discord
from discord.ext import commands
from discord import app_commands
import yaml
import logging
from datetime import datetime

# 設定ファイルを読み込み
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

TOKEN = config["token"]
VOICE_CHANNEL_IDS = config["voice_channel_ids"]
BOT_USER_IDS = config["bot_user_ids"]
log_channel_id = config['log_channel_id']

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True  # これを追加
client = commands.Bot(command_prefix='!', intents=intents)



def is_within_time_range(time_set):
    """現在の時刻が指定された時間範囲内かどうかをチェックする関数"""
    now = datetime.now().time()
    start_time = datetime.strptime(time_set['start'], "%H:%M").time()
    end_time = datetime.strptime(time_set['end'], "%H:%M").time()
    
    if start_time <= end_time:
        return start_time <= now <= end_time
    else:
        # 終了時間が翌日にまたがる場合
        return now >= start_time or now <= end_time


@client.event
async def on_ready():
    synced = await client.tree.sync()
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
                    await log_channel.send(f' {after.channel.name} で {member.display_name}({member.name}) がVCをはじめました。')
                else:
                    print("ログチャンネルが見つかりませんでした")

@client.event
async def on_disconnect():
    # ボットが切断されたときのイベント
    logging.warning('ボットが切断されました！')

@client.event
async def on_resumed():
    # ボットが再接続されたときのイベント
    logging.info('ボットが再接続されました！')



@discord.app_commands.context_menu(name="通話から切断")
async def disconnect_from_voice(interaction: discord.Interaction, member: discord.Member):
    # Botに必要な権限があるか確認
    if not interaction.guild.me.guild_permissions.move_members:
        await interaction.response.send_message("Botに『メンバーを移動する』権限がありません。", ephemeral=True)
        return

    # ユーザーがボイスチャンネルにいるか確認
    if member.voice and member.voice.channel:
        try:
            # ボイスチャンネルを取得
            channel = member.voice.channel

            # ユーザーを通話から切断
            await member.move_to(None)

            # 該当VCにメッセージを送信
            await channel.send(
                f"{interaction.user.display_name} が {member.display_name} を通話から切断しました。"
            )

            # インタラクション応答
            await interaction.response.send_message(
                f"{member.display_name} を通話から切断しました。", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("このユーザーを切断する権限がありません。", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)
    else:
        await interaction.response.send_message(f"{member.display_name} は通話に参加していません。", ephemeral=True)


# コンテキストメニューコマンドを登録
client.tree.add_command(disconnect_from_voice)

client.run(TOKEN)

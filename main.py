# -Импорт библиотек
import configparser
import asyncio
import tenacity
#import random
import os
import re
import g4f
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import ChannelPrivateError, InvalidBufferError
from telethon.sync import TelegramClient
from telethon.events import NewMessage
from tenacity import retry, stop_after_attempt


def cls_cmd():
    os.system('cls' if os.name == 'nt' else 'clear')

def gd_print(value):
    green_color = '\033[32m'
    reset_color = '\033[0m'
    result = f"\n>{green_color} {value} {reset_color}\n"
    print(result)

def bd_print(value):
    red_color = '\033[31m'
    reset_color = '\033[0m'
    result = f"\n>{red_color} {value} {reset_color}\n"
    print(result)

config = configparser.ConfigParser()
config.read('settings.ini')
cls_cmd()

api_id = config['Telegram'].get('api_id', None)
api_hash = config['Telegram'].get('api_hash', None)
device_model = config['Telegram'].get('device_model', None)
system_version = config['Telegram'].get('system_version', None)
channel_usernames = config['Telegram'].get('channel_usernames', None)
auto_join = config['Telegram'].get('auto_join', None)
PROXY_LOGIN = config['Telegram'].get('PROXY_LOGIN', None) 
PROXY_PASSWORD = config['Telegram'].get('PROXY_PASSWORD', None) 
PROXY_IP = config['Telegram'].get('PROXY_IP', None) 
PROXY_PORT = config['Telegram'].get('PROXY_PORT', None) 
client = TelegramClient('SESSION_FOR_TELEGRAM_COMMENTOR', api_id, api_hash, device_model=device_model, system_version=system_version)


if channel_usernames is not None:
    channels = channel_usernames.split(', ')
    channel_usernames = [channel.strip() for channel in channels if channel]


async def chatgpt_ai(text):
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=[{"role": "user", "content": f"""Сейчас ты играешь роль обычного пользователя в Telegram. 
            Я предоставлю тебе текст поста, на который ты должен будешь отреагировать. Реагируй кратко и эмоционально, как обычный пользователь.
            Вне зависимости от контекста предоставленного тебе текста поста ты должен отреагировать на него. 
            Никогда не говори, кто ты и зачем ты здесь. Никогда не повторяй заголовок поста. Никогда не говори, что ты готов помочь. Не используй смайлики Не используй ХЭШТЕГИ и @. Отвечай, как обычный пользователь. 
            Если ты не знаешь, как реагировать на пост или текст поста пуст или не имеет никакого смысла, то ответь только: '...'. 
            Отвечай только на том языке, который используется в посте. Помни: ты не отвечаешь, а комментируешь. Старайся именно комментировать запись.. 
            Будь саркастичным и остроумным, стеби но не оскорбляй, напиши комментарий строго ДО 15 слов: 
            
            `{text}`
            """}],
            provider=g4f.Provider.Bing,
            temperature=0.9,
            max_tokens=100,
            proxy=f'http://{PROXY_LOGIN}:{PROXY_PASSWORD}@{PROXY_IP}:{PROXY_PORT}'
            
        )
        gd_print(f"Коммент создан")
        return response
    except Exception as e:
        print(e)
        raise e


@retry(stop=stop_after_attempt(5), wait=tenacity.wait_fixed(60))
async def main():
    try:

        name = await client.get_me()
        gd_print(f"Бот запущен ({name.first_name}). Мониторим канал(ы)...")
        try:
            channel_entities = None
            channel_entities = [await client.get_entity(username) for username in channel_usernames]
            commented_messages = {entity.id: set() for entity in channel_entities}
        except Exception as e:
            bd_print(f"Ошибка: {e}")
            if 'No user has' in str(e) and 'as username' in str(e) and channel_entities == None:
                bd_print("Плохо дело. Ни один канал не был найден. Работать негде. Скрипт завершён.")
                exit()

        if auto_join.lower() == "true":
            for username in channel_usernames:
                try:
                    await client(JoinChannelRequest(username))
                    gd_print(f"Присоединились к каналу @{username}")
                except Exception as e:
                    bd_print(f"Не удалось присоединиться к каналу @{username}: {e}")

        
        last_comment_times = {entity.id: 0 for entity in channel_entities}

        # -Обработчик события создания новых постов.
        async def handle_new_posts(event):
            loop = asyncio.get_event_loop()
            start_time = loop.time()
            print("> Создан новый пост. Комментирую...")
            message = event.message
            for entity in channel_entities:
                if entity.id == message.peer_id.channel_id:
                    current_time = loop.time()
                    print(current_time)
                    if current_time - last_comment_times[entity.id] >= 60:
                        last_comment_times[entity.id] = current_time
                        print(last_comment_times[entity.id])
                        if not message.out and message.id not in commented_messages[entity.id]:
                            try:
                                comment_text = await chatgpt_ai(message.text)
                                await client.send_message(entity=entity, message=str(comment_text), comment_to=message)
                                end_time = loop.time()
                                elapsed_time = end_time - start_time
                                gd_print(f"Созданный пост успешно прокомментирован. Затраченное время: {round(elapsed_time, 2)} секунд.")
                                gd_print(f"Comment Link: https://t.me/{entity.username}/{message.id}")
                                commented_messages[entity.id].add(message.id)
                                
                            except ChannelPrivateError as banorprivate:
                                bd_print(f"Ошибка по привату: {banorprivate}")
                            except Exception as e:
                                bd_print(f"Возникла ошибка при комментировании записи: {e}")

        for entity in channel_entities:
            client.add_event_handler(handle_new_posts, event=NewMessage(incoming=True, chats=entity))

        await client.run_until_disconnected()

    except InvalidBufferError as e:
        print(f"InvalidBuffer occured {e}")

if __name__ == "__main__":
    cls_cmd()
    with client:
        client.loop.run_until_complete(main())

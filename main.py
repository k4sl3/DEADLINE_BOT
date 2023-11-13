import requests
import logging
from datetime import datetime, timezone, timedelta
from icalendar import Calendar
from telegram import Update, ParseMode
from telegram.ext import  CommandHandler, CallbackContext, Updater, ConversationHandler , MessageHandler , Filters
import json
from pathlib import Path
import os


TOKEN = os.environ['TG_BOT_TOKEN']
CALENDAR_URL = 'https://moodle.astanait.edu.kz/calendar/export_execute.php?userid=9657&authtoken=5d17755272606beb3223c1fc08809487eee52a91&preset_what=all&preset_time=recentupcoming'
AWAITING_NEWS = 0
website_url = "https://moodle.astanait.edu.kz/login/index.php"
NEWS_FILE = "NEWS_FILE.json"


def save_news_to_file(news):
    with open(NEWS_FILE, 'w') as file:
        json.dump(news, file, default=str)


def load_news_from_file():
    news_data = []
    if Path(NEWS_FILE).is_file():
        with open(NEWS_FILE, 'r') as file:
            try:
                news_data = json.load(file)
            except json.JSONDecodeError:
                print("The file is empty or not a valid JSON.")
    return news_data or []


NEWS_STORAGE = load_news_from_file() or []



class CustomContext(CallbackContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_ids = set()

# Настройте журналирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text='Привет! Напиши "/help", чтобы увидеть команды.')

def parse_categories(description: str) -> str:
    # Извлекаем КАТЕГОРИИ из ОПИСАНИЯ
    start_index = description.find('CATEGORIES:')
    end_index = description.find('\n', start_index) if start_index != -1 else len(description)
    categories = description[start_index + 11:end_index].strip()
    return categories


def deadline(update: Update, context: CallbackContext) -> None:
    try:
        # Загружаем файл календаря
        response = requests.get(CALENDAR_URL)
        response.raise_for_status()

        # Разбираем данные календаря
        calendar = Calendar.from_ical(response.text)

        # Получаем текущую дату и время
        now = datetime.now(timezone.utc)

        # Подготавливаем список для хранения предстоящих дедлайнов
        upcoming_deadlines = []

        # Счетчик для нумерации элементов
        counter = 1

        # Множество для хранения уникальных дедлайнов на основе категории, начальной и конечной даты
        unique_deadlines = set()

        # Итерируемся по событиям в календаре
        for event in calendar.walk('VEVENT'):
            # Извлекаем необходимую информацию из события
            category = event.get('CATEGORIES')
            start_date = event.get('DTSTART').dt
            end_date = event.get('DTEND').dt
            summary = event.get('SUMMARY')

# Проверяем, является ли событие дедлайном и находится ли в будущем
            if category and start_date and end_date and summary:
                # Форматируем категорию
                if isinstance(category, list):
                    decoded_category = category[0].decode('utf-8').strip()
                else:
                    decoded_category = category.to_ical().decode('utf-8').strip()

                formatted_category = decoded_category

                # Форматируем информацию о дедлайне
                formatted_start_date = start_date.strftime('%Y-%m-%d %H:%M:%S')
                formatted_end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')

                if end_date > now:
                    # Проверяем уникальность на основе категории, начальной и конечной даты
                    deadline_key = f"{formatted_category} - {formatted_start_date} - {formatted_end_date}"
                    if deadline_key not in unique_deadlines:
                        unique_deadlines.add(deadline_key)

                        # Рассчитываем оставшееся время
                        time_left = end_date - now

                        # Форматируем оставшееся время
                        days_left = time_left.days
                        hours, remainder = divmod(time_left.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        formatted_time_left = f"{days_left} дней, {hours} часов, {minutes} минут"

                        # Форматируем информацию о дедлайне с нумерацией
                        deadline_info = f"{counter}. 📖{formatted_category} | {formatted_end_date} | 🕓Времени до дедлайна: {formatted_time_left} | 📝{summary}"
                        upcoming_deadlines.append(deadline_info)

                        counter += 1

        # Проверяем, есть ли предстоящие дедлайны
        if upcoming_deadlines:
            # Соединяем дедлайны в отформатированное сообщение
            message = '\n\n'.join(upcoming_deadlines)

            # Отправляем сообщение пользователю
            update.message.reply_text(f"Ближайшие дедлайны  ¯\_(ツ)_/¯ :\n{message}")
        else:
            update.message.reply_text("Дедлайнов нет.")
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ошибка: {str(e)}")

    print(decoded_category)


def final(update: Update, context: CallbackContext) -> None:
    # Path to the photo on the desktop using a raw string
    photo_path = r"C:\Users\makal\Desktop\photo_2023-11-12_10-55-32.jpg"

    # Message to be sent with the photo
    message = "Список файналов 1го тримака 2го курса!"

    # Send photo and message
    update.message.reply_photo(open(photo_path, "rb"), caption=message)


def help_command(update: Update, context: CallbackContext) -> None:

    # Display the list of commands
    help_message = f"Доступные команды :" \
                   f"/deadline" \
                   f" " \
                   f"/check" \
                   f" " \
                   f"/final" \
                   f" " \
                   f"/send_news"
    update.message.reply_text(help_message)

def check_website(update: Update, context: CallbackContext) -> None:
    try:
        # Make an HTTP GET request to the hardcoded URL
        response = requests.get(website_url, timeout=48)  # Set timeout in seconds

        # Check the status code of the response
        if response.status_code == 200:
            update.message.reply_text(f"[Moodle Website] [ ✅ Up] {response.status_code} - OK")
        else:
            update.message.reply_text(f"[Moodle Website] [ 🔴 Down] {response.status_code} - {response.reason}")

    except requests.exceptions.RequestException as e:
        update.message.reply_text(f"[Moodle Website] [ 🔴 Down] {e}")


def send_news(update, context):
    update.message.reply_text("Отправь мне свою новость.")
    return AWAITING_NEWS

def save_news(update, context):
    user = update.message.from_user

    # Check if the message contains media (photo, document, etc.)
    if update.message.photo or update.message.document:
        # Save the file_id of the media for reference
        media_file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
        news_item = {'user_id': user.id, 'media_file_id': media_file_id, 'timestamp': str(datetime.now())}
    else:
        # Extract text from the user's message
        news_text = update.message.text.strip()
        # Save news with timestamp
        news_item = {'user_id': user.id, 'text': news_text, 'timestamp': str(datetime.now())}

    # Load existing news from file
    NEWS_STORAGE = load_news_from_file()

    # Append the new news item
    NEWS_STORAGE.append(news_item)

    # Save the updated news back to the file
    save_news_to_file(NEWS_STORAGE)

    update.message.reply_text("Новость сохранена!")

    return ConversationHandler.END


def get_news(update, context):
    global NEWS_STORAGE
    NEWS_STORAGE = load_news_from_file()

    # Filter news that are not older than 3 days
    recent_news = [
        news for news in NEWS_STORAGE if datetime.now() - datetime.strptime(news.get('timestamp', ''), '%Y-%m-%d %H:%M:%S.%f') <= timedelta(days=3)
    ]

    if recent_news:
        # Prepare and send the recent news to the group
        for news in recent_news:
            user_info = context.bot.get_chat_member(news['user_id'], news['user_id']).user
            user_name = user_info.username if user_info.username else user_info.first_name

            if 'text' in news:
                # If it's a text message, send the text
                context.bot.send_message(chat_id=update.message.chat_id, text=f"{user_name} отправил:\n{news['text']}")
            elif 'media_file_id' in news:
                # If it's a media message, send the media
                context.bot.send_photo(chat_id=update.message.chat_id, photo=news['media_file_id'])
    else:
        update.message.reply_text("Новостей нет")

    print(recent_news)

def cancel(update, context):
    update.message.reply_text("Отменили операцию.")
    return ConversationHandler.END

def main() -> None:
    # Создаем Updater
    updater = Updater(TOKEN)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    custom_context = CustomContext(dispatcher=dp)

    dp.bot_data['context'] = custom_context


    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("deadline", deadline))
    dp.add_handler(CommandHandler("final", final))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("check", check_website))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("send_news", send_news)],
        states={
            AWAITING_NEWS: [MessageHandler(Filters.all & ~Filters.command, save_news)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(conv_handler)

    dp.add_handler(CommandHandler("news", get_news))
    # Запускаем бота
    updater.start_polling()

    # Запускаем бота до получения сигнала остановки
    updater.idle()


if __name__ == '__main__':
    main()
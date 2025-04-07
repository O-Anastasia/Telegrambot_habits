import telebot
import os
from dotenv import load_dotenv
from datetime import datetime, date
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from database_setup import User, db, app
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ForceReply

load_dotenv('.env')
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['help'])
def start(message):
    start_text = '''
    Hello, I'm your bot.
    Here you can set and control your habits
    /start - starts the chatbot
    /add - add your habit
    /list - everyday habits reminder  
    /done - done habits of the day
    /delete - delete habit
    /stat - statistics of habits
    /edit - edit habit
        
    '''

    bot.send_message(message.chat.id, start_text)


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_1 = KeyboardButton('/add')
    button_2 = KeyboardButton('/list')
    keyboard.add(button_1, button_2)

    button_3 = KeyboardButton('/done')
    button_4 = KeyboardButton('/delete')
    keyboard.add(button_3, button_4)

    button_5 = KeyboardButton('/stat')
    button_6 = KeyboardButton('/edit')
    keyboard.add(button_5, button_6)

    bot.send_message(message.chat.id, 'Choose an action:', reply_markup=keyboard)


user_data = {}


@bot.message_handler(commands=['add'])
def add(message):
    telegram_id = message.chat.id

    with app.app_context():
        existing_user = User.query.filter_by(telegram_id=telegram_id).first()

    if existing_user:
        bot.reply_to(message, "You have been already registered ")
    else:
        user_data[telegram_id] = {}
        bot.reply_to(message, "Hello, enter your name :")


@bot.message_handler(func=lambda message: message.chat.id in user_data and 'username' not in user_data[message.chat.id])
def handle_username(message):
    telegram_id = message.chat.id
    user_data[telegram_id]['username'] = message.text
    bot.reply_to(message, 'Enter your first habit, please:')


@bot.message_handler(func=lambda message: message.chat.id in user_data and 'habit_1' not in user_data[message.chat.id])
def handle_habit_1(message):
    telegram_id = message.chat.id
    if message.text == '/skip':
        user_data[telegram_id]['habit_1'] = None
    else:
        user_data[telegram_id]['habit_1'] = message.text
    bot.reply_to(message, 'Enter your second habit, please:')


@bot.message_handler(func=lambda message: message.chat.id in user_data and 'habit_2' not in user_data[message.chat.id])
def handle_habit_2(message):
    telegram_id = message.chat.id
    if message.text == '/skip':
        user_data[telegram_id]['habit_2'] = None
    else:
        user_data[telegram_id]['habit_2'] = message.text
    bot.reply_to(message, 'Enter your third habit, please:')


@bot.message_handler(func=lambda message: message.chat.id in user_data and 'habit_3' not in user_data[message.chat.id])
def handle_habit_3(message):
    telegram_id = message.chat.id
    if message.text == '/skip':
        user_data[telegram_id]['habit_3'] = None
    else:
        user_data[telegram_id]['habit_3'] = message.text

    save_to_db(telegram_id)

    bot.reply_to(message, 'Data has been saved successfully')


def save_to_db(telegram_id):
    user_info = user_data.get(telegram_id)

    if user_info:
        new_user = User(
            telegram_id=str(telegram_id),
            username=user_info.get('username'),
            habit_1=user_info.get('habit_1'),
            habit_2=user_info.get('habit_2'),
            habit_3=user_info.get('habit_3'),
            date_created_1=date.today(),
            date_done_1=date.today(),
            date_created_2=date.today(),
            date_done_2=date.today(),
            date_created_3=date.today(),
            date_done_3=date.today()
        )

        with app.app_context():
            db.session.add(new_user)
            db.session.commit()

        del user_data[telegram_id]


@bot.message_handler(commands=['done'])
def done(message):
    telegram_id = message.chat.id

    with app.app_context():
        existing_user = User.query.filter_by(telegram_id=telegram_id).first()

    if existing_user:
        habits = [existing_user.habit_1, existing_user.habit_2, existing_user.habit_3]
        habits = [habit for habit in habits if habit]

        markup = InlineKeyboardMarkup()
        for habit in habits:
            markup.add(InlineKeyboardButton(text=habit, callback_data=f'done_{habit}'))
        if markup.keyboard:
            bot.send_message(telegram_id, 'Choose a habit, you have done', reply_markup=markup)
        else:
            bot.send_message(telegram_id, 'You have no habits, yet. Please, press "/add" to add habit')


@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def mark_habit_done(call):
    telegram_id = call.message.chat.id
    habit_name = call.data[5:]

    with app.app_context():
        existing_user = User.query.filter_by(telegram_id=telegram_id).first()
        if existing_user:
            habit_mapping = {
                existing_user.habit_1: 'date_done_1',
                existing_user.habit_2: 'date_done_2',
                existing_user.habit_3: 'date_done_3'
            }
        done_field = habit_mapping.get(habit_name)
        if done_field:
            setattr(existing_user, done_field, date.today())
            db.session.commit()
            bot.send_message(telegram_id, f'{habit_name} has been successfully done')
        else:
            bot.send_message(telegram_id, 'There is no such habit, try again')

    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['delete'])
def delete_habit(message):
    telegram_id = message.chat.id
    with app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()

    if user:
        habits = {
            'habit_1': user.habit_1,
            'habit_2': user.habit_2,
            'habit_3': user.habit_3
        }
        habits = {key: value for key, value in habits.items() if value}

        if habits:
            markup = InlineKeyboardMarkup()
            for field, habit in habits.items():
                markup.add(InlineKeyboardButton(text=habit, callback_data=f'delete_{field}'))

            bot.send_message(telegram_id, 'Choose a habit, you want to delete', reply_markup=markup)
        else:
            bot.send_message(telegram_id, 'You have no habits')


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_habit_done(call):
    telegram_id = call.message.chat.id
    habit_field = call.data[7:]
    with app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if user:
            setattr(user, habit_field, None)
            setattr(user, habit_field.replace('habit', 'date_created'), None)
            setattr(user, habit_field.replace('habit', 'date_done'), None)
            db.session.commit()
            bot.answer_callback_query(call.id)
            bot.send_message(telegram_id, 'Your habit has been deleted')
        else:
            bot.answer_callback_query(call.id)
            bot.send_message(telegram_id, 'There is no such user')


@bot.message_handler(commands=['edit'])
def edit_habit(message):
    telegram_id = message.chat.id

    with app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()

    if user:
        empty_fields = [field for field in ['habit_1', 'habit_2', 'habit_3'] if not getattr(user, field)]

        if empty_fields:
            bot.send_message(telegram_id, "Enter new habit", reply_markup=ForceReply())
            bot.register_next_step_handler(message, save_new_habit, user, empty_fields[0])
        else:
            bot.send_message(telegram_id,
                             "You have already 3 habits. If you want to change your habit, delete the previous one, using /delete ")
    else:
        bot.send_message(telegram_id, "You haven't been registered yet. Press /add for registration")


def save_new_habit(message, user, field):
    new_habit = message.text.strip()

    with app.app_context():
        user = User.query.filter_by(telegram_id=user.telegram_id).first()

        if user:
            setattr(user, field, new_habit)
            setattr(user, field.replace('habit', 'date_created'), date.today())
            db.session.commit()
            bot.send_message(user.telegram_id, f'Habit {new_habit}  has been saved')
        else:
            bot.send_message(user.telegram_id, "Error. User haven't been found")


if __name__ == '__main__':
    bot.polling()

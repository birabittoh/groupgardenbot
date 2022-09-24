import os, logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CallbackContext, CallbackQueryHandler, CommandHandler, PicklePersistence
from Gardening import Plant, get_plant_info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
load_dotenv()

def reply(update: Update, context: CallbackContext, text: str = "", markup: str = ""):
    return context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup, parse_mode='Markdown')

def edit(update: Update, context: CallbackContext, text: str = "", markup: str = ""):
    context.bot.editMessageText(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')

def get_plant(context: CallbackContext, user_id: int):
        try:
            plant = context.bot_data[user_id]["plant"]
        except KeyError:
            return None
        
        plant.update()
        return plant

def get_plant_markup(user_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Innaffia 🚰", callback_data=f"water {user_id}"),
            InlineKeyboardButton(text="Aggiorna 🌱", callback_data=f"show {user_id}"),
        ]
    ])

def start_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    plant = get_plant(context, user_id)
    new = False
    
    if plant is None:
        plant = Plant(user_id)
        context.bot_data[update.effective_user.id] = { "plant" : plant }
        new = True

    if plant.dead or plant.stage == 5:
        plant.start_over()
        new = True
    
    if new:
        show_handler(update, context)
        return reply(update, context, "Hai piantato un nuovo seme! Adesso usa /water per innaffiarlo.")
    
    return reply(update, context, "La tua pianta non è ancora pronta per andarsene!")

def water(context: CallbackContext, user_id: int):
    plant = get_plant(context, user_id)
    
    if plant is None:
        return "Non hai niente da innaffiare! Usa /start per piantare un seme."

    if plant.dead:
        return "La pianta è morta..."
    
    plant.water()
    return "Pianta innaffiata."

def show(context: CallbackContext, user_id: int):
    plant = get_plant(context, user_id)
    
    if plant is None:
        return "Non hai nessuna pianta da mostrare! Usa /start per piantarne una.", ""
    
    text = get_plant_info(plant)
    markup = get_plant_markup(user_id)
    return text, markup

def rename(context: CallbackContext, user_id: int):
    plant = get_plant(context, user_id)
    
    if plant is None:
        return "Non hai ancora piantato niente! Usa /start per piantare un seme."
    try:
        new_name = " ".join(context.args).strip()
        if new_name == "":
            raise IndexError
    except IndexError:
        return "Utilizzo: /rename <nuovo nome>"
    
    plant.name = new_name
    return f"Fatto! Adesso la tua pianta si chiama {new_name}!"

def water_handler(update: Update, context: CallbackContext):
    answer = water(context, update.effective_user.id)
    return reply(update, context, answer)

def show_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    answer, markup = show(context, user_id)
    reply(update, context, answer, markup)
    
def rename_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    answer = rename(context, user_id)
    reply(update, context, answer)

def keyboard_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = None
    
    if data.startswith("water"):
        user_id = int(data.split(" ")[1])
        answer = water(context, user_id)
        query.answer(answer)
    
    if data.startswith("show"):
        user_id = int(data.split(" ")[1])
        query.answer()
    
    if user_id is not None:
        text, markup = show(context, user_id)
        return edit(update, context, text, markup)
        
    return query.answer("Questo tasto non fa nulla.")

if __name__ == "__main__":
    updater = Updater(token=os.getenv("token"),
                      persistence=PicklePersistence(filename='bot-data.pkl',
                                                    store_user_data=False,
                                                    store_bot_data=True,
                                                    store_callback_data=False,
                                                    store_chat_data=False
                                                    ))
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start_handler))
    dispatcher.add_handler(CommandHandler('water', water_handler))
    dispatcher.add_handler(CommandHandler('show', show_handler))
    dispatcher.add_handler(CommandHandler('rename', rename_handler))
    dispatcher.add_handler(CallbackQueryHandler(callback=keyboard_handler))
    
    updater.start_polling()
    print(updater.bot.name, "is up and running!")
    updater.idle()

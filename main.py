import os, logging, time
from dotenv import load_dotenv
from telegram import Update, User, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import PersistenceInput, ApplicationBuilder, CallbackContext, CallbackQueryHandler, CommandHandler, PicklePersistence
from Gardening import Plant
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
load_dotenv()

async def reply(update: Update, context: CallbackContext, text: str = "", markup: str = ""):
    return await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup, parse_mode='Markdown')

async def edit(update: Update, context: CallbackContext, text: str = "", markup: str = ""):
    return await context.bot.editMessageText(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')

def get_plant_info(plant: Plant):
    return f'''
```{plant.get_art()}
owner : {plant.owner_name}
name  : {plant.name}
stage : {plant.parse_plant()}
age   : {plant.age_days} days
score : {plant.points}
bonus : x{plant.generation_bonus - 1:.2f}
water : {plant.get_water()}```

{plant.get_description()}
{f'Last watered by {plant.last_water_name}.' if plant.last_water_user != plant.owner else ""}
'''

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

async def start_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    plant = get_plant(context, user_id)
    new = False
    
    if plant is None:
        plant = Plant(update.effective_user)
        context.bot_data[user_id] = { "plant" : plant }
        new = True

    if plant.dead or plant.stage == 5:
        plant.start_over(update.effective_user)
        new = True
    
    if new:
        show_handler(update, context)
        return await reply(update, context, "Hai piantato un nuovo seme! Adesso usa /water o un tasto sopra per innaffiarlo.")
    
    return await reply(update, context, "La tua pianta non è ancora pronta per andarsene!")

def water(context: CallbackContext, user_id: int, who: User):
    plant = get_plant(context, user_id)
    
    if plant is None:
        return "Non hai niente da innaffiare! Usa /start per piantare un seme."

    if plant.dead:
        return "La pianta è morta..."

    plant.water(who)
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
        return "Utilizzo: /rename nuovo nome"
    
    plant.name = new_name
    return f"Fatto! Adesso la tua pianta si chiama {new_name}!"

async def water_handler(update: Update, context: CallbackContext):
    answer = water(context, update.effective_user.id, update.effective_user)
    return await reply(update, context, answer)

async def show_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    answer, markup = show(context, user_id)
    return await reply(update, context, answer, markup)
    
async def rename_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    answer = rename(context, user_id)
    return await reply(update, context, answer)

async def keyboard_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = None
    
    if data.startswith("water"):
        user_id = int(data.split(" ")[1])
        answer = water(context, user_id, update.effective_user)
        await query.answer(answer)
    
    if data.startswith("show"):
        user_id = int(data.split(" ")[1])
        await query.answer()
    
    if user_id is not None:
        text, markup = show(context, user_id)
        return await edit(update, context, text, markup)
        
    return await query.answer("Questo tasto non fa nulla.")

if __name__ == "__main__":
    pers = PersistenceInput(bot_data=True, user_data=False, callback_data=False, chat_data=False)
    
    application = ApplicationBuilder()
    application.token(os.getenv("token"))
    application.persistence(PicklePersistence(filepath='bot-data.pkl', store_data=pers))
    application = application.build()
    
    application.add_handler(CallbackQueryHandler(callback=keyboard_handler))
    
    
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('water', water_handler))
    application.add_handler(CommandHandler('show', show_handler))
    application.add_handler(CommandHandler('rename', rename_handler))
    
    #print(application.bot.name, "is up and running!")
    application.run_polling()

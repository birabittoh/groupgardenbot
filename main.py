import os, logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, User, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import PersistenceInput, ApplicationBuilder, CallbackContext, CallbackQueryHandler, CommandHandler, PicklePersistence
from telegram.error import BadRequest
from Gardening import Plant
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

data_dir = 'data'

async def reply(update: Update, context: CallbackContext, text: str = "", markup: str = ""):
    return await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup, parse_mode='Markdown')

async def edit(update: Update, context: CallbackContext, text: str = "", markup: str = ""):
    try:
        return await context.bot.editMessageText(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')
    except BadRequest:
        logger.warning("Message contents were unchanged.")

def get_plant_info(plant: Plant):
    status = f'''
```{plant.get_art()}
owner : {plant.owner_name}
name  : {plant.name}
stage : {plant.parse_plant()}
age   : {plant.age_days} days
score : {plant.points}
bonus : x{plant.generation_bonus - 1:.2f}
last  : {datetime.fromtimestamp(plant.last_water).strftime("%d/%m/%Y %H:%M:%S")}
water : {plant.get_water()}
```

{plant.get_description()}
'''
    if plant.last_water_user != plant.owner:
        status += f'Last watered by {plant.last_water_name}.'
    return  status

def get_plant(context: CallbackContext, user_id: int):
        try:
            plant = context.bot_data[user_id]["plant"]
        except KeyError:
            return None
        
        plant.update()
        return plant

def get_plant_markup(user_id: int, plant):

    buttons = []
    if not plant.dead:
        buttons += [
            [
                InlineKeyboardButton(text="Innaffia 🚰", callback_data=f"water {user_id}"),
                InlineKeyboardButton(text="Aggiorna 🌱", callback_data=f"show {user_id}"),
            ]
        ]
    
    if plant.dead or plant.stage == 5:
        buttons += [ [ InlineKeyboardButton(text="Ricomincia 🌰", callback_data=f"start {user_id}") ] ]

    return InlineKeyboardMarkup(buttons)

def new_plant(context: CallbackContext, who: User):
    plant = Plant(who)
    context.bot_data[who.id] = { "plant": plant }
    return plant

def start(context: CallbackContext, user_id: int, who: User):

    plant = get_plant(context, user_id)
    new_text = "Hai piantato un nuovo seme!"

    if plant is not None:
        if not (plant.dead or plant.stage == 5):
            return "La tua pianta non è ancora pronta per andarsene!", False

        plant.start_over(who)
        return new_text, True

    new_plant(context, who)
    return new_text, True
        
async def start_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    plant = get_plant(context, user_id)

    response, new = start(context, update.effective_user.id, update.effective_user)

    await reply(update, context, response)

    if new:
        text, markup = show(context, user_id)
        await reply(update, context, text, markup)

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
    markup = get_plant_markup(user_id, plant)
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

    if data.startswith("start"):
        user_id = int(data.split(" ")[1])
        if user_id != update.effective_user.id:
            return await query.answer("Non puoi usare questo comando.")
        text, _ = show(context, user_id)
        await edit(update, context, text, None)
        answer = start(context, user_id, update.effective_user)
        await query.answer(answer)
        text, markup = show(context, user_id)
        return await reply(update, context, text, markup)
    
    if data.startswith("water"):
        user_id = int(data.split(" ")[1])
        answer = water(context, user_id, update.effective_user)
        await query.answer(answer)
        text, markup = show(context, user_id)
        return await edit(update, context, text, markup)
    
    if data.startswith("show"):
        user_id = int(data.split(" ")[1])
        await query.answer()
        text, markup = show(context, user_id)
        return await edit(update, context, text, markup)
        
    return await query.answer("Questo tasto non fa nulla.")

async def kill_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    plant = get_plant(context, user_id)
    plant.dead = True
    return await reply(update, context, "💀💀💀", "")

async def bloom_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    plant = get_plant(context, user_id)
    plant.points = 9999999
    plant.dead = False
    return await reply(update, context, "🌸🌸🌸", "")

if __name__ == "__main__":
    pers = PersistenceInput(bot_data=True, user_data=False, callback_data=False, chat_data=False)
    
    application = ApplicationBuilder()
    application.token(os.getenv("token"))
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    application.persistence(PicklePersistence(filepath=os.path.join(data_dir, 'bot-data.pkl'), store_data=pers))
    application = application.build()
    
    application.add_handler(CallbackQueryHandler(callback=keyboard_handler))
    
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('water', water_handler))
    application.add_handler(CommandHandler('show', show_handler))
    application.add_handler(CommandHandler('rename', rename_handler))

    if os.getenv("cheats") == "True":
        application.add_handler(CommandHandler('kill', kill_handler))
        application.add_handler(CommandHandler('bloom', bloom_handler))
    
    #print(application.bot.name, "is up and running!")
    application.run_polling()

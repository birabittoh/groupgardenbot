import os, logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
from telegram import Update
from telegram.ext import Updater, CallbackContext, CallbackQueryHandler, CommandHandler, MessageHandler, PicklePersistence
from dotenv import load_dotenv
load_dotenv()
from Gardening import Plant, get_plant_info

def reply(update: Update, context: CallbackContext, text: str = "", markup: str = ""):
    return context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup, parse_mode='Markdown')

def get_plant(update: Update, context: CallbackContext):
        try:
            plant = context.bot_data[update.effective_user.id]["plant"]
        except KeyError:
            return None
        
        if plant is None: # probably useless but heh
            print("############### This wasn't so useless after all! ###############")
            return None
        
        plant.update()
        return plant

def start(update: Update, context: CallbackContext):
    plant = get_plant(update, context)
    new = False
    
    if plant is None:
        context.bot_data[update.effective_user.id] = { "plant" : Plant(update.effective_user.id) }
        new = True

    if plant.dead or plant.stage == 5:
        plant.start_over()
        new = True
    
    if new:
        return reply(update, context, "Hai piantato un nuovo seme! Adesso usa /water per innaffiarlo.")
    
    return reply(update, context, "La tua pianta non è ancora pronta per andarsene!")

def water(update: Update, context: CallbackContext):
    plant = get_plant(update, context)
    
    if plant is None:
        return reply(update, context, "Non hai nessuna pianta da innaffiare! Usa /start per piantarne una.")

    if plant.dead:
        return reply(update, context, "La tua pianta è morta... Usa /harvest per piantarne un'altra.")
    
    plant.water()
    return reply(update, context, "Pianta innaffiata.")

def show(update: Update, context: CallbackContext):
    plant = get_plant(update, context)
    
    if plant is None:
        return reply(update, context, "Non hai nessuna pianta da mostrare! Usa /start per piantarne una.")

    return reply(update, context, get_plant_info(plant))


'''
def keyboard_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    
    if data.startswith("reroll"):
        amount = int(data.split(" ")[1])
        
        if amount <= 1:
            return spin(update, context)
        return autospin(context, update.effective_chat.id, amount)
    
    match data:
        case "none":
            return query.answer("This button doesn't do anything.", context))
        case other:
            logging.error(f"unknown callback: {data}")
    
    return query.answer()

def unknown(update: Update, context: CallbackContext):
    logging.info(f"User {update.message.from_user.full_name} sent {update.message.text_markdown_v2} and I don't know what that means.")
'''
def main():
    
    updater = Updater(token=os.getenv("token"),
                      persistence=PicklePersistence(filename='bot-data.pkl',
                                                    store_user_data=False,
                                                    store_bot_data=True,
                                                    store_callback_data=False,
                                                    store_chat_data=False
                                                    ))
    
    dispatcher = updater.dispatcher
    
    
    # commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('water', water))
    dispatcher.add_handler(CommandHandler('show', show))
    
    '''
    # slot
    dispatcher.add_handler(CommandHandler('spin', spin))
    dispatcher.add_handler(CommandHandler('bet', bet))
    dispatcher.add_handler(CommandHandler('cash', cash))
    '''
    
    '''
    dispatcher.add_handler(CallbackQueryHandler(callback=keyboard_handler))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    '''
    
    updater.start_polling()
    print(os.getenv("bot_name"))
    updater.idle()

if __name__ == "__main__":
    main()

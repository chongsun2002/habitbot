from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from .db.db import Database
from datetime import datetime, timezone, timedelta
import logging

class OnboardingStates:
    START, WHAT, WHERE, WHEN, CATEGORY, CONSENT = range(6)

    pre_state_messages = {
        0: "",
        1: "What habit would you like to build?",
        2: "Where do you want to build this habit?",
        3: "When would you like to build this habit?",
        4: "Which habit category is your habit under?",
        5: "Do we have permission to anonymously share your reflections with others?",
    }

    end_message = "Your onboarding data has been successfully captured! Lets work towards greatness together :)"
    already_onboarded_message = "Your onboarding has already been captured! If you would like to edit your habit, use the /edit_habit command!"
    categories = ["Flexibility", "Strength", "Cardio", "Diet"]
    consent = ["I'm down to share!", "I'd rather just reflect myself."]
    invalid_category_message = "Sorry, the category you chose is not a valid option, please choose again!"
    invalid_consent_message = "Sorry, we didn't quite get that, could you please try clicking the buttons again?"


def call_onboard_function(user_data: dict):
    now_utc5 = datetime.now(timezone(timedelta(hours=5)))
    # Subtract one day to get yesterday
    yesterday = now_utc5 - timedelta(days=1)
    # Reset the time to midnight (00:00:00)
    last_done_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    # Convert to string format "YYYY-MM-DD"
    last_done_date_str = last_done_date.strftime("%Y-%m-%d")
    streak = "0"
    initial_points = 0
    Database.get_instance().add_new_user(
        (user_data["telegram"].id,
         user_data["telegram"].username,
         user_data["habit"],
         user_data["location"],
         user_data["time_period"],
         user_data["reflection_consent"],
         last_done_date_str,
         streak,
         initial_points,
         user_data["category"]
        )
    )   

# Should check if user is in the existing db
async def onboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    context.user_data["telegram"] = user
    if Database.get_instance().is_user_registered(user.id):
        await update.message.reply_text(OnboardingStates.already_onboarded_message)
        return ConversationHandler.END
    next_state = OnboardingStates.WHAT
    await update.message.reply_text(OnboardingStates.pre_state_messages[next_state])
    return next_state

async def what_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    context.user_data["habit"] = text
    next_state = OnboardingStates.WHERE
    await update.message.reply_text(OnboardingStates.pre_state_messages[next_state])
    return next_state

async def where_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    context.user_data["location"] = text
    next_state = OnboardingStates.WHEN
    await update.message.reply_text(OnboardingStates.pre_state_messages[next_state])
    return next_state

async def when_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    context.user_data["time_period"] = text
    next_state = OnboardingStates.CATEGORY
    reply_keyboard = [OnboardingStates.categories]
    await update.message.reply_text(
        OnboardingStates.pre_state_messages[next_state],
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder=OnboardingStates.pre_state_messages[next_state]
        )
    )
    return next_state

async def category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    # In case the buttons were not rendered properly and invalid category was input
    if text not in OnboardingStates.categories:
        reply_keyboard = [OnboardingStates.categories]
        await update.message.reply_text(
            OnboardingStates.invalid_category_message,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                input_field_placeholder=OnboardingStates.pre_state_messages[next_state]
            )
        )
        return OnboardingStates.CATEGORY
    context.user_data["category"] = text
    next_state = OnboardingStates.CONSENT
    reply_keyboard = [OnboardingStates.consent]
    await update.message.reply_text(
        OnboardingStates.pre_state_messages[next_state],
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder=OnboardingStates.pre_state_messages[next_state]
        )
    )
    return next_state
    
async def consent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    if text not in OnboardingStates.consent:
        reply_keyboard = [["I'm down to share!", "I'd rather just reflect myself."]]
        await update.message.reply_text(
            OnboardingStates.invalid_consent_message,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                input_field_placeholder=OnboardingStates.pre_state_messages[OnboardingStates.CONSENT]
            )
        )
    if text == "I'm down to share!":
        context.user_data["reflection_consent"] = 1
    else:
        context.user_data["reflection_consent"] = 0
    call_onboard_function(context.user_data)
    await update.message.reply_text(OnboardingStates.end_message)
    return ConversationHandler.END

onboarding_handler = ConversationHandler(
    entry_points=[CommandHandler("onboard", onboard_command)],
    states={
        OnboardingStates.WHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, what_command)],
        OnboardingStates.WHERE: [MessageHandler(filters.TEXT & ~filters.COMMAND, where_command)],
        OnboardingStates.WHEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, when_command)],
        OnboardingStates.CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_command)],
        OnboardingStates.CONSENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, consent_command)],
    },
    fallbacks=[],
)

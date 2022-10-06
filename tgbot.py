#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os
import sys
import plistlib as pl

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO, stream=sys.stdout
)
logger = logging.getLogger(__name__)

SPOTIFY_AUTH, APPLE_LIBRARY = range(2)


def parse_library(filename):
    with open(filename, 'rb') as fp:
        a_music = pl.load(fp)
    logger.info('Tracks Count: ' + str(len(a_music['Tracks'])))

    return a_music


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""

    await update.message.reply_text(
        "Hi! Send me an Apple Music Library File!\n\n"
        "Send /cancel to stop talking to me."
    )

    return APPLE_LIBRARY


async def test_library(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for a location."""
    user = update.message.from_user
    plist_file = await update.message.document.get_file()
    file_name = "in/" + str(user.id) + ".xml"
    await plist_file.download(file_name)
    logger.info("File of %s: %s", user.first_name, file_name)
    a_music = parse_library(file_name)
    tracks_count = len(a_music['Tracks'])
    await update.message.reply_text(
        "Saved the file!\n" +
        "Found " + str(tracks_count) + " tracks!\n" +
        "END"
    )

    return ConversationHandler.END


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for a location."""
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    await update.message.reply_text(
        "Ok, skipped the file."
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Ok, canceled.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    bot_token = os.getenv('BOT_TOKEN')
    application = Application.builder().token(bot_token).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            APPLE_LIBRARY: [MessageHandler(filters.Document.FileExtension("xml"), test_library), CommandHandler("skip", skip_photo)],
            SPOTIFY_AUTH: [MessageHandler()]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

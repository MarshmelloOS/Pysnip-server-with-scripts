import pyspades.constants
from translate import Translator

# Initialize the translator
translator = Translator(to_lang='en')  # Default translation language is English

# Define the translation command
def translate_command(connection, command, arguments):
    # Check if the player provided a sentence to translate
    if len(arguments) < 2:
        connection.send_chat("Usage: /translate <target_language> <sentence>")
        return
    
    target_language = arguments[0].lower()
    sentence = ' '.join(arguments[1:])

    # Translate the sentence
    translated_sentence = translator.translate(sentence, to_lang=target_language)

    # Send the translated sentence to the player
    connection.send_chat("Translated: {}".format(translated_sentence))

# Register the translation command
pyspades.constants.DEFAULT_COMMANDS.append('translate')

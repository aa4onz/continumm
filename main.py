from variables import bot, tok
import prefix, slash, events

prefix.register()
slash.register()
events.register()

if __name__ == '__main__':
    bot.run(tok
           )

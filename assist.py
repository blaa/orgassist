#!/usr/bin/env python3

import schedule
import orgassist
import logging
from time import sleep

def configure_logging():
    "Configure logging"
    logging.basicConfig(level=logging.INFO)

def main_loop(assitants, scheduler):
    "Main loop - execute scheduled tasks"
    while True:
        print("Looping")
        sleep(5)
        scheduler.run_pending()

def main():
    "Initialize environment"
    configure_logging()

    cfg = orgassist.Config('config.yml')

    # Scheduler
    scheduler = schedule.Scheduler()

    # XMPP Bot / interface
    xmpp_bot = orgassist.XmppBot(cfg.xmpp)

    # Create instances of assistants
    assistants = []
    for instance_name, instance_config in cfg.instances.items():

        # Construct a configuration based on defaults
        opts = cfg.defaults.copy()
        opts_overrides = instance_config.get('opts', {})
        opts.update(opts_overrides)
        instance_config['opts'] = opts

        s = orgassist.Assistant(instance_name, instance_config, scheduler)
        s.register_xmpp_bot(xmpp_bot)
        # FUTURE: s.register_irc_bot(irc)
        assistants.append(s)

    # Start processing in other threads
    xmpp_bot.client.process()

    try:
        main_loop(assistants, scheduler)
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        xmpp_bot.client.abort()


if __name__ == "__main__":
    main()

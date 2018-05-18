What is it?
===========

TODO: README needs polishing up. App is in early development, but became usable
recently so I decided to backup it to github. Give it sometime - unless you
want to develop it yourself.

"orgassist" is a bot - an assistant who handles your appointments, tasks and
note-taking when you're away from your computer. It can integrate multiple
sources of notifications and use multiple different communication interfaces -
by default XMPP.

It's architected to be easily expandable, but by design handles:
- org-mode directory structure with deadlines, scheduled tasks and agendas.
- XMPP interface to read commands and send notifications.
- FUTURE: other bot-interfaces: irc interface, email interface, web interface, android push-notification interface.
- FUTURE: taking notes directly into the inbox file inside the org tree.
- FUTURE: Outlook (OWA) calendar integration to get integrated notification stream.


But why?
===========

* Do you love your org-mode, but still struggle to get the agenda or
  notifications on your two mobile devices?
* You have two org-mode trees - one for work, one for private planning? 
* And appointments in Outlook or Google Calendar?
* And sticky notes or notepad to gather notes on the run?
* Or maybe a mobile app to gather notes (orgzly?)
* Taking notes on the run requires you to later integrate them? 
* You treat your org-mode as private notes and dislike keeping them decrypted
  everywhere, but at the same time would like to use it remotely?

I had most of those problems and decided this would be an elegant way to solve
all of them without dropping org-mode or using cloud-sync solutions.


Plugins
===========
OrgAssist is split into plugins with a well-defined API.

Calendar 
-----------
Code originally developed in the org plugin, but extracted to allow sharing it's
functions between all plugins. In general, it handles a list of org-like
"events" - dated (or not) tasks in various states (TODO, DONE, DELEGATED, etc.)

Can generate notifications for the incoming events and whole-day agendas to
remind you what you've planned for today.

It's considered a Core plugin as its existence is a depedency of other plugins.

Org
-----------
Reads org files and feeds events into the calendar. FUTURE: Allows you to change
state of tasks, take a note into an org file, etc.

OWA
-----------
FUTURE: Planned plugin to integrate events from a corporate OWA calendar. 

Shell
-----------
FUTURE: Execute a configured command when given a command. Enable/disable
alarms, control music, etc.


Setup
===========
1. FUTURE: pip3 install orgassist
2. Copy config.tmpl.yaml to ~/.org/assist.yml
3. $ orgassist --config [path to the config file]


License
=======
MIT License

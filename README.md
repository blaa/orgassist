What is it?
===========

TODO: README needs polishing up. App is in early development, but became usable
recently so I decided to backup it to github. Give it sometime - unless you
want to develop it yourself.

"orgassist" is a bot - an assistant who handles your appointments, tasks and
note-taking when you're away from your computer. It can integrate multiple
sources of notifications.

It's architected to be easily expandable, but by design handles:
- org-mode directory structure with deadlines, scheduled tasks and agendas.
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

Setup
===========
1. FUTURE: pip3 install orgassist
2. Copy config.tmpl.yaml to ~/.org/assist.yml
3. $ orgassist --config [path to the config file]

License
=======

MIT License

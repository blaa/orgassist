"""
org-mode compatible, agenda-focused calendar.
"""

from orgassist import log
from orgassist.assistant import Assistant, AssistantPlugin

@Assistant.plugin('calendar')
class CalendarCore(AssistantPlugin):

    def initialize(self):
        # How often to check calendar and plan notifications?
        # If someone cancels an event after notification was scheduled
        # the notification will happen anyway.
        scan_interval = 120

        self.scheduler.every(scan_interval).seconds.do(self.schedule_notifications)


    def schedule_notifications(self):
        "Schedule incoming notifications"
        log.info('Would schedule notifications!')

    def register(self):
        commands = [
            (['agenda', 'ag'], self.handle_agenda),
        ]
        for aliases, callback in commands:
            self.assistant.register_command(aliases, callback)

    def format_agenda(self):
        "Format agenda"
        incoming = self.state['db']['incoming']
        incoming.sort()
        today = dt.datetime.today()

        for event in incoming:
            closest_converted_date, data = incoming
            todo = data['entry'].todo or 'TASK'

            # TODO: This is a hack as those without hours get 23:59:59
            accurate = data['converted_date'] == data['date']

            s = "%s %9s %-20s %s"
            s = s % (marker, todo, _get_delta(data['delta'], accurate),
                     data['entry'].headline[:60])


    def handle_agenda(self, message):
        "Respond with an agenda on agenda command"
        message.respond('That is an agenda!')
        message.respond('It works!')

        self.state['db']



class DefaultSMSMessage(object):

    def __init__(self, notification):
        self.to = notification.target_user
        self.subject = self.kwargs.get('subject')
        self.body = ''

    def create_message(self):
        """
        """
        self.body = ""

    def send(self):
        pass

    def check_validity(self):
        return True

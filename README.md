# transmissions

[![Build Status](https://travis-ci.org/makingspace/transmissions.svg?branch=master)](https://travis-ci.org/makingspace/transmissions) [![Coverage Status](https://coveralls.io/repos/makingspace/transmissions/badge.svg?branch=master)](https://coveralls.io/r/makingspace/transmissions?branch=master)

Transmissions is a Django application that channels all user notifications via email, sms, push notifcations, etc.

## Requirements

For now, Transmissions only works with Django 1.7 or later (due to the database migration schema). There is no reason for us not to make it Django-free, but unless requested, we will probably not work on it right away.

Celery and its scheduler celery beat are also a requirement (and an inspiration) for transmissions. It is probably the best way to queue up notitications to be sent and to schedule for them to continuously be checked.

Finally, we require 3 packages that made developing Transmissions easier. We will re-evaluate them soon since the code needed is not very complex. 

 * `django_extensions`
 * `django_enumfield`
 * `shortuuid`.

***The package is tested for Python 2.7, 3.3 and 3.4.***


## Installation

1. Install the application

  ```bash
  pip install transmissions
  ```

2. Add transmissions to your Django settings

  ```python
  INSTALLED_APPS += ("transmissions", )
  ````
  
3. Add the transmissions processing task to your celerybeat schedule

  ```python
  CELERYBEAT_SCHEDULE['minutely_process_all_notifications'] = {
    'task': 'transmissions.tasks.process_all_notifications',
    'schedule': crontab(minute='*')
  }
  ````

4. Run the migrations for the [Notification](blob/master/transmissions/models.py) model

  ```bash
  python manage.py migrate
  ```
  
## Using Transmissions for new messages  

1. Define a new message

  ```python
  from transmissions import message
  from transmissions.channels.email import DefaultEmailMessage
  
  @message('hello-world-message', behavior=None, subject='Hello world!')
  class MyEmailMessage(DefaultEmailMessage):
  
    def send(self):
      self.body = 'Hey, let me type a message later'
      super(MyEmailMessage, self).send()
  ```

2. Trigger a notification in your code

  ```python
  from my.code.base import MyEmailMessage
  
  def confirmation_page(request):
  
    MyEmailMessage.trigger(request.user)
    
    return HttpResponse('42')
  ```

## Documentation

### Notifications model

The [Notification](blob/master/transmissions/models.py) model is a lightweight way to store scheduled and sent notifications. When sending messages, your application will not interacte with it directly, however, it is useful to list past notifications for your users:

#### Fields

| Field              | Type              | Required | Description                                                       |
|--------------------|-------------------|:--------:|-------------------------------------------------------------------|
| uuid               | ShortUUID         |          | Unique ID                                                         |
| trigger_name       | String            |    yes   | Message slug name                                                 |
| target_user        | ForeignKey        |    yes   | User who should receive the notification                          |
| trigger_user       | ForeignKey        |          | User who sent/triggered the notification if any                   |
| content            | GenericForeignKey |          | Related Django object                                             |
| data               | Pickled object    |          | Additional data for the message. We recommend avoiding this field |
| datetime_created   | datetime          |   auto   | Date of creation                                                  |
| datetime_scheduled | datetime          |   auto   | Scheduled date to send the notification                           |
| datetime_processed | datetime          |   auto   | Date the notification was processed (sent or failed)              |
| datetime_seen      | datetime          |          | Date the notification was seen. Must be set by API                |
| datetime_consumed  | datetime          |          | Date the notification was acted upon. Must be set by API          |
| status             | enum              |   auto   | CREATED, SUCCESSFULLY_SENT, FAILED, CANCELLED or BROKEN           |

#### Datetime fields

When a message is triggered, the `datetime_created` and `datetime_scheduled` will be set. Then, when the schedule time is met, the notification will be processed and `datetime_processed` will be udpated together with the `status`. 

It is up to your application to manage `datetime_seen`, which may be useful to maintain a notification badge on an application or website; and `datetime_consumed` which can be useful to highlight notification that have been seen but not acted upon (ex. `trigger_user.name` sent commented on your photo). In this case, `content` could be a photo, or the comment, and your app could set  `datetime_consumed` to `now()` as soon as the user loads the page or view with the comment.

#### List notifications

Here is an example of how to list past notifications for a user:

```python
def my_page(request):
 notications = request.user.notifications.exclude(datetime_processed=None).order_by('datetime_scheduled)
 ...
```


### Channels

Channels are meant to be connected to 3rd party code. `DefaultSMSMessage` and `DefaultEmailMessage` are actually not very useful at the moment. Writting your custom channel is still recommended until we add more channels.

#### APIs

* `__init__(notification)`

  All channels will be instantiated with a notification when being processed. The notification model comes with a Django User from which the email address, phone number, device id and other details should be available

* `check_validity()`

  Before sending a message, Transmissions will call this method to check if the notification is still valid. A common case is for a notification to be triggered in the future, and for the the conditions to send it not to be valid forever. For example, `check_validity()` of an Unpaid Invoice notification triggered when then invoice is created for 30 days later could check if the invoice has been paid. This method should return a boolean.

* `send()`

  This is how the method sends the message, however the channel itself should work. In case of error while sending, a `ChannelSendException`should be raised to avoid sending multiple times the same notifications
  
#### Example

  ```python
  from django.conf import settings
  from twilio.rest import TwilioRestClient
  
  class BaseTwilioSMS(object):
    """
    This class defines the base SMS model that uses twilio
    """
    from_phone = settings.TWILIO_SMS_NUMBER
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN

    def __init__(self, notification):
        self.target_user = notification.target_user
        self.to = notification.target_user.phone
        self.client = TwilioRestClient(self.account_sid, self.auth_token)

    def check_validity(self):
        # if phone number is not None, it's a valid sms
        return self.to

    def create_message(self):
        raise NotImplementedError()
        
    def send(self):
        try:
            # call twilio client for sending the message
            res = self.client.messages.create(body=self.create_message(),
                                              to=self.to,
                                              from_=self.from_phone)
            if not res:
                raise ChannelSendException()
            return res
        except Exception as e:
            raise ChannelSendException("There was an error in sending sms to {}, error: {}".format(self.to, e.args))
  ```

### Messages

Messages are defined in the code base. Inspired from celery tasks, they are meant to be the variable piece of Transmissions that lives in your code.

#### Trigger Behavior

To keep the abstraction level in your code, you **only** want to query for Notifications when listing them. This is why we added behaviors:

* DEFAULT – A new notification is created each time the message is triggered
* DELETE_AFTER_PROCESSING – The notification will be deleted once it's processed successfully
* TRIGGER_ONCE – The notification will only be triggered once per user, until processed
* TRIGGER_ONCE_PER_CONTENT – The notification will only be triggered once per user and per content, until processed
* SEND_ONCE – The notification will only ever be sent once per user
* SEND_ONCE_PER_CONTENT – The notification will only ever be sent once per user and per content


#### The `@message` decorator

Messages are sub-classes of Channels with a `@message` decorator which defines the following fields:

1. `trigger_name` – a slug that will be used in the Notification model to map your code to the notifcation. Be careful when modifying it!
2. `behavior` – a definition of our this message may be triggered, see TriggerBehavior

#### Message trigger

Sending a message is the action performed when a notification is processed. For a notification to be created and scheduled, you need to trigger a message. The trigger method only requires the `target_user` but will accept additional fields:

* `target_user` – User that should receive the message
* `trigger_user` – User that triggered the message. This is only for your app to use, so you are free to use the field as you wish.
* `datetime_scheduled` – If ignored, the message will be sent as soon as possible, otherwise the queue will not process the message before that date. If set in the past, the message will also be processed right away by the queue.
* `content` – A Django model instance to be referenced to in the notification
* `data` – Additional data to be stored along the notification. This is useful when `content` is not sufficient, but should be avoided if you do not want your notification table to grow exponentially every day.
* `silent` – Boolean whether to raise exceptions if the notification cannot be triggered, or silently fail and ignore it

#### Example

**Definition**

```python
from transmissions import message, TriggerBehavior

@message('welcome-sms', behavior=TriggerBehavior.SEND_ONCE)
class WelcomeSMS(BaseTwilioSMS):

    def create_message(self):
        return 'Hey {}, welcome to transmissions!'.format(self.target_user.name)
```

**Usage**

```python
from django.utils import timezone

# Trigger a welcome SMS to be sent in 2 days
later = timezone.now()+timezone.timedelta(days=2)
WelcomeSMS.trigger(user, datetime_scheduled=later)
```


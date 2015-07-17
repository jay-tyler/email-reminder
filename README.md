#ScatterPeas Messenger
A pod for all of your scattered peas. Visit us at [scatterpeas.com](scatterpeas.com).

##Overview of Functionality
The back-end of ScatterPeas is intended to support recurring reminders
conforming to the [iCal specification](http://www.kanzaki.com/docs/ical/rrule.html).
It also allows users to be associated
with multiple 'aliases,' allowing them to choose on-the-fly message
delivery preferences, as well as the ability to send messages to family
members and friends.

##Table Contents
###uuids
The uuids table is meant to track attempts at activating user accounts.
Contents include:
* id
* alias id, foreign key
* uuid
* created: instantiation datetime in utc
* confirmation_state
###users
A parent table linking to many aliases. Effectively the 'FROM:' of each
reminder.
Contents include:
* id
* first: name
* last: name
* password
* username
* dflt_medium: 1 for email, 2 for text
* timezone: local user timezone
###aliases
A parent table linking to many reminders. Each alias is associated with
the 'TO:' for each reminder and could potentially be linked to more than
one user.
* id
* user_id, foreign key
* alias: user facing moniker -- default value is ‘ME’
* contact_info: phone or email in string form
* activation_state: 0 for unconfirmed, 1 for confirmed
* medium: indicates whether email or text; 1 for email, 2 for text
* to be added: user link (to indicate bidirectional relationships)
###reminders
A parent table to track the contents to send with a reminder, and the rrule 
used to generate jobs. Each time a job is executed, helper methods on reminders
are called to generate the next job (i.e. if there is one) and to update the 
reminder state appropriately.
Contents include:
* id
* alias_id: foreign key
* title: the small payload that is sent for every reminder
* text_payload: an optional larger payload
* media_payload: not fully implemented; may point towards a blob or a static file
* rstate: True if jobs are still pending; False otherwise.
###rrules
A table used mostly to containerize data associated with [iCal](http://www.kanzaki.com/docs/ical/rrule.html).
We may choose a different means of containerizing these in the future.
Contents include:
* DTSTART
* TZID
* FREQ
* INTERVAL
* COUNT
* BYMONTH 
* BYDAY 
* WKST
* BYMONTHDAY
* BYYEARDAY
* EXDATE
###jobs
Reminders to be sent out.
* id
* reminder_id: as foreign key
* job_state: 0 for awaiting execution, 1 for successful execution, 2 for failed, 3 for cancelled
* execution_time: in utc

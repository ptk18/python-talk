from email_clientpy import EmailClient
import sys

obj = EmailClient()
print(obj.send_email(recipient='user@gmail.com', subject='report', body='report content'))
print(obj.mark_as_read())

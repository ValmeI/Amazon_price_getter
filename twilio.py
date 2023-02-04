from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from colored import fg, attr
import config


def send_email(sent_from, sent_to, sent_subject, sent_body):

    message = Mail(
        from_email=sent_from,
        to_emails=sent_to,
        subject=sent_subject,
        html_content=sent_body)
    try:
        sg = SendGridAPIClient(config.twilio_apy_key)
        response = sg.send(message)
        if response.status_code == 202:
            print(f"\n {fg('blue')}{attr('bold')}Email sent{attr('reset')}")
        else:
            print(f"\n {fg('blue')}{attr('bold')}Email NOT SENT{attr('reset')}")
    except Exception as e:
        print(e.message)

# send_email('ignarvalme@gmail.com', 'ignarvalme@gmail.com', 'TEST IGNAR', 'TEST')

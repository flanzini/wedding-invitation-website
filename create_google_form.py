from __future__ import print_function
import os.path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive.file',
]

CREDS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
FORM_LINKS_FILE = 'form_links.json'

LANGUAGE_FORMS = [
    {
        'code': 'en',
        'name': 'English',
        'title': 'Wedding travel interest survey',
        'description': (
            'We are planning our wedding in the beautiful Carpathian mountains of Ukraine, '
            'near the borders with Romania, Hungary and Poland. Please tell us whether you would '
            'be willing to travel there and whether a later celebration in Italy would work better.'
        ),
        'questions': [
            {
                'title': 'Would you be willing to attend our wedding in the Carpathian mountains of Ukraine?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Yes, I would attend',
                    'Maybe, depending on travel and safety',
                    'No',
                ],
            },
            {
                'title': 'How many people in your party would attend if the wedding is in Ukraine?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    '1',
                    '2',
                    '3 or more',
                    'Not sure yet',
                ],
            },
            {
                'title': 'If we also plan a later celebration in Italy, would you attend that instead?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Yes',
                    'Maybe',
                    'No / Unsure',
                ],
            },
            {
                'title': 'What would make it difficult for you to travel to Ukraine?',
                'required': False,
                'type': 'TEXT',
            },
            {
                'title': 'Optional: Your name or email if you want us to follow up',
                'required': False,
                'type': 'TEXT',
            },
        ],
    },
    {
        'code': 'it',
        'name': 'Italiano',
        'title': 'Sondaggio di interesse per il viaggio al matrimonio',
        'description': (
            'Stiamo pianificando il nostro matrimonio nelle splendide montagne dei Carpazi in Ucraina, '
            'vicino ai confini con Romania, Ungheria e Polonia. Dicci se saresti disposto a viaggiare lÃ¬ '
            'o se una celebrazione successiva in Italia sarebbe piÃ¹ adatta.'
        ),
        'questions': [
            {
                'title': 'Saresti disposto a partecipare al nostro matrimonio nelle montagne dei Carpazi in Ucraina?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'SÃ¬, parteciperÃ²',
                    'Forse, a seconda del viaggio e della sicurezza',
                    'No',
                ],
            },
            {
                'title': 'Quante persone del tuo gruppo parteciperebbero se il matrimonio fosse in Ucraina?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    '1',
                    '2',
                    '3 o piÃ¹',
                    'Non sono sicuro ancora',
                ],
            },
            {
                'title': 'Se organizziamo anche una celebrazione successiva in Italia, parteciperesti invece a quella?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'SÃ¬',
                    'Forse',
                    'No / Non so',
                ],
            },
            {
                'title': 'Cosa renderebbe difficile per te viaggiare in Ucraina?',
                'required': False,
                'type': 'TEXT',
            },
            {
                'title': 'Opzionale: il tuo nome o email se vuoi che ti contattiamo',
                'required': False,
                'type': 'TEXT',
            },
        ],
    },
    {
        'code': 'uk',
        'name': 'Ð£ÐºÑ€Ð°Ñ—Ð½ÑÑŒÐºÐ°',
        'title': 'ÐžÐ¿Ð¸Ñ‚ÑƒÐ²Ð°Ð½Ð½Ñ Ñ‰Ð¾Ð´Ð¾ Ð¿Ð¾Ñ—Ð·Ð´ÐºÐ¸ Ð½Ð° Ð²ÐµÑÑ–Ð»Ð»Ñ',
        'description': (
            'ÐœÐ¸ Ð¿Ð»Ð°Ð½ÑƒÑ”Ð¼Ð¾ Ð½Ð°ÑˆÐµ Ð²ÐµÑÑ–Ð»Ð»Ñ Ð² ÐºÑ€Ð°ÑÐ¸Ð²Ð¸Ñ… ÐšÐ°Ñ€Ð¿Ð°Ñ‚Ð°Ñ… Ð£ÐºÑ€Ð°Ñ—Ð½Ð¸, Ð¿Ð¾Ð±Ð»Ð¸Ð·Ñƒ ÐºÐ¾Ñ€Ð´Ð¾Ð½Ñ–Ð² Ð· Ð ÑƒÐ¼ÑƒÐ½Ñ–Ñ”ÑŽ, Ð£Ð³Ð¾Ñ€Ñ‰Ð¸Ð½Ð¾ÑŽ Ñ‚Ð° ÐŸÐ¾Ð»ÑŒÑ‰ÐµÑŽ. '
            'Ð‘ÑƒÐ´ÑŒ Ð»Ð°ÑÐºÐ°, ÑÐºÐ°Ð¶Ñ–Ñ‚ÑŒ Ð½Ð°Ð¼, Ñ‡Ð¸ Ð³Ð¾Ñ‚Ð¾Ð²Ñ– Ð²Ð¸ Ñ‚ÑƒÐ´Ð¸ Ð¿Ð¾Ñ—Ñ…Ð°Ñ‚Ð¸ Ñ– Ñ‡Ð¸ Ð·Ñ€ÑƒÑ‡Ð½Ñ–ÑˆÐ¸Ð¼ Ð±ÑƒÐ² Ð±Ð¸ Ð¿Ñ–Ð·Ð½Ñ–ÑˆÐ¸Ð¹ Ð·Ð°Ñ…Ñ–Ð´ Ð² Ð†Ñ‚Ð°Ð»Ñ–Ñ—.'
        ),
        'questions': [
            {
                'title': 'Ð§Ð¸ Ð³Ð¾Ñ‚Ð¾Ð²Ñ– Ð²Ð¸ Ð¿Ñ€Ð¸Ñ—Ñ…Ð°Ñ‚Ð¸ Ð½Ð° Ð½Ð°ÑˆÐµ Ð²ÐµÑÑ–Ð»Ð»Ñ Ð² ÐšÐ°Ñ€Ð¿Ð°Ñ‚Ð°Ñ… Ð£ÐºÑ€Ð°Ñ—Ð½Ð¸?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Ð¢Ð°Ðº, Ñ Ð¿Ñ€Ð¸Ñ—Ð´Ñƒ',
                    'ÐœÐ¾Ð¶Ð»Ð¸Ð²Ð¾, Ð·Ð°Ð»ÐµÐ¶Ð½Ð¾ Ð²Ñ–Ð´ Ð¿Ð¾Ñ—Ð·Ð´ÐºÐ¸ Ñ‚Ð° Ð±ÐµÐ·Ð¿ÐµÐºÐ¸',
                    'ÐÑ–',
                ],
            },
            {
                'title': 'Ð¡ÐºÑ–Ð»ÑŒÐºÐ¸ Ð»ÑŽÐ´ÐµÐ¹ Ð· Ð²Ð°ÑˆÐ¾Ñ— Ð³Ñ€ÑƒÐ¿Ð¸ Ð¿Ñ€Ð¸Ñ—Ñ…Ð°Ð»Ð¸ Ð±, ÑÐºÑ‰Ð¾ Ð²ÐµÑÑ–Ð»Ð»Ñ Ð±ÑƒÐ´Ðµ Ð² Ð£ÐºÑ€Ð°Ñ—Ð½Ñ–?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    '1',
                    '2',
                    '3 Ð°Ð±Ð¾ Ð±Ñ–Ð»ÑŒÑˆÐµ',
                    'ÐŸÐ¾ÐºÐ¸ Ð½Ðµ Ð²Ð¿ÐµÐ²Ð½ÐµÐ½Ð¸Ð¹',
                ],
            },
            {
                'title': 'Ð¯ÐºÑ‰Ð¾ Ð¼Ð¸ Ñ‚Ð°ÐºÐ¾Ð¶ Ð¾Ñ€Ð³Ð°Ð½Ñ–Ð·ÑƒÑ”Ð¼Ð¾ Ð¿Ñ–Ð·Ð½Ñ–ÑˆÐµ ÑÐ²ÑÑ‚ÐºÑƒÐ²Ð°Ð½Ð½Ñ Ð² Ð†Ñ‚Ð°Ð»Ñ–Ñ—, Ñ‡Ð¸ Ð¿Ñ€Ð¸Ñ—Ð´ÐµÑ‚Ðµ Ð²Ð¸ Ñ‚ÑƒÐ´Ð¸ Ð·Ð°Ð¼Ñ–ÑÑ‚ÑŒ Ñ†ÑŒÐ¾Ð³Ð¾?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Ð¢Ð°Ðº',
                    'ÐœÐ¾Ð¶Ð»Ð¸Ð²Ð¾',
                    'ÐÑ– / ÐÐµ Ð²Ð¿ÐµÐ²Ð½ÐµÐ½Ð¸Ð¹',
                ],
            },
            {
                'title': 'Ð©Ð¾ ÑƒÑÐºÐ»Ð°Ð´Ð½Ð¸Ñ‚ÑŒ Ð´Ð»Ñ Ð²Ð°Ñ Ð¿Ð¾Ñ—Ð·Ð´ÐºÑƒ Ð´Ð¾ Ð£ÐºÑ€Ð°Ñ—Ð½Ð¸?',
                'required': False,
                'type': 'TEXT',
            },
            {
                'title': 'Ð—Ð° Ð±Ð°Ð¶Ð°Ð½Ð½ÑÐ¼: Ð²Ð°ÑˆÐµ Ñ–Ð¼â€™Ñ Ð°Ð±Ð¾ email, ÑÐºÑ‰Ð¾ Ñ…Ð¾Ñ‡ÐµÑ‚Ðµ, Ñ‰Ð¾Ð± Ð¼Ð¸ Ð· Ð²Ð°Ð¼Ð¸ Ð·Ð²â€™ÑÐ·Ð°Ð»Ð¸ÑÑ',
                'required': False,
                'type': 'TEXT',
            },
        ],
    },
]


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(
                    f'Google OAuth credentials file not found: {CREDS_FILE}. '
                    'Download it from Google Cloud Console and place it here.'
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
    return creds


def build_question_request(question, index):
    if question['type'] == 'RADIO':
        return {
            'createItem': {
                'item': {
                    'title': question['title'],
                    'questionItem': {
                        'question': {
                            'required': question['required'],
                            'choiceQuestion': {
                                'type': 'RADIO',
                                'options': [{'value': option} for option in question['options']],
                                'shuffle': False,
                            },
                        }
                    },
                },
                'location': {'index': index},
            }
        }
    return {
        'createItem': {
            'item': {
                'title': question['title'],
                'questionItem': {
                    'question': {
                        'required': question['required'],
                        'textQuestion': {},
                    }
                },
            },
            'location': {'index': index},
        }
    }


def create_form(service, form_data):
    form_body = {
        'info': {
            'title': form_data['title'],
        }
    }
    result = service.forms().create(body=form_body).execute()
    form_id = result.get('formId')
    responder_uri = result.get('responderUri')
    print(f"Created {form_data['name']} form: {responder_uri}")

    requests = [
        {
            'updateFormInfo': {
                'info': {
                    'description': form_data['description'],
                },
                'updateMask': 'description',
            }
        }
    ]

    for index, question in enumerate(form_data['questions']):
        requests.append(build_question_request(question, index))

    update_body = {'requests': requests}
    service.forms().batchUpdate(formId=form_id, body=update_body).execute()
    return {
        'code': form_data['code'],
        'name': form_data['name'],
        'url': responder_uri,
        'title': form_data['title'],
    }


def write_form_links(language_forms):
    """Save generated form links without rewriting the website."""
    output = {
        'forms': language_forms,
    }
    with open(FORM_LINKS_FILE, 'w', encoding='utf-8') as links_file:
        json.dump(output, links_file, ensure_ascii=False, indent=2)
        links_file.write('\n')

    print(f'Saved form links to {FORM_LINKS_FILE}.')


def main():
    creds = get_credentials()
    service = build('forms', 'v1', credentials=creds)
    created_forms = []
    for form_data in LANGUAGE_FORMS:
        created_forms.append(create_form(service, form_data))

    write_form_links(created_forms)
    print('\nAll done. The website was not changed; update index.html links manually if needed.')


if __name__ == '__main__':
    main()

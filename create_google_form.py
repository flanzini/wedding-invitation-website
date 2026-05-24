from __future__ import print_function

import json
import os.path

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
        'title': 'RSVP | Antonina & Filippo',
        'description': (
            'We are planning our wedding celebration in the Carpathians, Ukraine, on 14-16 May 2027. '
            'We are working with a local agency to reserve a venue and accommodation suited to our guests. '
            'Please let us know whether you expect to join us; the exact venue and travel details will follow.'
        ),
        'questions': [
            {
                'title': 'Full name',
                'required': True,
                'type': 'TEXT',
            },
            {
                'title': 'Will you join us for our wedding celebration in the Carpathians on 14-16 May 2027?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Yes, I/we plan to attend',
                    'Maybe, I/we need more details before confirming',
                    'No, I/we will not be able to attend',
                ],
            },
            {
                'title': 'How many guests should we plan for in your party, including you?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    '1',
                    '2',
                    '3',
                    '4 or more',
                    'Not sure yet',
                    'Not attending',
                ],
            },
            {
                'title': 'Would your party need accommodation for the wedding weekend?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Yes, for the nights of 14 and 15 May',
                    'Maybe, I/we need more information',
                    'No',
                    'Not attending',
                ],
            },
            {
                'title': 'If you attend, would you be interested in renting a traditional Ukrainian vyshyvanka to wear during the celebration?',
                'required': False,
                'type': 'RADIO',
                'options': [
                    'Yes, please send details when available',
                    'Maybe',
                    'No, I/we will wear wedding guest attire',
                ],
            },
            {
                'title': 'Is there anything we should know as we plan the weekend (for example travel, accommodation, dietary or accessibility needs)?',
                'required': False,
                'type': 'TEXT',
            },
            {
                'title': 'Optional: email or phone number if you would like us to contact you directly',
                'required': False,
                'type': 'TEXT',
            },
        ],
    },
    {
        'code': 'it',
        'name': 'Italiano',
        'title': 'Conferma presenza | Antonina & Filippo',
        'description': (
            'Stiamo organizzando il nostro matrimonio nei Carpazi, in Ucraina, dal 14 al 16 maggio 2027. '
            "Insieme a un'agenzia locale stiamo scegliendo la struttura e gli alloggi più adatti al numero "
            'degli invitati. Vi chiediamo quindi di indicarci se pensate di esserci; comunicheremo in seguito '
            'il luogo esatto e tutti i dettagli del viaggio.'
        ),
        'questions': [
            {
                'title': 'Nome e cognome',
                'required': True,
                'type': 'TEXT',
            },
            {
                'title': 'Potrete essere con noi per il matrimonio nei Carpazi dal 14 al 16 maggio 2027?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Sì, pensiamo di partecipare',
                    'Forse, prima di confermare vorremmo qualche dettaglio in più',
                    'No, purtroppo non riusciremo a partecipare',
                ],
            },
            {
                'title': 'Per quante persone dobbiamo prevedere la partecipazione, voi compresi?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    '1',
                    '2',
                    '3',
                    '4 o più',
                    'Non lo sappiamo ancora',
                    'Non parteciperemo',
                ],
            },
            {
                'title': "Avreste bisogno dell'alloggio per il fine settimana del matrimonio?",
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Sì, per le notti del 14 e del 15 maggio',
                    'Forse, avremmo bisogno di maggiori informazioni',
                    'No',
                    'Non parteciperemo',
                ],
            },
            {
                'title': 'Se parteciperete, vi interesserebbe noleggiare una vyshyvanka, la tradizionale camicia ricamata ucraina, da indossare durante la festa?',
                'required': False,
                'type': 'RADIO',
                'options': [
                    'Sì, ci piacerebbe ricevere informazioni',
                    'Forse',
                    'No, preferiamo un normale abito da invitato',
                ],
            },
            {
                'title': "C'è qualcosa che dovremmo sapere per organizzare il fine settimana (ad esempio viaggio, alloggio, esigenze alimentari o di accessibilità)?",
                'required': False,
                'type': 'TEXT',
            },
            {
                'title': 'Facoltativo: email o numero di telefono se desiderate essere ricontattati direttamente',
                'required': False,
                'type': 'TEXT',
            },
        ],
    },
    {
        'code': 'uk',
        'name': 'Українська',
        'title': 'Підтвердження участі | Антоніна та Філіппо',
        'description': (
            'Ми плануємо відсвяткувати наше весілля в Карпатах 14-16 травня 2027 року. '
            'Зараз разом з агенцією обираємо та бронюємо локацію відповідно до кількості гостей. '
            'Будь ласка, повідомте, чи плануєте бути з нами. Точне місце та детальну програму '
            'ми надішлемо після підтвердження бронювання.'
        ),
        'questions': [
            {
                'title': "Ім'я та прізвище",
                'required': True,
                'type': 'TEXT',
            },
            {
                'title': 'Чи зможете ви бути з нами на весіллі в Карпатах 14-16 травня 2027 року?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Так, планую бути',
                    'Можливо, зможу підтвердити пізніше',
                    'Ні, на жаль, не зможу',
                ],
            },
            {
                'title': 'Скільки гостей буде у вашій компанії, разом із вами?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Тільки я',
                    '2 людини',
                    '3 людини',
                    '4 або більше',
                    'Поки не знаю',
                    'Не братиму участі',
                ],
            },
            {
                'title': 'Чи потрібно буде передбачити для вас проживання на весільні вихідні?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    'Так, на ночі 14 та 15 травня',
                    'Можливо, потрібні додаткові деталі',
                    'Ні',
                    'Не братиму участі',
                ],
            },
            {
                'title': 'Якщо ви будете з нами, чи хотіли б ви орендувати вишиванку для святкування?',
                'required': False,
                'type': 'RADIO',
                'options': [
                    'Так, цікаво отримати деталі',
                    'Можливо',
                    'Ні, оберу звичайне святкове вбрання',
                ],
            },
            {
                'title': 'Чи є щось важливе, що нам варто врахувати під час організації (наприклад проживання, харчування або інші потреби)?',
                'required': False,
                'type': 'TEXT',
            },
            {
                'title': "За бажанням: email або номер телефону для зв'язку",
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
    print(f"Created {form_data['code']} form: {responder_uri}")
    return {
        'code': form_data['code'],
        'name': form_data['name'],
        'form_id': form_id,
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

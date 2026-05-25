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
            'Please let us know whether you expect to join us; we will contact you directly with the confirmed '
            'venue and practical details closer to the date.\n\n'
            'Privacy note: We will use the information you provide only to organise our wedding and communicate '
            'with you about it. We will keep it private and delete it when it is no longer needed for the celebration.'
        ),
        'questions': [
            {
                'title': 'Full name of the person completing this form',
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
                'title': 'How many guests should we expect with you, including you?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    {'value': '1', 'goToSectionId': 'en_details'},
                    {'value': '2', 'goToSectionId': 'en_guests'},
                    {'value': '3', 'goToSectionId': 'en_guests'},
                    {'value': '4 or more', 'goToSectionId': 'en_guests'},
                    {'value': 'Not sure yet', 'goToSectionId': 'en_details'},
                    {'value': 'Not attending', 'goToSectionId': 'en_details'},
                ],
            },
            {
                'id': 'en_guests',
                'title': 'Guests joining you',
                'type': 'SECTION',
            },
            {
                'title': (
                    'Please list the full names of everyone who would attend with you. '
                    'If any children would attend, please include their ages at the time of the wedding.'
                ),
                'required': True,
                'type': 'TEXT',
                'paragraph': True,
            },
            {
                'id': 'en_details',
                'title': 'A few final details',
                'type': 'SECTION',
            },
            {
                'title': 'Is there anything we should know as we plan the weekend (for example dietary or accessibility needs)?',
                'required': False,
                'type': 'TEXT',
                'paragraph': True,
            },
            {
                'title': 'Email address and/or phone number where we can contact you with confirmed wedding details',
                'required': True,
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
            'Vi chiediamo di indicarci se pensate di esserci; vi comunicheremo direttamente la location confermata '
            'e tutti i dettagli pratici in prossimità della data.\n\n'
            'Nota sulla privacy: useremo le informazioni fornite esclusivamente per organizzare il nostro matrimonio '
            'e comunicare con voi al riguardo. Le manterremo riservate e le elimineremo quando non saranno più necessarie.'
        ),
        'questions': [
            {
                'title': 'Nome e cognome della persona che compila il modulo',
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
                'title': 'Quante persone parteciperanno insieme a voi, voi compresi?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    {'value': '1', 'goToSectionId': 'it_details'},
                    {'value': '2', 'goToSectionId': 'it_guests'},
                    {'value': '3', 'goToSectionId': 'it_guests'},
                    {'value': '4 o più', 'goToSectionId': 'it_guests'},
                    {'value': 'Non lo sappiamo ancora', 'goToSectionId': 'it_details'},
                    {'value': 'Non parteciperemo', 'goToSectionId': 'it_details'},
                ],
            },
            {
                'id': 'it_guests',
                'title': 'Le persone che saranno con voi',
                'type': 'SECTION',
            },
            {
                'title': (
                    'Indicate nome e cognome di tutte le persone che parteciperebbero con voi. '
                    "Se ci saranno bambini, indicate anche la loro età al momento del matrimonio."
                ),
                'required': True,
                'type': 'TEXT',
                'paragraph': True,
            },
            {
                'id': 'it_details',
                'title': 'Qualche ultimo dettaglio',
                'type': 'SECTION',
            },
            {
                'title': "C'è qualcosa che dovremmo sapere per organizzare il fine settimana (ad esempio esigenze alimentari o di accessibilità)?",
                'required': False,
                'type': 'TEXT',
                'paragraph': True,
            },
            {
                'title': 'Indirizzo email e/o numero di telefono a cui potremo comunicarvi i dettagli confermati del matrimonio',
                'required': True,
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
            'Будь ласка, повідомте, чи плануєте бути з нами; підтверджену локацію та практичні деталі '
            'ми надішлемо вам особисто ближче до дати.\n\n'
            'Примітка про конфіденційність: надану інформацію ми використовуватимемо лише для організації '
            "нашого весілля та зв'язку з вами щодо нього. Ми зберігатимемо її конфіденційно й видалимо, "
            'коли вона більше не буде потрібна для святкування.'
        ),
        'questions': [
            {
                'title': "Ім'я та прізвище особи, яка заповнює цю форму",
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
                'title': 'Скільки гостей буде разом із вами, враховуючи вас?',
                'required': True,
                'type': 'RADIO',
                'options': [
                    {'value': 'Тільки я', 'goToSectionId': 'uk_details'},
                    {'value': '2 людини', 'goToSectionId': 'uk_guests'},
                    {'value': '3 людини', 'goToSectionId': 'uk_guests'},
                    {'value': '4 або більше', 'goToSectionId': 'uk_guests'},
                    {'value': 'Поки не знаю', 'goToSectionId': 'uk_details'},
                    {'value': 'Не братиму участі', 'goToSectionId': 'uk_details'},
                ],
            },
            {
                'id': 'uk_guests',
                'title': 'Гості, які будуть із вами',
                'type': 'SECTION',
            },
            {
                'title': (
                    "Будь ласка, вкажіть ім'я та прізвище кожного, хто планує бути разом із вами. "
                    'Якщо серед гостей будуть діти, також вкажіть їхній вік на момент весілля.'
                ),
                'required': True,
                'type': 'TEXT',
                'paragraph': True,
            },
            {
                'id': 'uk_details',
                'title': 'Ще кілька деталей',
                'type': 'SECTION',
            },
            {
                'title': 'Чи є щось важливе, що нам варто врахувати під час організації (наприклад особливості харчування чи потреби доступності)?',
                'required': False,
                'type': 'TEXT',
                'paragraph': True,
            },
            {
                'title': "Email та/або номер телефону, за яким ми зможемо повідомити вам підтверджені деталі весілля",
                'required': True,
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


def build_form_item(question, section_ids=None):
    if question['type'] == 'SECTION':
        return {
            'title': question['title'],
            'pageBreakItem': {},
        }
    if question['type'] == 'RADIO':
        options = []
        for option in question['options']:
            if isinstance(option, str):
                options.append({'value': option})
                continue
            choice_option = {'value': option['value']}
            if section_ids:
                choice_option['goToSectionId'] = section_ids[option['goToSectionId']]
            options.append(choice_option)
        return {
            'title': question['title'],
            'questionItem': {
                'question': {
                    'required': question['required'],
                    'choiceQuestion': {
                        'type': 'RADIO',
                        'options': options,
                        'shuffle': False,
                    },
                }
            },
        }
    return {
        'title': question['title'],
        'questionItem': {
            'question': {
                'required': question['required'],
                'textQuestion': {
                    'paragraph': question.get('paragraph', False),
                },
            }
        },
    }


def build_question_request(question, index):
    return {
        'createItem': {
            'item': build_form_item(question),
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

    created_form = service.forms().get(formId=form_id).execute()
    section_ids = {
        question['id']: created_form['items'][index]['itemId']
        for index, question in enumerate(form_data['questions'])
        if question['type'] == 'SECTION'
    }
    navigation_requests = []
    for index, question in enumerate(form_data['questions']):
        has_navigation = (
            question['type'] == 'RADIO'
            and any(isinstance(option, dict) for option in question['options'])
        )
        if has_navigation:
            navigation_requests.append({
                'updateItem': {
                    'item': build_form_item(question, section_ids=section_ids),
                    'location': {'index': index},
                    'updateMask': 'questionItem.question.choiceQuestion.options',
                }
            })
    if navigation_requests:
        service.forms().batchUpdate(formId=form_id, body={'requests': navigation_requests}).execute()

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

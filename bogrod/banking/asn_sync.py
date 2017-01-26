import csv
import io
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from django.utils.timezone import datetime

from banking.models import Account, Transaction


def login(username, password):
    session = requests.Session()
    url = 'https://www.asnbank.nl/onlinebankieren/secure/loginparticulier.html'
    src = session.get(url).text
    soup = BeautifulSoup(src, 'lxml')
    token = soup.find('input', {'name': 'ibp.integrity.token'})['value']
    session.integrity_token = token
    payload = {
        'orgurl': '',
        'ibp.integrity.token': session.integrity_token,
        'j_username': username,
        'j_password': password,
        'action_sendWithDigicode': 'Inloggen',
    }
    url = 'https://www.asnbank.nl/onlinebankieren/secure/j_security_check'
    response = session.post(url, data=payload)
    return session, response


def logout(session):
    url = ("https://www.asnbank.nl"
           "/onlinebankieren/secure/logout/logoutConfirm.html")
    response = session.get(url)
    return session, response


def import_accounts(session):
    url = ("https://www.asnbank.nl/onlinebankieren"
           "/homepage/secure/homepage/homepage.html")
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    for table in soup.find_all('table'):
        account_type = table.find('th').text
        if 'Betalen' in account_type:
            account_type = 'checking'
        elif 'Sparen' in account_type:
            account_type = 'savings'
        elif 'Beleggen' in account_type:
            account_type = 'investment'
            continue  # TODO handle this properly; has IBAN uniqueness issues
        else:
            account_type = 'other'
        for tr in table.find('tbody').find_all('tr'):
            try:
                iban = tr['account']
            except KeyError:
                continue
            account, cr = Account.objects.get_or_create(iban=iban)
            account.account_type = account_type
            account.save()
    return session, response


def import_transactions(session, account, since=None, until=None):
    url = ("https://www.asnbank.nl/onlinebankieren"
           "/bankieren/secure/transacties/transactieoverzicht.html"
           "?accountNr={}").format(account.iban)
    src = session.get(url).text
    soup = BeautifulSoup(src, 'lxml')
    # TODO this can probably be minimized; this was copied verbatim
    payload = {
        'ibp.integrity.token':
            soup.find('input', {'name': 'ibp.integrity.token'})['value'],
        'formId': 'transactionForm',
        "pageName": "betalen",
        "accountNr": account.iban,
        "tabstop_sl_accountNr_rekening": "",
        "range": "LAST_MONTH",
        "creditAccount": "",
        "nameSecondParty": "",
        "reference": "",
        "description": "",
        "dateStart": "",
        "dateEnd": "",
        "amountLow": "",
        "amountLowCents": "",
        "amountHigh": "",
        "amountHighCents": "",
        "searchDebetCredit":
            soup.find('input', {'name': 'searchDebetCredit'})['value'],
        "accountNumber": "",
        "downloadDateStart": "",
        "downloadDateEnd": "",
        "downloadtype": "ALLE_TRANSACTIES",  # TODO use since and until here
        "cbValue_downloadFilter": "cbExists",
        "filetype": "CSVIBAN",
        "action_downloadTransactions": "Start+downloaden",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "action": "Print+deze+transactie+(pdf)",
        "pagingSize": (soup.find('select', {'name': 'pagingSize'})
                           .find_all('option', selected=True)[0]['value']),
        "transactionOffset": "",
        "receivings": soup.find('input', {'name': 'receivings'})['value'],
        "expenses": soup.find('input', {'name': 'expenses'})['value'],
        "showSearch": "",
        "sequenceNr": "",
        "journalDate": "",
        "action": "",
    }
    response = session.post(url, data=payload)
    csvreader = csv.reader(io.StringIO(response.text), delimiter=',')
    for row in csvreader:
        try:
            t = Transaction.objects.get(
                journal_date=datetime.strptime(row[11], '%d-%m-%Y'),
                sequence_number=int(row[15]),
            )
        except Transaction.DoesNotExist:
            t = Transaction(
                journal_date=datetime.strptime(row[11], '%d-%m-%Y'),
                sequence_number=int(row[15]),
            )
        t.booking_date = datetime.strptime(row[0], '%d-%m-%Y')
        t.account, cr = Account.objects.get_or_create(iban=row[1])
        t.counter_account, cr = Account.objects.get_or_create(iban=row[2])
        t.counter_name = row[3]
        t.account_currency = row[7]
        t.balance_before = Decimal(row[8])
        t.mutation_currency = row[9]
        t.mutation_value = Decimal(row[10])
        t.value_date = datetime.strptime(row[12],    '%d-%m-%Y')
        t.internal_code = int(row[13])
        t.global_code = row[14]
        t.reference = row[16]
        t.description = row[17]
        t.statement_number = int(row[18])
        t.save()
    return session, response

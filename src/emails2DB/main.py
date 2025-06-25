import imaplib
import email
from email.header import decode_header
import firebirdsql
from datetime import datetime, timedelta
import quopri
import base64
from bs4 import BeautifulSoup
import re
import os 
import unicodedata
import config
import requests
import schedule
import time
from sys import platform


# Конфигурация IMAP
IMAP_SERVER = "imap.mail.ru"

# Конфигурация Firebird
DB_HOST = config.host
DB_NAME = config.database
DB_USER = config.user
DB_PASSWORD = config.password

headers = config.headers

if platform == "linux" or platform == "linux2":
    print('linux')
    MATTERMOST_URL = 'https://mm-mpk.ru'
    UPLOAD_DIR = "/uploads"
    UPLOAD_DIR_2_DB = "\\\\10.199.1.11\\РАБОТА\\10. Личные папки"
elif platform == "darwin":
    print('OS X')
elif platform == "win32":
    print('Windows')
    MATTERMOST_URL = config.MATTERMOST_URL
    UPLOAD_DIR = "\\\\10.199.1.11\\РАБОТА\\10. Личные папки"
    UPLOAD_DIR_2_DB = "\\\\10.199.1.11\\РАБОТА\\10. Личные папки"

ignored_senders = [
    'a.bukreev@mosproektkompleks.ru',
    'reports@yoomoney.ru',
    'notification@russianpost.ru',
    'moscow@officemag.ru',
    'no-reply@gosuslugi.ru',
    'noreply@sbis.ru',
    'rafaelbeauty@rafaelbeauty.ru',
    'no-reply.dns@dns-shop.ru',
    '@fsk-lider.ru',
    '@mail.gba-assistent-newclient.ru',
    '@yoomoney.ru',
    '@raww.ru',
    '@account.2gis.com',
    '@info.pobeda.aero',
    '@i-tenders.ru',
    '@sender.ozon.ru',
    '@carcade.com',
    '@cdek.ru',
    '@mangotele.com',
    '@mi-shop.com',
    '@tenchat.ru',
    '@tensor.ru',
    '@alfabank.ru',
    '@site.hh.ru',
    '@sabylink.ru',
    '@officemag.ru',
    '@mysoftpro.ru',
    '@stmwater.ru',
    '@europlan.ru',
    '@kontur.ru',
    '@regstal.ru',
    '@onlinetrade.ru',
    '@news.ozon.ru',
    '@sberbank.ru',
    '@kdiscont.ru',
    '@printer-plotter.ru',
    '@kdm-y.ru',
    '@kontur.ru',
    '@news-umitc.ru',
    '@agregatoreat.ru',
    '@novapribor.ru',
    '@yandex-team.ru',
    '@sberbank-ast.ru',
    '@npower.ru',
    '@prin.ru',
    '@applerealestate.ru',
    '@stroyprice.ru',
    '@stolitsafinance.ru',
    '@sroprp.ru',
    '@noreply.etprf.ru',
    '@vknsystems.ru',
    '@webinar.ru',
    '@ip-levina.ru',
    '@sagalov.ru',
    '@mkmlogistics.ru',
    '@argogeo.ru',
    '@iesoft.ru'
    '@mail.instagram.com',
    '@fkdnews.ru',
    '@chek.pofd.ru',
    '@telegraf.ru',
    '@hhexpo.ru',
    '@dreamgr.bitrix24.ru',
    '@chipcart.shop',
    '@taxi.yandex.ru',
    '@rezinotekhnika-asbest.ru',
    'infoprintpro@yandex.ru',
    'notifications@avito.ru',
]


def extract_invoice_number(text):
    # Регулярное выражение для поиска номера счёта
    match = re.search(r'сч[её]ту\s*№\s*(\d+-\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def shorten_filename(filename, max_length):
    # Разделяем имя файла и его расширение
    name, ext = os.path.splitext(filename)
    
    # Проверяем, нужно ли укоротить имя
    if len(name) > max_length - len(ext) - 3:  # Учитываем длину расширения и многоточия
        return name[:max_length - len(ext) - 3] + '...' + ext  # Убираем 3 символа для многоточия
    # filename = filename.replace('//','_')
    return filename  # Возвращаем оригинальное имя, если оно в пределах лимита


def show_directory_contents(directory):
    try:
        # Получаем список файлов и папок в указанной директории
        contents = os.listdir(directory)
        
        # Проверяем, есть ли содержимое
        if not contents:
            print(f"Папка '{directory}' пуста.")
        else:
            print(f"Содержимое папки '{directory}':")
            for item in contents:
                print(item)
    except FileNotFoundError:
        print(f"Ошибка: Папка '{directory}' не найдена.")
    except PermissionError:
        print(f"Ошибка: У вас нет прав доступа к папке '{directory}'.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def upload_files_to_mattermost(files):
    uploaded_files = []
    for file in files:
        # file = file.replace('/','_')
        directory_path = os.path.dirname(file)
        file_name = shorten_filename(os.path.basename(file),100)
        file = os.path.join(directory_path, file_name)
        print(directory_path, file_name, file)
        with open(file, 'rb') as f:
            response = requests.post(
                f'{MATTERMOST_URL}/api/v4/files',
                headers={'Authorization': f'Bearer {config.ACCESS_TOKEN}'},
                data={'channel_id': 'kbcyc66jbtbcubs93h43nf19dy'},
                files={'files': f}
                # verify=False
            )
            print(f'Response from file upload: {response.status_code}, {response.text}')  # Добавьте эту строку для отладки
            if response.status_code == 201:
                file_id = response.json()['file_infos'][0]['id']
                uploaded_files.append(file_id)
                print(f'Файл успешно загружен: {file}, {response.status_code}, {response.text}')
                print(f'{file_id=}')
            else:
                print(f'Не удалось загрузить файл {file}: {response.status_code}, {response.text}')
    if len(uploaded_files) > 10:
        uploaded_files = uploaded_files[:10]
    return uploaded_files    


def send_message_to_channel(channel_id, message, file_ids=None, props={}):
    url = f'{MATTERMOST_URL}/api/v4/posts'
    # Подготовка данных для сообщения
    payload = {
        'channel_id': channel_id,
        'message': message
    }
    payload.update(props)
    if file_ids:
        payload['file_ids'] = file_ids
    response = requests.post(url, json=payload, headers=headers) #, verify=False)
    if response.status_code == 201:
        print('Message sent successfully.')
        return response.json()
    else:
        print(f'Failed to send message: {response.status_code}, {response.text}')


def send_message_to_thread(channel_id, root_id, message):
    url = f'{MATTERMOST_URL}/api/v4/posts'
    payload = {
        'channel_id': channel_id,
        'root_id': root_id,
        'message': message
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print('Message sent to thread successfully.')
    else:
        print(f'Failed to send message to thread: {response.status_code}, {response.text}')


def normalize_filename(filename):
    valid_chars = "-_.() %s%s" % (unicodedata.normalize('NFKD', 'йцукенгшщзхъфывапролджэячсмитьбюё').encode('ascii', 'ignore').decode('utf-8'), unicodedata.normalize('NFKD', 'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ').encode('ascii', 'ignore').decode('utf-8'))
    valid_chars += ''.join(chr(i) for i in range(32, 127) if chr(i).isalnum())
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    return cleaned_filename


def get_users_with_email_pass():
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password, charset=config.charset) as con:
        cur = con.cursor()
        sql = f"SELECT F12, F5038, F8 FROM T3 WHERE F5038 IS NOT NULL"
        cur.execute(sql)
        result = cur.fetchall()
        print(len(result))
        print(f'{result=}')
        return(result)
    

def get_thread_id_and_channdel_id(invoice_number):
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password, charset=config.charset) as con:
        cur = con.cursor()
        sql = f"""
        SELECT 
            T213.F4928 AS THREAD_ID,
            T212.F4644 AS CHANNEL_ID
        FROM T213
        JOIN T212 ON T213.F4573 = T212.ID
        WHERE T213.F5727 = '{invoice_number}'
        """
        cur.execute(sql)
        result = cur.fetchone()
        return result


def get_max_msg_id_in_folder(folder_name, email):
    if folder_name == 'sent':
        email_field = 'F5033'
        folder_id_field = 'F5275'
    if folder_name == 'inbox':
        email_field = 'F5034'
        folder_id_field = 'F5037'
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password, charset=config.charset) as con:
        cur = con.cursor()
        sql = f"SELECT MAX({folder_id_field}) FROM T254 WHERE F5039 = '{folder_name}' AND {email_field} = '{email}'"
        cur.execute(sql)
        result = cur.fetchone()[0]
        return(result)


def normlize_folder(folder):
    match = re.search(r'"([^"]+)"$', folder)
    if match:
        result = match.group(1)
        print(result)
    return result 


def encode_att_names(str_pl):
    enode_name = re.findall(r"\=\?.*?\?\=", str_pl)
    
    if len(enode_name) == 1:
        encoding = decode_header(enode_name[0])[0][1]
        decode_name = decode_header(enode_name[0])[0][0]
        
        # Проверяем, есть ли кодировка
        if encoding is not None:
            try:
                decode_name = decode_name.decode(encoding)
            except (UnicodeDecodeError, TypeError):
                # Если произошла ошибка декодирования, пробуем использовать utf-8
                decode_name = decode_name.decode('utf-8', errors='replace')
        else:
            decode_name = decode_name  # Если кодировка отсутствует, просто оставляем строку как есть
        
        str_pl = str_pl.replace(enode_name[0], decode_name)
    
    elif len(enode_name) > 1:
        nm = ""
        for part in enode_name:
            encoding = decode_header(part)[0][1]
            decode_name = decode_header(part)[0][0]
            
            # Проверяем, есть ли кодировка
            if encoding is not None:
                try:
                    decode_name = decode_name.decode(encoding)
                except (UnicodeDecodeError, TypeError):
                    # Если произошла ошибка декодирования, пробуем использовать utf-8
                    decode_name = decode_name.decode('utf-8', errors='replace')
            else:
                decode_name = decode_name  # Если кодировка отсутствует, просто оставляем строку как есть
            
            nm += decode_name
        
        str_pl = str_pl.replace(enode_name[0], nm)
        for c, i in enumerate(enode_name):
            if c > 0:
                str_pl = str_pl.replace(enode_name[c], "").replace('"', "").rstrip()
    
    return str_pl


def extract_email(recipient_str):
    # Регулярное выражение для извлечения адреса электронной почты
    email_pattern = r'[\w\.-]+@[\w\.-]+'
    
    # Поиск всех совпадений в строке
    emails = re.findall(email_pattern, recipient_str)
    
    # Возвращаем первый найденный адрес (предполагаем, что он один)
    if emails:
        # return emails[0]
        return emails
    else:
        return None


def normalize_whitespace(text):
    if text:
        # Удаление лишних пробелов
        text = re.sub(r' +', ' ', text)
        # Удаление лишних переводов строки
        text = re.sub(r'\n+', '\n', text)
        return text
    else:
        return None


def imap_date(date):
    return date.strftime('%d-%b-%Y')


def decode_payload(part):
    content_transfer_encoding = part.get("Content-Transfer-Encoding", "").lower()
    payload = part.get_payload(decode=False)
    
    if content_transfer_encoding == "quoted-printable":
        payload = quopri.decodestring(payload)
    elif content_transfer_encoding == "base64":
        payload = base64.b64decode(payload)
    else:
        payload = part.get_payload(decode=True)
    
    charset = part.get_content_charset()
    if charset is None:
        charset = "utf-8"
    
    return payload.decode(charset, errors="ignore")


def get_letter_text_from_html(body):
    body = body.replace("<div><div>", "<div>").replace("</div></div>", "</div>")
    try:
        soup = BeautifulSoup(body, "html.parser")
        paragraphs = soup.find_all("div")
        text = ""
        for paragraph in paragraphs:
            text += paragraph.text + "\n"
        return text.replace("\xa0", " ")
    except (Exception) as exp:
        print("text ftom html err ", exp)
        return False


def letter_type(part):
    if part["Content-Transfer-Encoding"] in (None, "7bit", "8bit", "binary"):
        return part.get_payload()
    elif part["Content-Transfer-Encoding"] == "base64":
        encoding = part.get_content_charset() or 'utf-8'  # Установите кодировку по умолчанию
        return base64.b64decode(part.get_payload()).decode(encoding, errors='replace')  # Обработка ошибок
    elif part["Content-Transfer-Encoding"] == "quoted-printable":
        encoding = part.get_content_charset() or 'utf-8'  # Установите кодировку по умолчанию
        try:
            return quopri.decodestring(part.get_payload()).decode(encoding)
        except UnicodeDecodeError:
            # Попробуйте другую кодировку или обработайте ошибку
            return quopri.decodestring(part.get_payload()).decode('ISO-8859-1', errors='replace')
    else:  # все возможные типы: quoted-printable, base64, 7bit, 8bit и binary
        return part.get_payload()


def get_letter_text(msg):
    def letter_type(part):
        # Функция для декодирования содержимого части письма
        charset = part.get_content_charset() or 'utf-8'
        return part.get_payload(decode=True).decode(charset, errors='ignore')

    def get_letter_text_from_html(html):
        # Функция для извлечения текста из HTML с сохранением переводов строк
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        # Заменяем <br> на переводы строк
        for br in soup.find_all("br"):
            br.replace_with("\n")
        return soup.get_text()

    text_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "text":
                extract_part = letter_type(part)
                if part.get_content_subtype() == "html":
                    letter_text = get_letter_text_from_html(extract_part)
                else:
                    letter_text = extract_part.rstrip().lstrip()
                text_parts.append(letter_text)
    else:
        if msg.get_content_maintype() == "text":
            extract_part = letter_type(msg)
            if msg.get_content_subtype() == "html":
                letter_text = get_letter_text_from_html(extract_part)
            else:
                letter_text = extract_part
            text_parts.append(letter_text)

    # Объединяем все части текста с сохранением переводов строк
    unique_text = "\n".join(text_parts)
    return unique_text.replace("<", "").replace(">", "").replace("\xa0", " ")


# def get_letter_text(msg):
#     if msg.is_multipart():
#         for part in msg.walk():
#             count = 0
#             if part.get_content_maintype() == "text" and count == 0:
#                 extract_part = letter_type(part)
#                 if part.get_content_subtype() == "html":
#                     letter_text = get_letter_text_from_html(extract_part)
#                 else:
#                     letter_text = extract_part.rstrip().lstrip()
#                 count += 1
#                 return (
#                     letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")
#                 )
#     else:
#         count = 0
#         if msg.get_content_maintype() == "text" and count == 0:
#             extract_part = letter_type(msg)
#             if msg.get_content_subtype() == "html":
#                 letter_text = get_letter_text_from_html(extract_part)
#             else:
#                 letter_text = extract_part
#             count += 1
#             return letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")


# def get_letter_text(msg): # из дипсика
#     letter_text = ""
#     if msg.is_multipart():
#         count = 0  # Инициализация счетчика вне цикла
#         for part in msg.walk():
#             if part.get_content_maintype() == "text" and count == 0:
#                 extract_part = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
#                 if part.get_content_subtype() == "html":
#                     letter_text = get_letter_text_from_html(extract_part)
#                 else:
#                     letter_text = extract_part.rstrip().lstrip()
#                 count += 1
#                 break  # Выход из цикла после обработки первой текстовой части
#     else:
#         # Если письмо не multipart, просто извлекаем текст
#         extract_part = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8')
#         if msg.get_content_subtype() == "html":
#             letter_text = get_letter_text_from_html(extract_part)
#         else:
#             letter_text = extract_part.rstrip().lstrip()

#     return letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")


def decode_header_value(header_value):
    if header_value is None:
        return ""
    parts = decode_header(header_value)
    decoded_string = ""
    for part, encoding in parts:
        if isinstance(part, bytes):
            try:
                decoded_string += part.decode(encoding.lower() if encoding else 'utf-8')
            except (LookupError, UnicodeDecodeError, AttributeError):
                decoded_string += part.decode('latin-1')
        else:
            decoded_string += part
    return decoded_string


def get_attachments(msg):
    attachments = list()
    for part in msg.walk():
        if (
            part.get_content_disposition() == "attachment"
            and part.get_filename()  # Проверяет наличие имени файла
        ):
            filename = part.get_filename()
            if filename:  # На всякий случай (хотя get_filename() уже проверил)
                filename = encode_att_names(filename)  # Декодируем, если нужно
                attachments.append(filename)
    return attachments


def save_attachments(msg, download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue

        file_name = part.get_filename()
        if file_name:
            print(f'{file_name=}')
            filename_edit = encode_att_names(file_name)
            filename_edit = shorten_filename(filename_edit, 100)
            filename_edit = filename_edit.replace('/', '_')
            print(f'{filename_edit=}')

            file_path = os.path.join(download_folder, filename_edit)
            payload = part.get_payload(decode=True)
            if payload is not None:  # Проверка на None
                with open(file_path, 'wb') as f:
                    f.write(payload)
                print(f'Скачан файл {filename_edit}')
            else:
                print(f'Не удалось получить полезную нагрузку для {filename_edit}')


def check_availability_email(email_id, folder_id_field, sender, subject):
    con = firebirdsql.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cur = con.cursor()
    # Проверка наличия записи с таким же email_id и recipient
    cur.execute(f"""
        SELECT COUNT(*)
        FROM T254
        WHERE {folder_id_field} = '{email_id}' AND F5033 = '{sender}' AND F5035 = '{subject}'
    """)
    count = cur.fetchone()[0]
    return count


def remove_list_formatting(text):
    lines = text.splitlines()  # Разделяем текст на строки
    cleaned_text = []  # Список для хранения очищенных строк

    for line in lines:
        # Убираем маркеры списка (например, "-", "*") и лишние пробелы
        if line.strip().startswith(('-', '*')):
            cleaned_line = line.strip()[1:].strip()  # Убираем маркер и лишние пробелы
            cleaned_text.append(cleaned_line)  # Добавляем очищенную строку
        else:
            cleaned_text.append(line.strip())  # Добавляем строку без изменений

    # Соединяем строки с помощью перевода строки
    return '\n'.join(cleaned_text)


def insert_into_firebird(email_data):
    # try:
        print(f'****Записываем все в базу данных*****')
        print(f'{email_data=}')
        message_id = 'NULL'
        con = firebirdsql.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = con.cursor()
        #Если это письмо в адрес почты с формами обратной связи то формируем и отправляем сообщение в ММ
        if (email_data["recipient"] == "fos@mosproektkompleks.ru" 
            or email_data["recipient"] == "info@mosproektkompleks.ru" 
            or email_data["recipient"] == "zakaz@mosproektkompleks.ru" 
            or email_data["recipient"] == "moder@encom.ru"
            or email_data["recipient"] == "info@encom.ru")\
            and email_data["folder_name"] == 'inbox': 
            upload_files=[]
            message = f'=======================================\n'
            message = f'Дата: {email_data["date"]}, Время: {email_data["time"]}\n'
            if email_data["recipient"] == "fos@mosproektkompleks.ru":
                message += f'## Заполнена 📢 форма обратной связи 📢: \n'
            if email_data["recipient"] == "info@mosproektkompleks.ru":
                message += f'## Получено письмо на ℹ️ info@mosproektkompleks.ru ℹ️: \n'
            if email_data["recipient"] == "zakaz@mosproektkompleks.ru":
                message += f'## Получено письмо на 🛒 zakaz@mosproektkompleks.ru 🛒: \n'
            if email_data["sender"] == 'messages@avito.ru':
                message += f'### Новое сообщение от :avito: АВИТО :avito:\n'
            if email_data["recipient"] == 'info@encom.ru':
                message += f'### 💚ЗАПРОС В ЭНКОМ💚\n'
            if email_data["recipient"] == 'moder@encom.ru':
                message += f'### ❇️ЗАПРОС ОБРАТНОЙ СВЯЗИ В ЭНКОМ❇️\n'
            message += f'### Отправитель: {email_data["sender"]}\n'
            message += f'### Тема: {email_data["subject"]}\n\
### Сообщение: \n {email_data["body"]}* \n'

            if email_data["attachments"]:
                k=0
                message += '### Приложения: \n'
                for attachment in email_data["attachments"]:
                    attachment = attachment.replace('/','_')
                    k+=1
                    upload_file = os.path.join(email_data["download_folder"],attachment)
                    upload_files.append(upload_file)
                    message += f'{k}. {attachment} \n'
            else:
                pass
            message += f'\n'
            message += f'======================================='
            print(f'Отправляем в канал Подготовка КП следующее сообщение: \n{message}')
            print(f'{upload_files=}')
            if not any(email_data["sender"].endswith(domain) for domain in ignored_senders):
                if email_data["sender"] != 'op@profi.ru':
                    # Отправка сообщения в канал "Подготвка КП"
                    managerNicknames = ['a.bukreev', 'a.lavruhin', 'm.ulanov', 's.volkov',
                                        'b.musaev',
                                        ]  # список тех, кто может удалять и менять статус КП
                    props = {
                        "attachments": [
                            {
                                "actions": [
                                    {
                                        "id": "delete",
                                        "name": "❌Удалить",
                                        "integration": {
                                            "url": f"{webhookLocalhostUrl}:{webhook_host_port}/"
                                                   "hooks/delete",
                                            "context": dict(
                                                # message=message.body,
                                                managerNicknames=managerNicknames,
                                            )
                                        },
                                    },
                                    {
                                        "id": "reactTo",
                                        "name": "⛔Неквал",
                                        "integration": {
                                            "url": f"{webhookLocalhostUrl}:{webhook_host_port}/"
                                                   "hooks/reactTo",
                                            "context": dict(
                                                # message=message.body,
                                                managerNicknames=managerNicknames,
                                            )
                                        },
                                    },
                                    {
                                        "id": "createLead",
                                        "name": "🚩Создать Лида",
                                        "integration": {
                                            "url": f"{webhookLocalhostUrl}:{webhook_host_port}/"
                                                   "hooks/createLead",
                                            "context": dict(
                                                # message=message.body,
                                                managerNicknames=managerNicknames,
                                            )
                                        },
                                    },
                                    {
                                        "id": "createKP",
                                        "name": "💲Создать КП",
                                        "integration": {
                                            "url": f"{webhookLocalhostUrl}:{webhook_host_port}/"
                                                   "hooks/createKP",
                                            "context": dict(
                                                # message=message.body,
                                                managerNicknames=managerNicknames,
                                            )
                                        },
                                    },
                                ],
                            }
                        ]
                    }
                    message_id = send_message_to_channel('kbcyc66jbtbcubs93h43nf19dy', message[:3990], upload_files_to_mattermost(upload_files), props=props)['id']
                else:
                    # Отправка сообщения в канал "Профи.ру"
                    message_id = send_message_to_channel('ncmxtc7ndfgtm8y1seq9zskijc', message[:3990], upload_files_to_mattermost(upload_files))['id']
            # Проверяем если письмо от Юмани 
            # if email_data["sender"] == 'ecommerce@yoomoney.ru' and email_data["subject"].startswith("Вы получили оплату"):
            if email_data["sender"] == 'ecommerce@yoomoney.ru':
                send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', f'МЫ ПОЛУЧИЛИ ОПЛАТУ')
                message = '## Получена 💰оплата💰 от физ. лица через ЮКассу! \n '
                message += f'### Тема: {email_data["subject"]}\n\
### Сообщение: \n {email_data["body"]}* \n'
                if extract_invoice_number(email_data["subject"]):
                    try:
                        thread_id, channel_id = get_thread_id_and_channdel_id(extract_invoice_number(email_data["subject"]))
                        send_message_to_thread(channel_id, thread_id, 'Счёт оплачен через Юкассу')
                    except Exception as ex:
                        send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', f'Не удалось найти тред для отправки сообщения')
                # Отправка сообщения в канал "💸Оплаты"
                send_message_to_channel('de31x3w9cbg55c3hdbf13mgeir',message[:3990])['id']
            else:
                pass

        
        
        print(f'Записываем в базу данных письмо {email_data["folder_name"]} {email_data["sender"]} {email_data["recipient"]} {email_data["subject"]} {email_data["email_id"]}')
        cur.execute('SELECT GEN_ID(GEN_T254, 1) FROM RDB$DATABASE')
        email_record_id = cur.fetchone()[0]
        cur.execute(f"""
            INSERT INTO T254 (ID, F5031, F5032, F5033, F5034, F5035, F5036, {email_data["folder_id_field"]}, F5039, F5269, F5561)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_record_id,
            email_data["date"],
            email_data["time"],
            email_data["sender"],
            email_data["recipient"],
            email_data["subject"],
            email_data["body"],
            email_data["email_id"],
            email_data["folder_name"],
            email_data["download_folder_2_db"],
            message_id
        ))
        con.commit()
        if email_data["attachments"]:
            for attachment in email_data["attachments"]:
                cur.execute('SELECT GEN_ID(GEN_T276, 1) FROM RDB$DATABASE')
                file_record_id = cur.fetchone()[0]   
                values = {
        'id': file_record_id,
        'F5270': email_record_id,
        'F5271': attachment
        }
                sql = f"""INSERT INTO T276 (
        {', '.join(values.keys())}
    ) VALUES (
        {', '.join(f"'{value}'" for value in values.values())}
    )
    """
                cur.execute(sql)
                con.commit()
        con.close()
    # except Exception as ex:
    #     send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', f'Ошибка в обработке emails в функции insert_into_firebird(emails): {email_data["sender"]=} {email_data["recipient"]=} {ex=}')
    #     print(f'Ошибка в обработке emails в функции insert_into_firebird(emails): {ex}')


def fetch_emails():
    # try:
        for user in get_users_with_email_pass():
            EMAIL_ACCOUNT = user[0]
            EMAIL_PASSWORD = user[1]
            FIO = user[2]
            # Подключение к IMAP серверу
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            status, folders = mail.list()
            print(f'folders: {folders}')
            # folders = ['zel услуги']
            emails = []
            for folder in folders:
                folder_info = folder.decode().split(' "/" ')
                folder_name = folder_info[1].strip('"') if len(folder_info) > 1 else folder_info[0].strip('"')
                folder_name = f'"{folder_name}"'
                print(f'{folder=} {folder.decode()=} {folder_name=}')
                if 'inbox' in folder.decode().lower() or 'sent' in folder.decode().lower():
                    if 'inbox' in folder.decode().lower():
                        folder_read_name = 'inbox'
                        folder_id_field = 'F5037'
                    if 'sent' in folder.decode().lower():
                        folder_read_name = 'sent'
                        folder_id_field = 'F5275'
                    print(f'{folder.decode().lower()=}')
                    print(f'__________________ОБРАБАТЫВАЕМ {folder_read_name}!___почты {EMAIL_ACCOUNT}_____________________')
                    mail.select(folder_name)
                    if get_max_msg_id_in_folder(folder_read_name, EMAIL_ACCOUNT) == None:
                        ID_LAST_MSG = 3
                    else:
                        ID_LAST_MSG = int(get_max_msg_id_in_folder(folder_read_name, EMAIL_ACCOUNT))
                    print(f'у аккаунта {EMAIL_ACCOUNT} в папке {folder_read_name} последний id письма:{ID_LAST_MSG=}')
                    # Формируем критерий поиска
                    date_criterion = '01-Sep-2024'
                    search_criterion = f'UID {ID_LAST_MSG - 2}:* SINCE "{date_criterion}"'
                    # Выполняем поиск писем
                    status, messages = mail.uid('SEARCH', None, search_criterion)
                    print(f'{status=}, {messages=}')
                    email_ids = messages[0].split()

                    # try:
                    for email_id in email_ids:
                        print(f'{email_id=}')
                        # status, message_data = mail.uid('FETCH', email_id, '(RFC822)') #закомментировал строчку чтобы письма делать снова НЕПРОЧИТАННЫМИ!
                        status, message_data = mail.uid('FETCH', email_id, '(BODY.PEEK[])')
                        raw_email = message_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        # print(f'msg={msg}')
                    
                        date_tuple = email.utils.parsedate_tz(msg["Date"])
                        local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                        if folder_read_name == 'inbox':
                            recipient = EMAIL_ACCOUNT
                        else:
                            recipient = ', '.join(extract_email(decode_header_value(msg["To"])))

                        if folder_read_name == 'sent':
                            sender = EMAIL_ACCOUNT
                        else:
                            sender = ', '.join(extract_email(decode_header_value(msg["From"])))

                        print(f'Получатель (возможно несколько получателей): {recipient}')
                        subject = decode_header_value(msg["Subject"])
                        body = get_letter_text(msg)
                        # print(f'body после get_letter_text: {body}')
                        body = normalize_whitespace(body)
                        # print(f'body после normalize_whitespace: {body}')
                        subject = subject.replace("'","")
                        print(f'{subject=}')
                        if not body:
                            body = "Текст в письме не найден"
                        attachments = get_attachments(msg)
                        print(f'{attachments=}')
                        if attachments:
                            download_folder = os.path.join(UPLOAD_DIR,FIO,folder_read_name,email_id.decode('utf-8'))
                        else:
                            download_folder = ''

                        email_data = {
                            "date": local_date.strftime("%Y-%m-%d"),
                            "time": local_date.strftime("%H:%M:%S"),
                            "sender": sender,
                            "recipient": recipient,
                            "subject": subject,
                            "body": body,
                            "folder_id_field": folder_id_field,
                            "email_id": email_id.decode('utf-8'),
                            "folder_name": folder_read_name,
                            "ID_LAST_MSG": ID_LAST_MSG,
                            "download_folder": download_folder,
                            "attachments": attachments,
                            "download_folder_2_db": os.path.join(UPLOAD_DIR_2_DB,FIO,folder_read_name,email_id.decode('utf-8'))
                        }
                        # print(f'{email_data=}')
                        print(f'{type(email_data["recipient"])}')
                        if check_availability_email(email_data["email_id"], email_data["folder_id_field"], email_data["sender"], email_data["subject"]) == 0: #если записи о таком письме еще нет в базе, то качаем вложения в письмо (при наличии) и записываем в базу
                            if email_data["attachments"]:
                                download_folder = os.path.join(UPLOAD_DIR,FIO,folder_read_name,email_id.decode('utf-8'))
                                print(f'{download_folder=}')
                                save_attachments(msg, download_folder)
                            else:
                                download_folder=''
                            insert_into_firebird(email_data)
                            # print(f'Пробуем сделать письмо НЕпрочитанным с id {email_id}')
                            # mail.store(email_id, '-FLAGS', '(\Seen)')
                            # print(f'Пробуем сделать письмо НЕпрочитанным с id {email_data["email_id"]}')
                            # mail.store(email_data["email_id"], '-FLAGS', '(\\Seen)')
                        else:
                            print(f'Такое письмо уже есть в базе: {email_data}')
                    # except Exception as ex:
                    #     send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', f'Ошибка при обработке письма(): {ex}')
                    #     print(f'Ошибка при обработке письма: {ex}')
                else:
                    print(f'___Не обрабатываем папку {folder_name}___')
            mail.close()
            mail.logout()
        return emails
    # except Exception as ex:
    #     try:
    #         sender_for_error = sender
    #     except:
    #         sender_for_error = None
    #     try:
    #         recipient_for_error = recipient
    #     except:
    #         recipient_for_error = None
    #     try:
    #         subject_for_error = subject
    #     except:
    #         subject_for_error = None
    #     send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', f'Ошибка в обработке emails в функции fetch_emails(): {sender_for_error=} {recipient_for_error=} {subject_for_error=} {ex=}')
    #     print(f'Ошибка в обработке emails в функции fetch_emails(): {ex}')


def job():
    print(f'Новая проверка')
    fetch_emails()
    print(f'Ждём одну минуту')


# Запустить задачу первый раз и потом каждую минуту
send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', f'Запуск emails_2_db')
job()
schedule.every(1).minutes.do(job)


while True:
    schedule.run_pending()
    time.sleep(1)

# send_message_to_channel('kbcyc66jbtbcubs93h43nf19dy', 'test', file_ids=['qmx5t9gemjf7bn75uzxe6hyqje'])
# print(upload_files_to_mattermost(['\\\\10.199.1.11\\РАБОТА\\10. Личные папки\\ФОС\\inbox\\3\\Счет № 1602 по договору 1988 от 19.07.2024[1].docx'],channel_id='kbcyc66jbtbcubs93h43nf19dy'))
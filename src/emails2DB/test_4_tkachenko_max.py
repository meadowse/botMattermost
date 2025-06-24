import imaplib
import email
from email.header import decode_header
from datetime import datetime
from bs4 import BeautifulSoup
import os
import re
import base64
import quopri

# Конфигурация IMAP
IMAP_SERVER = "imap.mail.ru"


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

def normalize_whitespace(text):
    if text:
        # Удаление лишних пробелов
        text = re.sub(r' +', ' ', text)
        # Удаление лишних переводов строки
        text = re.sub(r'\n+', '\n', text)
        return text
    else:
        return None


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

def get_attachments(msg):
    attachments = list()
    for part in msg.walk():
        if (
            part["Content-Type"]
            and "name" in part["Content-Type"]
            and part.get_content_disposition() == "attachment"
        ):
            filename = part.get_filename()
            if filename:
                # Decode the attachment name if needed
                print(f'{filename=}')
                filename = encode_att_names(filename)
                attachments.append(filename)
    return(attachments)


def get_letter_text(msg):
    def letter_type(part):
        # Функция для декодирования содержимого части письма
        charset = part.get_content_charset() or 'utf-8'
        return part.get_payload(decode=True).decode(charset, errors='ignore')

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
    

def fetch_emails():
    # try:
            EMAIL_ACCOUNT = 'm.tkachenko@mosproektkompleks.ru'
            EMAIL_PASSWORD = 's397bUsDZHqFFbQDvHQn'
            FIO = 'Ткаченко Максим Александрович'
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
                    ID_LAST_MSG = 3
                    print(f'у аккаунта {EMAIL_ACCOUNT} в папке {folder_read_name} последний id письма:{ID_LAST_MSG=}')
                    # Формируем критерий поиска
                    date_criterion = '01-Jan-2025'
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
                            # download_folder = os.path.join(UPLOAD_DIR,FIO,folder_read_name,email_id.decode('utf-8'))
                            download_folder = '1'
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
                            # "download_folder_2_db": os.path.join(UPLOAD_DIR_2_DB,FIO,folder_read_name,email_id.decode('utf-8'))
                        }
                        print(f'{email_data}')

            mail.close()
            mail.logout()

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

fetch_emails()
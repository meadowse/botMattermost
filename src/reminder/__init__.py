import firebirdsql
from datetime import timedelta, datetime
import requests
from config import MATTERMOST_URL, headers, headers_oko, host, database, user, password, charset, \
    webhook_host_url, webhook_host_port


def send_message_to_thread(channel_id, root_id, message, props={}):
    url = f'{MATTERMOST_URL}/api/v4/posts'
    payload = {
        'channel_id': channel_id,
        'root_id': root_id,
        'message': message
    }
    payload.update(props)
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print('Message sent to thread successfully.')
    else:
        print(f'Failed to send message to thread: {response.status_code}, {response.text}')


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

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        print('Message sent successfully.')
        return response.json()
    else:
        print(f'Failed to send message: {response.status_code}, {response.text}')


def send_message_to_oko(oko_channel_id, message, file_ids=None):
    url = f'{MATTERMOST_URL}/api/v4/posts'

    # Подготовка данных для сообщения
    payload = {
        'channel_id': oko_channel_id,
        'message': message
    }

    if file_ids:
        payload['file_ids'] = file_ids

    response = requests.post(url, json=payload, headers=headers_oko)

    if response.status_code == 201:
        print('Message sent successfully.')
        return response.json()
    else:
        print(f'Failed to send message: {response.status_code}, {response.text}')


def set_value_by_id(table, field, value, id):
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()
        if value != 'NULL':
            sql = f"UPDATE {table} SET {field} = '{value}' WHERE ID = '{id}'"
        else:
            sql = f"UPDATE {table} SET {field} = {value} WHERE ID = '{id}'"
        cur.execute(sql)
        con.commit()
        con.close()


def get_value_by_id(table, field, id):
    if id != '' and id != 'NULL':
        with firebirdsql.connect(host=host, database=database, user=user, password=password,
                                 charset=charset) as con:
            cur = con.cursor()
            sql = f"SELECT {field} FROM {table} WHERE ID = '{id}'"
            cur.execute(sql)
            result = cur.fetchone()
            return result
    else:
        return None


def get_value_by_value(table, need_value_field, had_value, had_value_field):
    print(table, need_value_field, had_value, had_value_field)
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()
        sql = f"SELECT {need_value_field} FROM {table} WHERE {had_value_field} = '{had_value}'"
        print(f'{sql=}')
        cur.execute(sql)
        result = cur.fetchone()
        return result


def f_num(number):
    if number is not None:
        if isinstance(number, float):
            integer_part, decimal_part = str(number).split('.')
            integer_part = '{:,}'.format(int(integer_part)).replace(',', ' ')
            result = f"{integer_part}.{decimal_part}"
        else:
            result = '{:,}'.format(int(number)).replace(',', ' ')
    else:
        result = '0'
    return result


# =================================== ПРОВЕРКА КП БЕЗ ОТВЕТА ===============================

def get_today_kp_reminders():
    today = datetime.today().strftime('%Y-%m-%d')
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()  # ID, № КП, message_id, дата отправки, id менеджера, дата напоминания, статус
        sql = f""" 
        SELECT ID, F4480, F4505, F4492, F4496, F4529, F4491 FROM T209 WHERE F4529 = '{today}' AND (F4491 = 'Отправлено' OR F4491 = 'Предварительное согласие')
        """
        cur.execute(sql)
        result = cur.fetchall()
        return result


def set_old_kp_reminders_for_today():
    today = datetime.today().strftime('%Y-%m-%d')
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()  # ID, № КП, message_id, дата отправки, id менеджера, дата напоминания, статус
        sql = f""" 
        SELECT ID, F4480, F4505, F4492, F4496, F4529, F4491 FROM T209 WHERE F4529 < '{today}' AND (F4491 = 'Отправлено' OR F4491 = 'Предварительное согласие')
        """
        cur.execute(sql)
        result = cur.fetchall()
        # Запрос на обновление
        if result:  # Проверяем, есть ли результаты для обновления
            ids_to_update = [row[0] for row in result]  # Предполагается, что ID находится в первом столбце
            ids_placeholder = ', '.join(['?'] * len(ids_to_update))  # Создаем плейсхолдеры для параметров

            sql_update = f"""
            UPDATE T209 
            SET F4529 = '{today}' 
            WHERE ID IN ({ids_placeholder})
            """
            cur.execute(sql_update, ids_to_update)  # Передаем список ID для обновления
        return result


def send_and_update_kp_reminders():
    set_old_kp_reminders_for_today()
    for i in get_today_kp_reminders():
        kp_id = i[0]
        kp_num = i[1]
        message_id = i[2]
        root_id = message_id.split('/')[-1]
        date_send = i[3]
        manager_id = i[4]
        date_remind = i[5]
        kp_status = i[6]
        new_date_remind = date_remind + timedelta(weeks=1)
        manager_nickname = get_value_by_id('T3', 'F4932', manager_id)[0]
        remind_message = f'По КП № {kp_num} наступила дата ожидаемого получения обратной связи, \n\
@{manager_nickname} Просьба связаться с Заказчиком и получить обратную связь по нашему КП'
        print(kp_id, kp_num, message_id, date_send, manager_id, date_remind, kp_status, new_date_remind,
              manager_nickname, root_id, remind_message)
        try:
            send_message_to_thread('kbcyc66jbtbcubs93h43nf19dy', root_id, remind_message)
            # Обновляем дату напоминания
            set_value_by_id('T209', 'F4529', new_date_remind, kp_id)
        except Exception as ex:
            send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy',
                                    f'Ошибка в направлении уведомлений о получении обратной связи: {kp_id, kp_num, message_id, date_send, manager_id, date_remind, kp_status, new_date_remind, manager_nickname, root_id, remind_message, ex}')
        print("Функция send_and_update_kp_reminders выполнена:", datetime.now())


# =========================================== ПРОВЕРКА НЕОПЛАЧЕННЫХ СЧЕТОВ И НЕПОДПИСАННЫХ ДОКУМЕНТОВ =======================================

def get_today_docs_reminders():
    today = datetime.today().strftime('%Y-%m-%d')
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()  # ID, id вида документа, № документа, сумма документа, тип документа, id Договора, id менеджера, nickname менеджера
        sql = f""" 
        SELECT T213.ID, T213.F4567, T216.F4674 AS doc, T213.F4568 AS doc_num, T213.F4571, T213.F4576, T213.F4573, 
               T212.F4844 , T3.F4932 AS manager_nickname, T213.F4928 AS message_id, T212.F4644, T213.F4666
        FROM T213 
        LEFT JOIN T216 ON T213.F4567 = T216.ID
        LEFT JOIN T212 ON T213.F4573 = T212.ID 
        LEFT JOIN T3 ON T212.F4844 = T3.ID 
        WHERE T213.F4666 = '{today}' AND T213.F4570 IS NULL
        """
        cur.execute(sql)
        result = cur.fetchall()
        return result


def get_today_task_reminders():
    today = datetime.today().strftime('%Y-%m-%d')
    print(f'Ищем задачи на сегодня {today}')
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()
        sql = f""" 
        SELECT 
        T218.ID AS ID,
        T218.F4695 AS TASK, 
        T3.F16 AS employe_id,
        T3.F5649 AS oko_channel_id,
        T212.F4538 AS contract_number,  -- Номер договора
        T212.F4946 AS contract_address,  -- Адрес договора
        T218.F4696 AS TASK_DATE, 
        T212.F4644 AS channel_id,  -- id MM канала
        T218.F5451 AS message_id  -- id сообщения задачи
        FROM T218 
        LEFT JOIN T3 ON T218.F4694 = T3.ID 
        LEFT JOIN T212 ON T218.F4691 = T212.ID  -- Присоединяем таблицу T212 по ID договора
        WHERE T218.F4970 <= '{today}' AND T218.F4697 = 0
        """
        cur.execute(sql)
        result = cur.fetchall()
        print(f'Что нашли: {result}')
        return result


def get_today_dr_reminders():
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()  # ID, id вида документа, № документа, сумма документа, тип документа, id Договора, id менеджера, nickname менеджера
        sql = f""" 
        SELECT 
        T3.F4886 AS NAME,
        T3.F18 AS DR_DATE 
        FROM T3 
        WHERE 
        (EXTRACT(MONTH FROM T3.F18) = EXTRACT(MONTH FROM CURRENT_DATE) AND 
        EXTRACT(DAY FROM T3.F18) = EXTRACT(DAY FROM CURRENT_DATE)) OR
        (EXTRACT(MONTH FROM T3.F18) = EXTRACT(MONTH FROM CURRENT_DATE) AND 
        EXTRACT(DAY FROM T3.F18) = EXTRACT(DAY FROM CURRENT_DATE) + 1) OR
        (EXTRACT(MONTH FROM T3.F18) = EXTRACT(MONTH FROM CURRENT_DATE) AND 
        EXTRACT(DAY FROM T3.F18) = EXTRACT(DAY FROM CURRENT_DATE) + 2) OR
        (EXTRACT(MONTH FROM T3.F18) = EXTRACT(MONTH FROM CURRENT_DATE) AND 
        EXTRACT(DAY FROM T3.F18) = EXTRACT(DAY FROM CURRENT_DATE) + 3) AND
        T3.F5383 = 1;
        """
        cur.execute(sql)
        result = cur.fetchall()
        return result


def set_old_docs_reminders_for_today():
    today = datetime.today().strftime('%Y-%m-%d')
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()  # ID, № КП, message_id, дата отправки, id менеджера, дата напоминания, статус
        sql = f""" 
        SELECT ID, F4567, F4568, F4571, F4576 FROM T213 WHERE F4666 < '{today}' AND F4570 IS NULL AND F4569 > '2024-08-01'
        """
        cur.execute(sql)
        result = cur.fetchall()
        # Запрос на обновление
        if result:  # Проверяем, есть ли результаты для обновления
            ids_to_update = [row[0] for row in result]  # Предполагается, что ID находится в первом столбце
            ids_placeholder = ', '.join(['?'] * len(ids_to_update))  # Создаем плейсхолдеры для параметров

            sql_update = f"""
            UPDATE T213 
            SET F4666 = '{today}' 
            WHERE ID IN ({ids_placeholder})
            """
            cur.execute(sql_update, ids_to_update)  # Передаем список ID для обновления
        return result


def send_and_update_docs_reminders():  # must
    set_old_docs_reminders_for_today()
    for i in get_today_docs_reminders():
        doc_id = i[0]
        doc_name = i[2]
        doc_num = i[3]
        doc_sum = i[4]
        doc_type = i[5]
        manager_nickname = i[8]
        message_id = i[9]
        channel_id = i[10]
        date_remind = i[11]
        new_date_remind = date_remind + timedelta(weeks=1)
        print(doc_id, doc_name, doc_num, doc_sum, doc_type, manager_nickname, message_id, channel_id)
        remind_message = f'У документа № {doc_num} ({doc_name} {doc_type}) на сумму {f_num(doc_sum)} р. наступила дата ожидаемой оплаты/подписания, \n\
@{manager_nickname} Просьба связаться с Заказчиком и узнать когда оплатят/подпишут'
        props = {
            "props": {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "underApproval",
                                "name": ":memo: На согласовании",
                                "integration": {
                                    "url": f"{webhook_host_url}:{webhook_host_port}/"
                                           "hooks/underApproval",
                                    "context": dict(
                                        text=":memo: На согласовании",
                                        message=remind_message,
                                        manager_nickname=manager_nickname,
                                    )
                                },
                            },
                            {
                                "id": "couldNotGetInTouch",
                                "name": ":shrug: Не удалось связаться",
                                "integration": {
                                    "url": f"{webhook_host_url}:{webhook_host_port}/"
                                           "hooks/couldNotGetInTouch",
                                    "context": dict(
                                        text=":shrug: Не удалось связаться",
                                        message=remind_message,
                                        manager_nickname=manager_nickname,
                                    )
                                },
                            },
                            {
                                "id": "cancel",
                                "name": ":x: Аннулировать",
                                "integration": {
                                    "url": f"{webhook_host_url}:{webhook_host_port}/"
                                           "hooks/cancel",
                                    "context": dict(
                                        text=":x: Аннулировать",
                                        message=remind_message,
                                        doc_id=doc_id,
                                        manager_nickname=manager_nickname,
                                    )
                                },
                            },
                        ],
                    }
                ]
            }
        }
        if message_id and channel_id:
            try:
                send_message_to_thread(channel_id, message_id, remind_message, props)
                # Обновляем дату напоминания
                set_value_by_id('T213', 'F4666', new_date_remind, doc_id)
            except Exception as ex:
                send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy',
                                        f'Ошибка в направлении уведомлений в тред о непобходимости подписания/оплаты договорных документов: {doc_id, doc_name, doc_num, doc_sum, doc_type, manager_nickname, message_id, channel_id, remind_message}')
        elif message_id is None and channel_id:
            try:
                send_message_to_channel(channel_id, remind_message, None, props)
                # Обновляем дату напоминания
                set_value_by_id('T213', 'F4666', new_date_remind, doc_id)
            except Exception as ex:
                send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy',
                                        f'Ошибка в направлении уведомлений в канал о непобходимости подписания/оплаты договорных документов: {doc_id, doc_name, doc_num, doc_sum, doc_type, manager_nickname, message_id, channel_id, remind_message}')
        else:
            send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy',
                                    f'Не нашлось ни сообщения ни канала чтобы получить обратную связь по подписанию/оплате по документу: {doc_id, doc_name, doc_num, doc_sum, doc_type, manager_nickname, message_id, channel_id, remind_message}')
        print("Функция send_and_update_docs_reminders выполнена:", datetime.now())

# ============================================= Напоминания о простановке приоритета у лида ===================================

def get_empty_priority_reminders():
    today = datetime.today().strftime('%Y-%m-%d')
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()  # ID, № лида, id менеджера, nickname менеджера, message_id
        sql = f""" 
        SELECT T208.ID, T208.F4450, T208.F4446 AS message_id, T3.F4932 AS manager_nickname, T208.F4964 AS message_id
        FROM T208 
        LEFT JOIN T3 ON T208.F4446 = T3.ID 
        WHERE T208.F5501 IS NULL AND T208.F4454 = 'Целевой' AND T208.F4442 > '2024-09-30'
        """
        cur.execute(sql)
        result = cur.fetchall()
        return result


def send_empty_priority_reminders():
    for i in get_empty_priority_reminders():
        lead_id = i[0]
        lead_num = i[1]
        manager_nickname = i[3]
        message_id = i[4]
        remind_message = f' @{manager_nickname} у Лида № {lead_num} нужно проставить Приоритет'
        # print(f'{lead_num=} {message_id=} {manager_nickname=}')
        send_message_to_thread('kbcyc66jbtbcubs93h43nf19dy', message_id, remind_message)


def get_info_about_channels():
    with firebirdsql.connect(host=host, database=database, user=user, password=password,
                             charset=charset) as con:
        cur = con.cursor()
        sql = f"""
        SELECT ID, 
        F4544 as stadia, 
        F4946 as address, 
        F4538 as dog_num, 
        F4603 as subject, 
        F4541 as price, 
        F4563 as avans, 
        F4542 as oplacheno,
        F4644 as channel_id
        FROM T212 WHERE F4644 IS NOT NULL
        """
        cur.execute(sql)
        result = cur.fetchall()
        return result


def update_channel(channel_id, header, purpose):
    url = f'{MATTERMOST_URL}/api/v4/channels/{channel_id}/patch'
    payload = {
        'header': header,
        'purpose': purpose
    }
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 200:
        print('Channel header and purpose updated successfully.')
    else:
        print(f'Failed to update channel: {response.status_code}, {response.text}')


def update_channels():
    k = 0
    for i in get_info_about_channels():
        k += 1
        dog_id = i[0]
        stadia = i[1]

        address = i[2]
        dog_num = i[3]
        subject = i[4]
        price = i[5]
        avans = i[6]
        oplacheno = i[7]
        channel_id = i[8]
        print(
            f'{k}, {dog_id=}, {stadia=}, {address=}, {dog_num=}, {subject=}, {price=}, {avans=}, {oplacheno=}, {channel_id=}')
        print(f'-------')

        # формируем header

        # if stadia == 'В работе':
        #     emo_header = ':construction_worker:'
        # elif stadia == 'Работа завершена':
        #     emo_header = ':checkered_flag:'
        # elif stadia == 'Аннулировано' or stadia == 'Отменена' :
        #     emo_header = ':no_entry:'
        # else:
        #     emo_header = ''

        if stadia != None and stadia != '':
            print(f'{stadia=}')
            emo_header = get_value_by_value('T298', 'F5648', stadia, 'F5534')[0]
            print(f'{emo_header=}')

            stadia = '**' + stadia + '**'
        else:
            stadia = ''
            emo_header = ''

        subject = str(subject)
        if subject == 'None':
            subject = ''
        # address = str(address)
        # if subject == None or address not in subject:
        #     address_2_mm = address
        # else:
        #     address_2_mm = ''
        # if address_2_mm == 'None':
        #     address_2_mm = ''

        # header = f'{emo_header}{stadia}{emo_header}// {subject} // {address_2_mm}'
        header = f'{emo_header} {stadia} {emo_header} // {subject}'

        # формируем purpose
        try:
            doc_osnov = get_value_by_id('T212', 'F4667', dog_id)[0]
        except Exception as ex:
            print(f'Не нашел документ основания из-за ошибки: {ex}')
            doc_osnov = ''
        if oplacheno == price and price > 0:
            emo_purpose = '🟢'
        elif oplacheno >= avans:
            emo_purpose = '🟡'
        elif oplacheno == 0 and price > 0:
            emo_purpose = '🔴'
        else:
            emo_purpose = ''
        purpose = f'{emo_purpose}Цена: *{f_num(price)} руб.* {emo_purpose}Аванс: *{f_num(avans)} руб.* {emo_purpose}Оплачено: *{f_num(oplacheno)} руб.* Документ-основание: {doc_osnov}'

        print(f'{header=}, {purpose=}')
        update_channel(channel_id, header, purpose)
        print('============================================================')


# ============================================= Напоминания о задачах ===================================

def send_task_reminders():
    today = datetime.today().strftime('%Y-%m-%d')  # Сегодняшняя дата в формате строки
    for i in get_today_task_reminders():
        task_id = i[0]
        task = i[1]
        employe_id = i[2]
        oko_channel_id = i[3]
        dog_num = i[4]
        dog_address = i[5]
        task_date = i[6]
        channel_id = i[7]
        message_id = i[8]

        print(f'{task=}, {employe_id=}, {oko_channel_id=}, {dog_num=}, {dog_address=}, {task_date=}, {channel_id=}')

        # Проверка на None
        if task_date is None:
            print(f"Задача {task_id} не имеет даты выполнения. Пропускаем.")
            continue

        # Преобразуем task_date в строку для сравнения
        task_date_str = task_date.strftime('%Y-%m-%d')
        message = '=============\n'
        if task_date_str < today:
            message += f'Просрочена задача: ***{task}*** '
        else:
            message += f'Наступила дата выполнения задачи: ***{task}*** '

        if dog_num is not None:
            if channel_id is not None:
                message += f'по договору № [{dog_num}](https://mm-mpk.ru/mosproektkompleks/channels/{channel_id}) '
            else:
                message += f'по договору № {dog_num} '
        if dog_address is not None:
            message += f'адрес в договоре: {dog_address}'
        if message_id is not None:
            message += f', [обсуждение задачи](https://mm-mpk.ru/mosproektkompleks/pl/{message_id})'

        send_message_to_oko(oko_channel_id, message)


# ============================================= Напоминания о ДР ===================================
def age_in_years(age):
    if age % 10 == 1 and age % 100 != 11:
        return f"{age} год"
    elif age % 10 in [2, 3, 4] and age % 100 not in [12, 13, 14]:
        return f"{age} года"
    else:
        return f"{age} лет"


def send_dr_reminders():
    for i in get_today_dr_reminders():
        name = i[0]
        dr_date = i[1]
        age = datetime.now().year - dr_date.year
        message = f"Напоминание о дне рождении: {name}, {age_in_years(age)}, день рождения {dr_date}."
        print(message)
        send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', message)  # отправка БАИ
        send_message_to_channel('emsxtq83jpnq8yp6gpcqfiw7ke', message)  # отправка Римме Хасановой
        send_message_to_channel('f3d7amu5m7nqdcc4k34j48p61h', message)  # отправка Екатерине Малашенко
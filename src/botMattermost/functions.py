import datetime
import firebirdsql
import config


def set_value_by_id(table, field, value, Id):
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password,
                             charset=config.charset) as con:
        cur = con.cursor()
        if value != 'NULL':
            sql = f"UPDATE {table} SET {field} = '{value}' WHERE ID = '{Id}'"
        else:
            sql = f"UPDATE {table} SET {field} = {value} WHERE ID = '{Id}'"
        cur.execute(sql)
        con.commit()
        con.close()

def editMessage(replyId, cur):
    cur.execute(f"""SELECT ID AS id,
    F4695 AS task,
    F4698 AS comment,
    F5569 AS dateStart,
    F4696 AS deadline,
    F4697 AS done,
    F4708 AS today,
    F4693 AS directorId,
    F4694 AS executorId,
    F5872 AS status,
    F5889 AS plannedTimeCosts FROM T218 WHERE F5451 = '{replyId}'""")
    taskData = cur.fetchone()
    columns = ('id', 'task', 'comment', 'dateStart', 'deadline', 'done', 'today', 'directorId', 'executorId', 'status',
               'plannedTimeCosts')
    jsonResult = {col: value for col, value in zip(columns, taskData)}
    sql = f"SELECT F4932 FROM T3 WHERE ID = {jsonResult.get('directorId')}"
    cur.execute(sql)
    director = cur.fetchone()[0]
    sql = f"SELECT F4932 FROM T3 WHERE ID = {jsonResult.get('executorId')}"
    cur.execute(sql)
    executor = cur.fetchone()[0]
    done = jsonResult.get('done')
    message = f"**{'Изменена' if done != 1 else 'Завершена'} :hammer_and_wrench: Задача :hammer_and_wrench: by @{director}**\n"
    message += f"Дата добавления: *{jsonResult.get('dateStart')}*\n"
    message += f"Постановщик: *@{director}*\n"
    message += f"Исполнитель: *@{executor}*\n"
    message += f"Задача: :hammer: *{jsonResult.get('task')}*\n"
    message += f"Deadline: :calendar: *{jsonResult.get('deadline')}*\n"
    comment = jsonResult.get('comment')
    if comment != '' and comment is not None:
        message += f"Комментарий: :speech_balloon: *{comment}*\n"
    plannedTimeCosts = jsonResult.get('plannedTimeCosts')
    if plannedTimeCosts is not None:
        message += f"Планируемые времязатраты: :clock3: *{jsonResult.get('plannedTimeCosts')}ч.*\n"
    sql = f"SELECT SUM(F5882) FROM T320 WHERE F5862 = {jsonResult.get('id')}"
    cur.execute(sql)
    currentTimeCosts = cur.fetchone()[0]
    if currentTimeCosts is not None:
        message += f"Текущие времязатраты: :clock3: *{currentTimeCosts}ч.*\n"
    statusEmoji = ''
    status = jsonResult.get('status')
    match status:
        case 'Новая':
            statusEmoji = ':new:'
        case 'В работе':
            statusEmoji = ':molot:'
        case 'Выполненная':
            statusEmoji = ':white_check_mark:'
        case 'Завершенная':
            statusEmoji = ':thumbsup:'
        case 'Отмененная':
            statusEmoji = ':x:'
    message += f"Статус: {statusEmoji} *{status}* {statusEmoji}\n"
    message += ":large_yellow_circle: *Задача ожидает завершения...*" if done != 1 else f":large_green_circle: *Задача завершена {jsonResult.get('today')}*"
    return message

def add_LEAD(message_id, user_db_id):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    current_year = datetime.datetime.now().year
    message_link = config.MATTERMOST_URL + '/mosproektkompleks/pl/' + message_id
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password, charset=config.charset) as con:
        cur = con.cursor()
        Sql = f"SELECT ID FROM T3 WHERE F16 = '{user_db_id}'"
        cur.execute(Sql)
        userData = cur.fetchone()
        userId = userData[0]
        sql_count_of_lead = f"SELECT COUNT(*) FROM T208 WHERE T208.F4452 = {current_year}"
        cur.execute(sql_count_of_lead)
        count_of_lead = cur.fetchall()[0][0]
        print(count_of_lead)
        lead_num = str(current_year) + '-' + str(int(count_of_lead) + 1) + 'Л'
        path_of_lead = 'N:\\1. Лиды\\'+str(current_year)+'\\'+lead_num
        print(lead_num)
        print(path_of_lead)
        cur.execute(f'SELECT GEN_ID(GEN_T208, 1) FROM RDB$DATABASE')
        ID = cur.fetchonemap().get('GEN_ID', None)
        values = {'id': ID,
                  'F4452': current_year, #год добавления КП
                  'F4442': current_date, #дата добавления КП
                  'F4443': current_time, #время добавления КП
                  'F4450': lead_num,
                  'F4458': message_link,
                  'F4446': userId,
                  'F5006': path_of_lead,
                  'F4477': 'напоминать Исп.',
                  'F4964': message_id, }
        sql = f"""INSERT INTO T208 ({', '.join(values.keys())}) VALUES ({', '.join(f"'{value}'" for value in values.values())})"""
        cur.execute(sql)
        con.commit()
        con.close()
        return lead_num


def add_KP(message_id, user_db_id):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.datetime.now().year
    message_link = config.MATTERMOST_URL + '/mosproektkompleks/pl/' + message_id
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password,
                             charset=config.charset) as con:
        cur = con.cursor()
        Sql = f"SELECT ID, F4887SRC, F4887DEST FROM T3 WHERE F16 = '{user_db_id}'"
        cur.execute(Sql)
        userData = cur.fetchone()
        userId = userData[0]
        src = userData[1]
        dest = userData[2]
        sql_count_of_kp = f"SELECT COUNT(*) FROM T209 WHERE T209.F4500 = {current_year}"
        cur.execute(sql_count_of_kp)
        count_of_kp = cur.fetchall()[0][0]
        print(count_of_kp)
        kp_num = str(current_year) + '-' + str(int(count_of_kp) + 1) + 'КП'
        path_of_kp = 'N:\\2. КП\\' + str(current_year) + '\\' + kp_num
        print(kp_num)
        print(path_of_kp)
        cur.execute(f'SELECT GEN_ID(GEN_T209, 1) FROM RDB$DATABASE')
        Id = cur.fetchonemap().get('GEN_ID', None)
        values = {'id': Id,
                  'F4490': Id,
                  'F4500': current_year,  # год добавления КП
                  'F4511': current_date,  # дата добавления КП
                  'F4485': current_date,  # дата КП
                  'F4480': kp_num,
                  'F4491': 'В процессе подготовки',
                  'F4505': message_link,
                  'F4496': userId,
                  'F4527': path_of_kp,
                  'F4528': 'напоминать Исп.',
                  'F4512': message_id,
                  'F4483': 'выполнение работ по ... (далее Объект(ы))',  # предмет работ
                  'F4484': 0,  # цена работ
                  'F4488': 0,  # срок работ
                  'F4503': 1,
                  'F4888SRC': src,
                  'F4888DEST': dest, }
        sql = f"""INSERT INTO T209 ({', '.join(values.keys())}) VALUES ({', '.join(f"'{value}'" for value in values.values())})"""
        cur.execute(sql)
        con.commit()
        con.close()
        return kp_num
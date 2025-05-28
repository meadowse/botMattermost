import schedule
from datetime import datetime
import time
from __init__ import send_and_update_kp_reminders, send_and_update_docs_reminders, send_empty_priority_reminders, \
    update_channels, send_task_reminders, send_dr_reminders, send_message_to_channel, isp_srok_reminder, check_all_employee_and_add_oko_id

# Запланируем выполнение функции по напоминаниям о задачах в 07:00 по будням
schedule.every().monday.at("07:00").do(check_all_employee_and_add_oko_id)
schedule.every().tuesday.at("07:00").do(check_all_employee_and_add_oko_id)
schedule.every().wednesday.at("07:00").do(check_all_employee_and_add_oko_id)
schedule.every().thursday.at("07:00").do(check_all_employee_and_add_oko_id)
schedule.every().friday.at("07:00").do(check_all_employee_and_add_oko_id)


# Запланируем выполнение функции по напоминаниям о задачах в 09:10 по будням
schedule.every().monday.at("09:10").do(send_task_reminders)
schedule.every().tuesday.at("09:10").do(send_task_reminders)
schedule.every().wednesday.at("09:10").do(send_task_reminders)
schedule.every().thursday.at("09:10").do(send_task_reminders)
schedule.every().friday.at("09:10").do(send_task_reminders)

# Запланируем выполнение функции по напоминаниям о ДР в 09:20 каждый день
schedule.every().monday.at("09:20").do(send_dr_reminders)
schedule.every().tuesday.at("09:20").do(send_dr_reminders)
schedule.every().wednesday.at("09:20").do(send_dr_reminders)
schedule.every().thursday.at("09:20").do(send_dr_reminders)
schedule.every().friday.at("09:20").do(send_dr_reminders)
schedule.every().saturday.at("09:20").do(send_dr_reminders)
schedule.every().sunday.at("09:20").do(send_dr_reminders)

# Запланируем выполнение функции по КП в 10:00 по будням
schedule.every().monday.at("10:00").do(send_and_update_kp_reminders)
schedule.every().tuesday.at("10:00").do(send_and_update_kp_reminders)
schedule.every().wednesday.at("10:00").do(send_and_update_kp_reminders)
schedule.every().thursday.at("10:00").do(send_and_update_kp_reminders)
schedule.every().friday.at("10:00").do(send_and_update_kp_reminders)

# Запланируем выполнение функции по договорным документам в 10:15 по будням
schedule.every().monday.at("10:15").do(send_and_update_docs_reminders)
schedule.every().tuesday.at("10:15").do(send_and_update_docs_reminders)
schedule.every().wednesday.at("10:15").do(send_and_update_docs_reminders)
schedule.every().thursday.at("10:15").do(send_and_update_docs_reminders)
schedule.every().friday.at("10:15").do(send_and_update_docs_reminders)

# Запланируем выполнение функции напоминания о скором завершении испытательного срока в 10:30 по будням
schedule.every().monday.at("10:30").do(isp_srok_reminder)
schedule.every().tuesday.at("10:30").do(isp_srok_reminder)
schedule.every().wednesday.at("10:30").do(isp_srok_reminder)
schedule.every().thursday.at("10:30").do(isp_srok_reminder)
schedule.every().friday.at("10:30").do(isp_srok_reminder)

# Запланируем выполнение функции по приоритетам лидов в 12:00 по будням
schedule.every().monday.at("12:00").do(send_empty_priority_reminders)
schedule.every().tuesday.at("12:00").do(send_empty_priority_reminders)
schedule.every().wednesday.at("12:00").do(send_empty_priority_reminders)
schedule.every().thursday.at("12:00").do(send_empty_priority_reminders)
schedule.every().friday.at("12:00").do(send_empty_priority_reminders)

# Запланируем выполнение функции по обновлениям каналов в 03:00 по будням
schedule.every().monday.at("03:00").do(update_channels)
schedule.every().tuesday.at("03:00").do(update_channels)
schedule.every().wednesday.at("03:00").do(update_channels)
schedule.every().thursday.at("03:00").do(update_channels)
schedule.every().friday.at("03:00").do(update_channels)

# emo_header = get_value_by_value('T298','F5648','Успех','F5534')[0]
# print(f'{emo_header=}')

send_message_to_channel('nf5xrwor7fgwpfoorp1g97ufoy', f'{datetime.now()} Процесс reminder запущен')
print(f'{datetime.now()} Процесс reminder запущен')
# send_dr_reminders()
# update_channels()
# send_task_reminders()

while True:
    print(f'{datetime.now()} Проверяем, есть ли запланированные задачи...')
    schedule.run_pending()  # Проверяем, есть ли запланированные задачи
    time.sleep(60)  # Пауза в 60 секунд
import re
import firebirdsql
import config

def extract_account_number(text):
    """
    Extracts the account number from the given text.

    Args:
        text (str): The input text containing the account number.

    Returns:
        str or None: The extracted account number if found, otherwise None.
    """
    match = re.search(r'сч[её]ту\s*№\s*(\d+-\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

# Example usage
# text = 'Вы получили оплату по счёту № 1039071-16 l ООО "МОСПРОЕКТКОМПЛЕКС"'
# account_number = extract_account_number(text)
# print(account_number)  # Output: 1039071-16


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
    
get_thread_id_and_channdel_id('1039071-16')
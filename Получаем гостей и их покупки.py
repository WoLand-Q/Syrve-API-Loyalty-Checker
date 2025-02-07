import requests
import json
import random
import datetime
import sys
import time
import codecs

# Конфигурационные данные
SYRVE_CLOUD_URL = 'https://api-eu.syrve.live'
SYRVE_CLOUD_API_LOGIN = ''  # Ваш API логин
ORGANIZATION_ID = ''
PHONE = "+"

# Функция для логирования
def log(log_text):
    with open('logs.txt', 'a', encoding='UTF-8') as file:
        file.write(f'[{time.strftime("%Y-%m-%d %H:%M")}] {log_text}\n')
    return True


class IikoCloudLoyalty:
    def __init__(self, base_url, api_login, organization_id, timeout=15):
        self.base_url = base_url
        self.api_login = api_login.strip()
        self.organization_id = organization_id
        self.timeout = timeout
        self.token = self.get_access_token()

    def get_access_token(self):
        url = f"{self.base_url}/api/1/access_token"
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
        payload = {
            "apiLogin": self.api_login
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            print(f"Отправка запроса на получение токена: {url}")
            print(f"Тело запроса: {json.dumps(payload, ensure_ascii=False)}")
            response.raise_for_status()
            data = response.json()
            access_token = data.get("token")
            if access_token:
                print(f"\n[+] Access Token успешно получен: {access_token}\n")
                log(f"Access Token получен: {access_token}")
                return access_token
            else:
                print("[-] Токен не найден в ответе сервера.")
                log("Токен не найден в ответе сервера.")
        except requests.exceptions.HTTPError as http_err:
            print(f"[-] HTTP ошибка при получении токена: {http_err} - Ответ сервера: {response.text}")
            log(f"HTTP ошибка при получении токена: {http_err} - Ответ сервера: {response.text}")
        except requests.exceptions.Timeout:
            print("[-] Превышено время ожидания при получении токена.")
            log("Превышено время ожидания при получении токена.")
        except Exception as err:
            print(f"[-] Ошибка при получении токена: {err}")
            log(f"Ошибка при получении токена: {err}")
        return None

    def get_customer_info(self, phone):
        url = f"{self.base_url}/api/1/loyalty/iiko/customer/info"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
        payload = {
            "phone": phone,
            "type": "phone",
            "organizationId": self.organization_id
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            print(f"Отправка запроса на получение информации о клиенте: {url}")
            print(f"Тело запроса: {json.dumps(payload, ensure_ascii=False)}")
            response.raise_for_status()
            customer_info = response.json()
            print("[+] Информация о клиенте успешно получена.\n")
            log(f"Информация о клиенте получена для телефона: {phone}")
            return customer_info
        except requests.exceptions.HTTPError as http_err:
            print(f"[-] HTTP ошибка при получении информации о клиенте: {http_err} - Ответ сервера: {response.text}")
            log(f"HTTP ошибка при получении информации о клиенте: {http_err} - Ответ сервера: {response.text}")
        except requests.exceptions.Timeout:
            print("[-] Превышено время ожидания при получении информации о клиенте.")
            log("Превышено время ожидания при получении информации о клиенте.")
        except json.JSONDecodeError:
            print("[-] Ошибка декодирования JSON при получении информации о клиенте. Ответ сервера:")
            print(response.text)
            log("Ошибка декодирования JSON при получении информации о клиенте.")
            log(response.text)
        except Exception as err:
            print(f"[-] Ошибка при получении информации о клиенте: {err}")
            log(f"Ошибка при получении информации о клиенте: {err}")
        return None

    def get_transactions_by_revision(self, customer_id, revision=0, last_transaction_id=None, page_number=1, page_size=100):
        url = f"{self.base_url}/api/1/loyalty/iiko/customer/transactions/by_revision"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
        payload = {
            "customerId": customer_id,
            "pageNumber": page_number,
            "pageSize": page_size,
            "organizationId": self.organization_id
        }

        if last_transaction_id:
            payload["revision"] = revision
            payload["lastTransactionId"] = last_transaction_id

        # Валидация pageSize
        if page_size < 1:
            print("[-] Некорректное значение pageSize. Оно должно быть не меньше 1.")
            log("Некорректное значение pageSize. Оно должно быть не меньше 1.")
            return []

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            print(f"Отправка запроса на получение транзакций по ревизии: {url}")
            print(f"Тело запроса: {json.dumps(payload, ensure_ascii=False)}")
            response.raise_for_status()
            data = response.json()

            transactions = data.get("transactions", [])
            # Фильтрация транзакций (можно настроить по необходимости)
            valid_transactions = [
                t for t in transactions
                if not t.get("isIgnored", False) and t.get("isDelivery", False)
            ]

            # Получение последней ревизии и ID транзакции
            last_revision = data.get("lastRevision", revision)
            last_transaction_id = data.get("lastTransactionId", last_transaction_id)

            print("[+] Транзакции клиента успешно получены.\n")
            log(f"Транзакции получены для клиента ID: {customer_id} за ревизию: {revision}")
            print(f"Получено транзакций (не игнорируемых и доставки): {len(valid_transactions)}")
            return valid_transactions
        except requests.exceptions.HTTPError as http_err:
            print(f"[-] HTTP ошибка при получении транзакций по ревизии: {http_err} - Ответ сервера: {response.text}")
            log(f"HTTP ошибка при получении транзакций по ревизии: {http_err} - Ответ сервера: {response.text}")
        except requests.exceptions.Timeout:
            print("[-] Превышено время ожидания при получении транзакций по ревизии.")
            log("Превышено время ожидания при получении транзакций по ревизии.")
        except json.JSONDecodeError:
            print("[-] Ошибка декодирования JSON при получении транзакций по ревизии. Ответ сервера:")
            print(response.text)
            log("Ошибка декодирования JSON при получении транзакций по ревизии.")
            log(response.text)
        except Exception as err:
            print(f"[-] Ошибка при получении транзакций по ревизии: {err}")
            log(f"Ошибка при получении транзакций по ревизии: {err}")
        return []

    def is_new_customer(self, transactions, brand_id):
        for transaction in transactions:
            if transaction.get('brandId') == brand_id:
                print(f"[-] Клиент не является новым по бренду {brand_id}.")
                log(f"Клиент не является новым по бренду {brand_id}.")
                return False
        print(f"[+] Клиент является новым по бренду {brand_id}.")
        log(f"Клиент является новым по бренду {brand_id}.")
        return True

    def display_customer_info(self, customer_info):
        print("=== Информация о Клиенте ===")
        print(f"ID: {customer_info.get('id', 'N/A')}")
        print(f"Имя: {customer_info.get('name', 'N/A')}")
        print(f"Фамилия: {customer_info.get('surname', 'N/A')}")
        print(f"Отчество: {customer_info.get('middleName', 'N/A')}")
        print(f"Телефон: {customer_info.get('phone', 'N/A')}")
        print(f"Email: {customer_info.get('email', 'N/A')}")
        print(f"Комментарий: {customer_info.get('comment', 'N/A')}")
        print(f"Дата регистрации: {customer_info.get('whenRegistered', 'N/A')}")
        consent_from = customer_info.get('personalDataConsentFrom', 'N/A')
        consent_to = customer_info.get('personalDataConsentTo', 'N/A')
        print(f"Дата согласия на обработку данных: {consent_from} до {consent_to}")
        print("==============================\n")

    def display_transactions(self, transactions):
        print("=== Транзакции Клиента ===")
        if not transactions:
            print("Транзакций не найдено.\n")
            return
        for idx, transaction in enumerate(transactions, start=1):
            print(f"--- Транзакция {idx} ---")
            print(f"ID транзакции: {transaction.get('id', 'N/A')}")
            print(f"ID бренда: {transaction.get('programId', 'N/A')}")
            print(f"Дата: {transaction.get('whenCreated', 'N/A')}")
            print(f"Сумма: {transaction.get('sum', 'N/A')}")
            print(f"Тип: {transaction.get('typeName', 'N/A')}")
            print("Детали:")
            details = transaction.get('comment', 'N/A')
            print(details)
            print("-------------------------\n")
        print("============================\n")

# Функция для генерации уникального промокода
def create_new_coupon(prefix, brand, existing_coupons):
    while True:
        code = str(random.randint(10000, 99999))
        coupon = f"{prefix}{code}{brand}"
        if coupon not in existing_coupons:
            return coupon

# Функция для загрузки существующих промокодов из файла
def load_existing_coupons(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"[-] Ошибка при загрузке существующих купонов: {e}")
        log(f"Ошибка при загрузке существующих купонов: {e}")
        return []

# Функция для сохранения нового промокода в файл
def save_new_coupon(file_path, coupon):
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{coupon}\n")
        print(f"[+] Промокод {coupon} успешно сохранён в {file_path}")
        log(f"Промокод {coupon} успешно сохранён в {file_path}")
    except Exception as e:
        print(f"[-] Ошибка при сохранении нового купона: {e}")
        log(f"Ошибка при сохранении нового купона: {e}")

# Основной процесс
def main():
    organization_id = ORGANIZATION_ID
    phone = PHONE

    # Инициализация iiko Cloud Loyalty API
    loyalty_api = IikoCloudLoyalty(
        base_url=SYRVE_CLOUD_URL,
        api_login=SYRVE_CLOUD_API_LOGIN,
        organization_id=organization_id
    )

    if not loyalty_api.token:
        print("[-] Не удалось получить токен доступа. Завершение скрипта.")
        log("Не удалось получить токен доступа. Скрипт завершен.")
        return

    # Получение информации о клиенте
    customer_info = loyalty_api.get_customer_info(phone)
    if not customer_info:
        print("[-] Не удалось получить информацию о клиенте. Завершение скрипта.")
        log("Не удалось получить информацию о клиенте. Скрипт завершен.")
        return

    # Красивый вывод информации о клиенте
    loyalty_api.display_customer_info(customer_info)

    customer_id = customer_info.get("id")
    if not customer_id:
        print("[-] Не найден ID клиента. Завершение скрипта.")
        log("Не найден ID клиента. Скрипт завершен.")
        return

    # Запрос на использование автоматического или ручного ввода customerId
    use_manual_id = input("Хотите ввести свой customerId вручную? (да/нет): ").strip().lower()
    if use_manual_id in ['да', 'д', 'yes', 'y']:
        manual_customer_id = input("Введите customerId: ").strip()
        if manual_customer_id:
            customer_id = manual_customer_id
            print(f"[+] Используется введённый customerId: {customer_id}")
            log(f"Используется введённый customerId: {customer_id}")
        else:
            print("[-] Введён пустой customerId. Используется автоматический.")
            log("Введён пустой customerId. Используется автоматический.")
    else:
        print(f"[+] Используется автоматический customerId: {customer_id}")
        log(f"Используется автоматический customerId: {customer_id}")

    # Запрос на ввод ревизии или использование автоматической
    use_manual_revision = input("Хотите ввести свою ревизию вручную? (да/нет): ").strip().lower()
    if use_manual_revision in ['да', 'д', 'yes', 'y']:
        manual_revision_input = input("Введите ревизию (целое число): ").strip()
        try:
            revision = int(manual_revision_input)
            if revision < 0:
                raise ValueError("Ревизия не может быть отрицательной.")
            print(f"[+] Используется введённая ревизия: {revision}")
            log(f"Используется введённая ревизия: {revision}")
        except ValueError as ve:
            print(f"[-] Некорректный ввод ревизии: {ve}. Используется ревизия 0.")
            log(f"Некорректный ввод ревизии: {ve}. Используется ревизия 0.")
            revision = 0
    else:
        print("[+] Используется ревизия 0.")
        log("Используется ревизия 0.")
        revision = 0

    # Запрос на ввод lastTransactionId или использование автоматического
    use_manual_last_transaction_id = input("Хотите ввести свой lastTransactionId вручную? (да/нет): ").strip().lower()
    if use_manual_last_transaction_id in ['да', 'д', 'yes', 'y']:
        manual_last_transaction_id = input("Введите lastTransactionId: ").strip()
        if manual_last_transaction_id:
            last_transaction_id = manual_last_transaction_id
            print(f"[+] Используется введённый lastTransactionId: {last_transaction_id}")
            log(f"Используется введённый lastTransactionId: {last_transaction_id}")
        else:
            print("[-] Введён пустой lastTransactionId. Используется автоматический.")
            log("Введён пустой lastTransactionId. Используется автоматический.")
            last_transaction_id = None
    else:
        print("[+] Используется автоматический lastTransactionId: None")
        log("Используется автоматический lastTransactionId: None")
        last_transaction_id = None

    # Получение транзакций клиента за указанную ревизию
    transactions = loyalty_api.get_transactions_by_revision(customer_id, revision, last_transaction_id)
    # Красивый вывод транзакций
    loyalty_api.display_transactions(transactions)

    # Определение бренда (пример: 'SH', 'BL', 'BS')
    comment = customer_info.get("comment") or ""  # Обработка None
    if "SH" in comment:
        brand = "SH"
    elif "BL" in comment:
        brand = "BL"
    elif "BS" in comment:
        brand = "BS"
    else:
        brand = "Unknown"

    if brand == "Unknown":
        print("[-] Не удалось определить бренд клиента из комментария. Завершение скрипта.")
        log("Не удалось определить бренд клиента из комментария. Скрипт завершен.")
        return

    print(f"[+] Определённый бренд: {brand}\n")
    log(f"Определённый бренд клиента: {brand}")

    # Проверка, является ли клиент новым по бренду
    is_new = loyalty_api.is_new_customer(transactions, brand_id=brand)

    if is_new:
        print(f"[+] Клиент {phone} является новым по бренду {brand}.\n")
        log(f"Клиент {phone} является новым по бренду {brand}.")

        # Загрузка существующих купонов
        existing_coupons = load_existing_coupons('existing_coupons.txt')  # Укажите правильный путь к файлу

        # Генерация нового промокода
        promo_code = create_new_coupon(prefix='N', brand=brand, existing_coupons=existing_coupons)
        print(f"[+] Сгенерирован промокод: {promo_code}\n")
        log(f"Сгенерирован промокод для клиента {phone}: {promo_code}")

        # Сохранение сгенерированного промокода
        save_new_coupon('existing_coupons.txt', promo_code)  # Укажите правильный путь к файлу


    else:
        print(f"[-] Клиент {phone} не является новым по бренду {brand}.\n")
        log(f"Клиент {phone} не является новым по бренду {brand}.")

if __name__ == "__main__":
    main()

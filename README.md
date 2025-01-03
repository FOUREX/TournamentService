# PowerCup Back-end
## Бекенд для автоматизації проведення турнірів

Цей бекенд створено для полегшення організації та управління турнірами. Він забезпечує автоматизацію ключових процесів, таких як реєстрація учасників, формування турнірних сіток, ведення результатів та забезпечення прозорості процесів. Основна мета — зробити управління турнірами швидким, зручним і доступним для всіх користувачів.

## Основні можливості

- **Реєстрація учасників**: забезпечення процесу створення та управління профілями учасників. 
- **Створення команд**: формування команд із зареєстрованих учасників для участі в турнірах.
- **Система сповіщень**: оперативне інформування учасників про зміни у розкладі, результати матчів, майбутні події тощо.
- **Організація турнірів**: автоматизація всіх етапів організації турнірів до визначення переможців.

## Встановлення

1. Склонуйте репозиторій до локальної машини:
   ```shell
   git clone https://github.com/FOUREX/TournamentService
   ```

2. Перейдіть до теки проєкту:
   ```shell
   cd TournamentService
   ```

3. Встановіть віртуальне середовище:
   ```shell
   python -m venv venv
   ```

4. Активуйте віртуальне середовище:
   ```shell
   venv\Scripts\activate
   ```

5. Встановіть залежності:
   ```shell
   pip install -r requirements.txt
   ```

6. Створіть файл `.env` та заповніть згідно зразку:
   ```dotenv
   DB_USER=
   DB_PASS=
   DB_HOST=
   DB_PORT=
   DB_NAME=
   
   JWT_SECRET=
   
   AWS_ACCESS_KEY=
   AWS_SECRET_KEY=
   
   ```

7. Проведення міграцій:
   ```shell
   alembic revision --autogenerate -m "Description"
   ```
   ```shell
   alembic upgrade head
   ```

8. Запуск:
   ```shell
   uvicorn src.main:app --host 127.0.0.1 --port 25565 --reload
   ```

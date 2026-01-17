# Система имитирующая данные с фитнесс браслета, проект использует python, PostgreSQL, Redash



Система состоит из:

\- \*\*Python генератора\*\* — пишет реалистичные данные фитнес-трекера в PostgreSQL раз в 10 секунд.

\- \*\*PostgreSQL\*\* — хранит таблицу `fitness\_events`.

\- \*\*Redash\*\* — подключается к PostgreSQL и визуализирует данные на дэшбордах.

\- \*\*Redis + отдельная PostgreSQL БД Redash\*\* — инфраструктура Redash (метаданные, очереди).



---



## Стек



\- Python 3.x

\- PostgreSQL

\- Docker / Docker Compose

\- Redash (UI аналитики)

\- Redis (для Redash)



---



## Архитектура и сервисы



Docker Compose поднимает несколько контейнеров:



\- `db` — PostgreSQL с пользовательской базой приложения (например `appdb`)

\- `generator` — Python контейнер с генератором фитнес-данных

\- `redash\_db` — отдельная PostgreSQL БД \*\*для метаданных Redash\*\* (не путать с `db`)

\- `redash\_redis` — Redis для Redash

\- `redash\_init` — одноразовая инициализация схемы Redash

\- `redash\_server`, `redash\_worker` — сервисы Redash



Данные приложения (фитнес-события) лежат в \*\*`db`\*\*, метаданные Redash — в \*\*`redash\_db`\*\*.



---


## Данные и таблица



Генератор пишет в таблицу:



`fitness\_events`:

\- `id` — PK

\- `ts` — время события (TIMESTAMPTZ)

\- `activity` — тип активности (`sleep`, `rest`, `walk`, `run`, `bike`, `strength`)

\- `steps` — шаги (INT)

\- `heart\_rate` — пульс (INT, уд/мин)

\- `calories` — калории (NUMERIC)



Таблица создаётся SQL-схемой из файла:

\- `db/init/001\_schema.sql`



Важно: init-скрипты Postgres выполняются \*\*только при первой инициализации пустого volume\*\*.



Если volume уже существовал и таблицы нет — примените схему вручную:



```bash

docker exec -i data\_project\_db psql -U appuser -d appdb < db/init/001\_schema.sql

```

## Как запустить?
### 1) Предварительные требования - Установленный Docker Desktop (или Docker Engine) и Docker Compose. 

### 2) Переменные окружения 

Создайте .env в корне проекта (не коммитить):

POSTGRES\_DB=appdb

POSTGRES\_USER=appuser

POSTGRES\_PASSWORD=apppassword

REDASH\_DB=redash

REDASH\_DB\_USER=redash

REDASH\_DB\_PASSWORD=redashpassword

REDASH\_COOKIE\_SECRET=change\_me\_to\_long\_random\_string

REDASH\_SECRET\_KEY=change\_me\_to\_long\_random\_string\_2

REDASH\_PORT=5000

### 3) Запуск

Запустите командой

```bash

docker compose up -d --build

```


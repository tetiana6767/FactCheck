# FactCheck — AI Agents for Digital Trust

Проєкт мультиагентної системи для аналізу новин і перевірки тверджень за допомогою зовнішніх доказів. Архітектура передбачає вебінтерфейс, API на FastAPI та оркестрацію агентів із LangGraph.

FastAPI приймає текст, виділяє декларативні твердження, шукає точні збіги в локальному навчальному корпусі та повертає простежуваний знімок доказів. Вебклієнт показує зв'язок між тезою, цитатою та джерелом. Поточна версія ще не виконує зовнішній вебпошук і завжди повертає статус про недостатність доказів для фактологічного висновку.

## Вимоги

- Python 3.13.
- Віртуальне середовище `venv`.

## Локальний запуск

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
Set-Location apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Після запуску вебклієнт доступний за адресою `http://127.0.0.1:8000`, перевірка стану API — `http://127.0.0.1:8000/api/health`, документація OpenAPI — `http://127.0.0.1:8000/docs`.

Приклад запиту:

```json
{
  "claim": "Київ — столиця України."
}
```

Відповідь містить початковий текст, список `claims`, сумісне поле `evidence` та версійований `evidence_snapshot`. URI з префіксом `urn:factcheck:test-corpus:` позначають навчальні записи й не є зовнішніми вебджерелами.

## Тести

```powershell
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements-dev.txt
Set-Location apps\api
..\..\.venv\Scripts\python.exe -m pytest -q
```

## Структура

- `apps/web/` — вебінтерфейс, стилі та JavaScript-клієнт API.
- `apps/api/app/api/` — HTTP-маршрути.
- `apps/api/app/agents/` — граф і агенти аналізу.
- `apps/api/app/services/` — виділення тверджень, пошуковий інтерфейс, локальний адаптер, реєстр доказів і координація перевірки.
- `apps/api/app/schemas/` — схеми запитів і відповідей.
- `apps/api/app/storage/` — зберігання історії.
- `apps/api/tests/` — тести API та його компонентів.
- `data/` — приклади й набори даних для оцінювання.
- `models/` — локальні моделі за потреби.
- `docs/` — документація проєкту.

## Ліцензія

Умови використання наведено у файлі [LICENSE](LICENSE).

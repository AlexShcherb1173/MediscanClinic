# MediscanClinic 🏥

Django-проект клиники диагностики и анализов: каталог услуг, врачи, онлайн-запись, акции, личный кабинет и выдача результатов исследований.

---

## ✨ Возможности

- **Каталог услуг**:   
  - категории, поиск, 
  - фильтры по цене,
  - сортировка, пагинация
- **Детальная страница услуги**:
  - описание, 
  - диапазон цен, 
  - CTA на запись
- **Врачи**: 
  - список и профиль врача (фото, специализации, стаж, расписание)
- **Онлайн-запись**: 
  - выбор услуги/врача, слоты, подтверждение
- **Акции**: 
  - список и детальная акция (привязка услуг к акции)
- **Личный кабинет**: 
  - записи, результаты исследований
- **Результаты исследований**: 
  - загрузка файлов администратором, 
  - отображение пациенту
- **Обратная связь / Задать вопрос**: 
  - формы, отправка администратору (email/telegram)
- **Уведомления**:  
  - Celery-задачи (напоминания и уведомления)

---

## 🧱 Стек

- Python, Django
- Celery (tasks / reminders)
- PostgreSQL (в docker-режиме)
- Redis (broker для Celery)
- TailwindCSS (сборка через npm)
- HTMX (точечные динамические элементы в шаблонах)

---

## 📁 Структура проекта (укрупнённо)

- `backend/apps/` — Django приложения:
  - `accounts`, 
  - `appointments`, 
  - `cabinet`, 
  - `contacts`, 
  - `notifications`,
    
  - `pages`, 
  - `patients`, 
  - `promos`, 
  - `results`, 
  - `services`, 
  - `staff`
- `backend/config/` — конфиг Django + settings (`base/dev/prod`)
- `backend/templates/` — шаблоны
- `backend/static/` — статика (CSS/JS)
- `backend/static_src/` — исходники Tailwind
- `docker/`, `Dockerfile`, `compose.yaml` — контейнеризация
- `fixtures/` внутри приложений — демо-данные

---

## ⚙️ Быстрый старт (локально)

### 1) Подготовка окружения
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt

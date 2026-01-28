# 🚀 Деплой на Timeweb VPS

## ✅ Ваш сервер готов!

**IP:** `46.149.66.138`  
**Пароль:** (смените при первом входе!)

---

## 📋 Быстрая установка (5 минут)

### Шаг 1: Подключитесь к серверу

```bash
ssh root@46.149.66.138
```

Введите пароль, который вам дали при создании VPS.

---

### Шаг 2: Смените пароль (ВАЖНО!)

```bash
passwd
```

Введите новый надежный пароль 2 раза.

---

### Шаг 3: Загрузите и запустите скрипт установки

**Автоматическая установка (рекомендуется):**

```bash
# Загрузка скрипта
curl -o install.sh https://raw.githubusercontent.com/ваш-username/gryadka/main/deploy_to_vps.sh

# Запуск
chmod +x install.sh
./install.sh
```

Скрипт спросит:
- GitHub username
- Название репозитория
- BOT_TOKEN (от @BotFather)
- ADMIN_ID (ваш Telegram ID)
- MINI_APP_URL (GitHub Pages URL)
- SECRET_KEY (или сгенерирует автоматически)

**Всё остальное установится автоматически!** ✨

---

### ИЛИ Шаг 3 (Ручная установка):

Если хотите установить вручную:

```bash
# 1. Обновление системы
apt update && apt upgrade -y

# 2. Установка ПО
apt install -y python3 python3-pip python3-venv git screen ufw

# 3. Firewall
ufw allow 22/tcp
ufw allow 8000/tcp
ufw --force enable

# 4. Клонирование проекта (замените username)
cd /root
git clone https://github.com/ваш-username/gryadka.git
cd gryadka

# 5. Виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Настройка .env
nano .env
```

В `.env` укажите:
```env
BOT_TOKEN=ваш_токен
ADMIN_ID=587362201
DATABASE_URL=sqlite+aiosqlite:///./gryadka.db
MINI_APP_URL=https://ваш-username.github.io/gryadka/
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=создайте_случайную_строку
```

```bash
# 7. Инициализация БД
python init_db.py

# 8. Создание systemd service
nano /etc/systemd/system/gryadka.service
```

Вставьте:
```ini
[Unit]
Description=Gryadka Telegram Bot and API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/gryadka
Environment="PATH=/root/gryadka/venv/bin"
ExecStart=/root/gryadka/venv/bin/python /root/gryadka/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 9. Запуск
systemctl daemon-reload
systemctl enable gryadka
systemctl start gryadka
systemctl status gryadka
```

---

## ✅ Проверка работы

**На сервере:**
```bash
curl http://localhost:8000/docs
```

**В браузере:**
```
http://46.149.66.138:8000/docs
```

Должна открыться Swagger документация! ✅

---

## 📝 Полезные команды

```bash
# Статус сервиса
systemctl status gryadka

# Логи в реальном времени
journalctl -u gryadka -f

# Перезапуск
systemctl restart gryadka

# Остановка
systemctl stop gryadka

# Запуск
systemctl start gryadka

# Обновление кода
cd /root/gryadka
git pull
systemctl restart gryadka
```

---

## 🌐 После установки

### Обновите Mini App на GitHub (НА ВАШЕМ КОМПЬЮТЕРЕ)

`docs/config.js` уже обновлен с IP сервера:
```javascript
API_BASE_URL: 'http://46.149.66.138:8000'
```

**Закоммитьте и запушьте:**
```bash
cd /Users/sdxsdysdz/Desktop/Programs/Freelance/Farid/Gryadka
git add docs/config.js deploy_to_vps.sh TIMEWEB_DEPLOY.md
git commit -m "Add Timeweb deployment scripts and config"
git push
```

---

## 🎉 Готово!

**Ваша архитектура:**
```
GitHub Pages
└── Mini App: https://ваш-username.github.io/gryadka/

Timeweb VPS (46.149.66.138)
├── Telegram Bot ✅
├── API ✅ http://46.149.66.138:8000
└── Database (SQLite) ✅
```

**Протестируйте:**
1. Откройте Mini App в браузере
2. Откройте бота в Telegram
3. Попробуйте добавить товар

---

## 🆘 Решение проблем

### Сервис не запускается

```bash
# Проверьте логи
journalctl -u gryadka -n 50

# Проверьте .env
cat /root/gryadka/.env

# Попробуйте запустить вручную
cd /root/gryadka
source venv/bin/activate
python run.py
```

### API не отвечает

```bash
# Проверьте, что порт открыт
ufw status

# Проверьте, слушает ли процесс
netstat -tlnp | grep 8000

# Проверьте firewall
curl http://localhost:8000/docs
```

### База данных не создается

```bash
cd /root/gryadka
source venv/bin/activate
rm gryadka.db
python init_db.py
```

---

## 💰 Стоимость

- **VPS Cloud 2:** ~300₽/месяц
- **GitHub Pages:** бесплатно

**Итого:** ~300₽/месяц 🎉

---

**Удачи!** 🚀

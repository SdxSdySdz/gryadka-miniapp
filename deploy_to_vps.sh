#!/bin/bash

# Скрипт автоматической установки проекта Gryadka на VPS (Timeweb)
# Используйте этот скрипт после подключения по SSH к серверу

set -e  # Остановить при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🍎 Установка проекта Грядка на VPS   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Проверка root прав
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Запустите скрипт с правами root (sudo)${NC}"
    exit 1
fi

# 1. Обновление системы
echo -e "${YELLOW}📦 Обновление системы...${NC}"
apt update && apt upgrade -y

# 2. Установка необходимого ПО
echo -e "${YELLOW}📦 Установка Python, Git, Screen...${NC}"
apt install -y python3 python3-pip python3-venv git screen ufw curl

# 3. Настройка Firewall
echo -e "${YELLOW}🔒 Настройка Firewall...${NC}"
ufw allow 22/tcp
ufw allow 8000/tcp
ufw --force enable
echo -e "${GREEN}✅ Firewall настроен (порты 22, 8000)${NC}"

# 4. Запрос данных
echo ""
echo -e "${BLUE}📝 Введите данные для настройки:${NC}"
read -p "GitHub username: " GITHUB_USER
read -p "Название репозитория [gryadka]: " REPO_NAME
REPO_NAME=${REPO_NAME:-gryadka}

read -p "BOT_TOKEN (от @BotFather): " BOT_TOKEN
read -p "ADMIN_ID (ваш Telegram ID): " ADMIN_ID
read -p "MINI_APP_URL (GitHub Pages URL): " MINI_APP_URL
read -p "SECRET_KEY (минимум 32 символа) [auto]: " SECRET_KEY

# Генерация SECRET_KEY если не указан
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    echo -e "${GREEN}✅ Сгенерирован SECRET_KEY${NC}"
fi

# 5. Клонирование проекта
echo ""
echo -e "${YELLOW}📥 Клонирование проекта...${NC}"
cd /root
if [ -d "$REPO_NAME" ]; then
    echo -e "${YELLOW}⚠️  Директория существует, обновляем...${NC}"
    cd $REPO_NAME
    git pull
else
    git clone https://github.com/$GITHUB_USER/$REPO_NAME.git
    cd $REPO_NAME
fi

# 6. Создание виртуального окружения
echo -e "${YELLOW}🐍 Создание виртуального окружения...${NC}"
python3 -m venv venv
source venv/bin/activate

# 7. Установка зависимостей
echo -e "${YELLOW}📦 Установка зависимостей...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 8. Создание .env файла
echo -e "${YELLOW}⚙️  Создание .env файла...${NC}"
cat > .env << EOF
# Telegram Bot Configuration
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./gryadka.db

# Mini App Configuration
MINI_APP_URL=$MINI_APP_URL

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=$SECRET_KEY
EOF

echo -e "${GREEN}✅ .env файл создан${NC}"

# 9. Инициализация базы данных
echo -e "${YELLOW}🗄️  Инициализация базы данных...${NC}"
python init_db.py
echo -e "${GREEN}✅ База данных инициализирована${NC}"

# 10. Создание systemd service
echo -e "${YELLOW}⚙️  Создание systemd service...${NC}"
cat > /etc/systemd/system/gryadka.service << EOF
[Unit]
Description=Gryadka Telegram Bot and API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/$REPO_NAME
Environment="PATH=/root/$REPO_NAME/venv/bin"
ExecStart=/root/$REPO_NAME/venv/bin/python /root/$REPO_NAME/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 11. Запуск сервиса
echo -e "${YELLOW}🚀 Запуск сервиса...${NC}"
systemctl daemon-reload
systemctl enable gryadka
systemctl start gryadka

# Ждем 3 секунды для запуска
sleep 3

# 12. Проверка статуса
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
if systemctl is-active --quiet gryadka; then
    echo -e "${GREEN}✅ Сервис успешно запущен!${NC}"
else
    echo -e "${RED}❌ Ошибка запуска сервиса${NC}"
    echo -e "${YELLOW}Проверьте логи: journalctl -u gryadka -f${NC}"
    exit 1
fi

# 13. Получение IP адреса
IP_ADDR=$(curl -s ifconfig.me)

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🎉 Установка завершена!        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📱 Mini App:${NC} $MINI_APP_URL"
echo -e "${GREEN}🌐 API:${NC} http://$IP_ADDR:8000"
echo -e "${GREEN}📚 API Docs:${NC} http://$IP_ADDR:8000/docs"
echo ""
echo -e "${YELLOW}📝 Полезные команды:${NC}"
echo -e "  ${BLUE}Статус:${NC}        systemctl status gryadka"
echo -e "  ${BLUE}Логи:${NC}          journalctl -u gryadka -f"
echo -e "  ${BLUE}Перезапуск:${NC}    systemctl restart gryadka"
echo -e "  ${BLUE}Остановка:${NC}     systemctl stop gryadka"
echo ""
echo -e "${GREEN}✅ Всё готово к работе!${NC}"
echo ""

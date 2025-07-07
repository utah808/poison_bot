#!/bin/bash

echo "➡️ Обновляем код из GitHub..."
git stash
git pull origin main

echo "🔄 Перезапускаем сервис poison_bot..."
sudo systemctl restart poison_bot

echo "✅ Готово!"


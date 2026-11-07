# 🚀 MineDash Launcher (v1.4.5)

[![Release](https://img.shields.io/badge/release-v1.4.5-blue.svg)](https://minedash.fun)
[![Built with Tauri](https://img.shields.io/badge/Tauri-v2.0-24C8DB?logo=tauri&logoColor=white)](https://tauri.app)
[![Rust](https://img.shields.io/badge/Rust-1.80+-DEA584?logo=rust&logoColor=white)](https://www.rust-lang.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Официальный легковесный open-source лаунчер Minecraft для сообщества **MineDash**.  
Построен на современном высокопроизводительном стеке **Rust (Tauri 2) + React 18 + TypeScript + Vite**.

Исходный код полностью открыт для максимальной прозрачности и доверия игроков: в лаунчере **нет скрытого кода, майнеров, телеметрии или модификации системных файлов**.

---

## 🌟 Основные возможности

- **Высокая производительность и лёгкость:** благодаря ядру на Rust лаунчер потребляет в 5–10 раз меньше оперативной памяти по сравнению с тяжёлыми Electron- и Java-лаунчерами.
- **Автоматическая установка окружения:**
  - Скачивание и распаковка изолированной **Adoptium Eclipse Temurin JDK 21** (игроку не нужно вручную ставить Java).
  - Автоматическая установка и валидация библиотек **NeoForge 1.21.1**.
  - Полная проверка целостности библиотек, ассетов и нативов Minecraft по SHA-1/SHA-256 хэшам.
- **Синхронизация модпака:** быстрая проверка и докачка модов через высокопроизводительный CDN `cdn.minedash.fun`.
- **Поддержка кастомных скинов:**
  - Загрузка скинов 64×64 и 64×32.
  - Поддержка форматов Classic (Steve) и Slim (Alex).
  - Интеграция с модами `mdskin` и `Chat Heads` для отображения в игре, табе и чате в offline-mode.
- **Кастомизация интерфейса:** сменяемые анимированные фоны, темы оформления и удобная панель управления.
- **Безопасная авторизация:** прямое защищённое соединение с сайтом и API проекта.

---

## 🛠 Архитектура проекта

```text
launcher/
├── src/                  # Фронтенд (React 18 + TypeScript + Vite + CSS)
│   ├── components/       # UI компоненты (Playbar, Titlebar, Sidebar, Hero, Modals)
│   ├── lib/              # API клиенты, форматирование, темы оформления
│   └── shared/           # Общие TypeScript интерфейсы
├── src-tauri/            # Бэкенд лаунчера на Rust
│   ├── src/main.rs       # Логика загрузки Java, NeoForge, запуска игры и проверки целостности
│   ├── Cargo.toml        # Зависимости Rust
│   └── tauri.conf.json   # Конфигурация Tauri 2
└── resources/            # Дополнительные ресурсы (шрифты, базовые скины, мод авторизации)
```

---

## 📦 Сборка из исходного кода

### Требования
1. **Node.js:** версия 20 или 22 LTS.
2. **Rust & Cargo:** версия 1.78 или новее ([установить Rust](https://rustup.rs/)).
3. **C++ Build Tools:** Visual Studio C++ Build Tools (Windows).

### Пошаговая сборка:

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/<ваш-аккаунт>/minedash-launcher.git
   cd minedash-launcher
   ```

2. **Установите зависимости фронтенда:**
   ```bash
   npm install
   ```

3. **Сборка веб-интерфейса:**
   ```bash
   npm run build
   ```

4. **Сборка релизного бинарника (`.exe`):**
   ```bash
   cargo build --release --manifest-path src-tauri/Cargo.toml
   ```

Готовый исполняемый файл будет доступен в:
`src-tauri/target/release/minedash-launcher.exe`

---

## 🔒 Безопасность и приватность

- **Без телеметрии:** лаунчер не собирает данные о системе, железе или действиях пользователя.
- **Безопасное хранение:** токены сессии шифруются и хранятся исключительно локально на компьютере пользователя.
- **Служба запуска:** игра запускается с изолированными параметрами в папке игры без внедрения DLL в сторонние процессы.

---

## 📄 Лицензия

Проект распространяется под открытой лицензией **MIT License**. См. файл [LICENSE](LICENSE) для подробностей.

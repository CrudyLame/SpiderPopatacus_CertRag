# МегаДемка:

![Demo GIF](https://github.com/CrudyLame/SpiderPopatacus_CertRag/blob/master/misc/ScreenCast.gif)

# Система проверки соответствия сертификации на основе RAG

Этот проект реализует систему генерации с расширенным поиском (Retrieval-Augmented Generation, RAG) для проверки соответствия автомобильных требований нормам сертификации.

## Особенности

- Анализирует тексты требований на соответствие автомобильным нормам
- Использует векторное хранилище FAISS для эффективного поиска релевантных сегментов нормативных документов
- Применяет языковые модели OpenAI для интеллектуальной оценки соответствия
- Предоставляет подробные заключения о соответствии с рекомендациями
- Поддерживает как проверку отдельных требований, так и пакетную обработку нескольких требований

## Компоненты

- `rag.py`: Содержит основной класс `CertRAG` для выполнения проверок соответствия
- `llm.py`: Реализует класс `LLMModel` для взаимодействия с языковыми моделями
- `store.py`: Управляет векторным хранилищем FAISS для хранения и извлечения сегментов нормативных документов
- `app.py`: Интерфейс командной строки для выполнения проверок соответствия
- `web_app.py`: Веб-интерфейс на основе Streamlit для удобного взаимодействия с пользователем

## Настройка

1. Клонируйте репозиторий
2. Настройте переменные окружения:
   - Создайте файл `.env` в корневой директории проекта
   - Добавьте ваш ключ API OpenAI: 
     ```
     OPENAI_API_KEY=ваш_ключ_api_здесь
     ```
   - При необходимости настройте прокси:
     - Для HTTP прокси: 
       ```
       HTTP_PROXY=http://your_proxy:port
       ```
     - Для HTTPS прокси: 
       ```
       HTTPS_PROXY=https://your_proxy:port
       ```
3. Подготовьте индекс FAISS:
   - Убедитесь, что у вас есть предварительно созданный индекс FAISS в директории `db/faiss_index` или же он будет создан автоматически

## Использование

1. Положите `.txt` файлы для индексации в папку `RegDocs`
2. Выполните следующие команды:
    
    Установка Poetry
   ```bash
   pip install poetry
   ```

   Установка зависимостей проекта
   ```bash
   poetry install
   ```

   Активация виртуального окружения Poetry
   ```bash
   poetry shell
   ```

   Запуск Streamlit приложения
   ```bash
   streamlit run web_app.py --server.headless True --server.enableXsrfProtection false
   ```
3. Запустится веб-интерфейс, и вы сможете начать пользоваться приложением



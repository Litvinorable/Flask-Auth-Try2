Для начала вам нужно установить:

- Python (Version 3.6 or above)
- Flask
- Pyrebase (A Python wrapper for the Firebase API)

## Инструкции по установке

1. Клонируйте этот репозиторий на свой локальный компьютер.
    ```bash
    git clone https://github.com/Litvinorable/Flask-Auth-Try2
    ```

2. Перейдите в каталог проекта.
    ```bash
    cd app
    ```

3. Установите необходимые пакеты.
    ```bash
    pip install -r requirements.txt
    ```
4. Установите Pyrebase (используйте pyrebase4, так как оригинальный pyrebase устарел):
   ```bash
    pip install pyrebase4
    ```  
    Дополнительные зависимости (если потребуются):
    ```bash
    pip install flask python-dotenv requests
    ``` 
    Проверьте установку:
     ```bash
    pip show pyrebase4
    ``` 

## Запуск приложения

Перейдите в папку app 

```bash
cd app
```

Чтобы запустить приложение, выполните следующую команду в вашем терминале:

```bash
python app.py
```


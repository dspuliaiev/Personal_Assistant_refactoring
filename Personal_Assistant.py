from abc import ABC, abstractmethod
import os
from datetime import datetime, date, timedelta
from rich.console import Console
import re
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich.table import Table
from rich.text import Text
from dateutil import parser
from rich.live import Live
import csv
import shutil
from pathlib import Path

console = Console()


class Contact:
    def __init__(self, name, address, phone, email, birthday):
        self.name = name
        self.address = address
        self.phone = phone
        self.email = email
        self.birthday = birthday


class Note:
    def __init__(self, text, tags=None):
        self.text = text
        self.tags = tags or []


class FolderOrganizer:
    def __init__(self, folder_path=None):
        self.folder_path = folder_path

        self.CYRILLIC_SYMBOLS = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ'
        self.TRANSLATION = (
        "a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
        "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "u", "ja", "je", "ji", "g")

        self.TRANS = dict()

        for cyrillic, latin in zip(self.CYRILLIC_SYMBOLS, self.TRANSLATION):
            self.TRANS[ord(cyrillic)] = latin
            self.TRANS[ord(cyrillic.upper())] = latin.upper()

        self.KNOWN_EXTENSIONS = {
            'Images': {'JPEG', 'JPG', 'PNG', 'SVG'},
            'Video': {'AVI', 'MP4', 'MOV', 'MKV'},
            'Documents': {'DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX'},
            'Audio': {'MP3', 'OGG', 'WAV', 'AMR'},
            'Archives': {'ZIP', 'GZ', 'TAR'},
        }

    def normalize(self, name: str) -> str:
        translate_name = re.sub(r'[^a-zA-Z0-9.]', '_', name.translate(self.TRANS))
        return translate_name

    def get_extension(self, name: str) -> str:
        return Path(name).suffix[1:].upper()

    def handle_file(self, file_name: Path, target_folder: Path):
        extension = self.get_extension(file_name)
        normalized_name = self.normalize(file_name.name)

        if extension in {ext for exts in self.KNOWN_EXTENSIONS.values() for ext in exts}:
            target_folder = target_folder / extension
        else:
            target_folder = target_folder / 'MY_OTHER'

        target_folder.mkdir(exist_ok=True, parents=True)
        target_path = target_folder / normalized_name

        if target_path.exists():
            target_path = target_folder / f"{normalized_name.stem}_{normalized_name.suffix}"

        shutil.move(str(file_name), str(target_path))

    def organize_folder(self, local_path):
        self.folder_path = Path(local_path)

        if not self.folder_path.exists() or not self.folder_path.is_dir():
            console.print(f'[red]Папка "{self.folder_path}" не існує.[/red]')

            while True:
                new_user_input = input(
                    'Введіть назву папки для сортування (або натисніть "enter", для введення іншої команди): ')
                if new_user_input == '':
                    break
                else:
                    FolderOrganizer.organize_folder(new_user_input)
                    return
        else:
            for item in self.folder_path.iterdir():
                if item.is_file():
                    self.handle_file(item, self.folder_path)
            console.print(f'[green]Файли в папці "{self.folder_path.name}" відсортовані.[/green]')


class ConsoleInterface(ABC):
    @abstractmethod
    def list_contacts(self):
        raise NotImplementedError

    @abstractmethod
    def list_notes(self):
        raise NotImplementedError

    @abstractmethod
    def display_commands_table(self):
        raise NotImplementedError


class AssistantInterface(ConsoleInterface):
    def __init__(self):
        self.contacts = []
        self.notes = []
        self.commands = ['додати контакт', 'список контактів', 'пошук контактів', 'дні народження',
                         'редагувати контакт', 'видалити контакт', 'сортувати файли',
                         'додати нотатку', 'пошук нотаток', 'видалити нотатку', 'список нотаток',
                         'редагувати нотатку', 'сортувати нотатки', 'допомога', 'вихід']

        # Встановлення автодоповнення на основі доступних команд
        self.command_completer = WordCompleter(self.commands)

    def list_contacts(self):
        """
        Виводить список контактів у вигляді таблиці.
        """
        if not self.contacts:
            console.print("[red]У вас немає жодних контактів в книзі.[/red]")
        else:
            table = Table(title="Список контактів")
            table.add_column("[blue]Ім'я[/blue]")
            table.add_column("[green]Адреса[/green]")
            table.add_column("[yellow]Телефон[/yellow]")
            table.add_column("[cyan]Електронна пошта[/cyan]")
            table.add_column("[magenta]День народження[/magenta]")

            for contact in self.contacts:
                birthday_str = contact.birthday.strftime('%d-%m-%Y')
                table.add_row(
                    Text(contact.name, style="blue"),
                    Text(contact.address, style="green"),
                    Text(contact.phone, style="yellow"),
                    Text(contact.email, style="cyan"),
                    Text(birthday_str, style="magenta")
                )

            # Встановлення відстані від верхнього краю екрану
            console.print("\n" * 2)
            console.print(table, justify="center")

    def list_notes(self):
        """
        Виводить список існуючих нотаток.
        """
        # Виведення списку нотаток
        if not self.notes:
            console.print("[red]У вас немає жодних нотаток.[/red]")
            return  # Повернення з функції, оскільки немає нотаток для редагування

        table = Table(title="Список нотаток")
        table.add_column("[blue]Номер[/blue]")
        table.add_column("[blue]Текст[/blue]")
        table.add_column("[cyan]Теги[/cyan]")

        for i, note in enumerate(self.notes, start=0):
            table.add_row(
                Text(str(i), style="blue"),
                Text(note.text, style="blue"),
                Text(", ".join(note.tags), style="cyan")
            )

        console.print(table, justify="center")
        console.print(f"[green]Кількість існуючих нотаток: {len(self.notes)}[/green]")

    def display_commands_table(self):
        """Створює таблицю зі списком доступних команд і виводить її в консолі"""
        # Створення об'єкта Console
        console = Console()

        # Створення таблиці зі списком команд
        table = Table(title="Доступні команди")
        table.add_column("[cyan]Команда[/cyan]", justify="center")

        for i, command in enumerate(self.commands):
            # Визначення кольору для кожного рядка
            color = "red" if i % 2 == 0 else "cyan"

            # Додавання рядка з визначеним кольором
            table.add_row(f"[{color}]{command}[/{color}]")

        # Виведення таблиці в консоль з використанням Live
        with Live(refresh_per_second=1, console=console) as live:
            console.print(table, justify="center")  # Виведення таблиці з вирівнюванням по центру
            input("Натисніть Enter для завершення перегляду команд...")  # Очікування вводу від користувача
            live.stop()



class AssistantFunctionality:
    def __init__(self, ui: AssistantInterface):
        self.ui = ui
        self.contacts = self.ui.contacts
        self.notes = self.ui.notes
        self.commands = self.ui.commands

    def is_valid_phone(self, phone):
        """
        Перевіряє, чи відповідає формат номера телефону встановленим правилам.
        Args:
            phone (str): Номер телефону для перевірки.
        Returns:
            bool: True, якщо номер телефону відповідає формату, False - інакше.
        """
        # Перевірка правильності формату номера телефону
        # Допустимі формати: +380501234567, 050-123-45-67, 0501234567, (050)123-45-67, 0989898989
        phone_pattern = re.compile(r'^\+?\d{1,3}?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$')
        return bool(re.match(phone_pattern, phone))

    def is_valid_email(self, email):
        """
        Перевіряє, чи відповідає формат електронної пошти встановленим правилам.
        Args:
            email (str): Адреса електронної пошти для перевірки.
        Returns:
            bool: True, якщо адреса електронної пошти відповідає формату, False - інакше.
        """
        # Перевірка правильності формату електронної пошти
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        return bool(re.match(email_pattern, email))

    def add_contact_from_console(self):
        """
        Забезпечує введення даних нового контакту з консолі та додає його до книги контактів.
        """
        console.print("[bold]Додавання нового контакту:[/bold]")

        name = input("Ім'я: ")
        address = input("Адреса: ")
        phone = input("Телефон (формати вводу +380501234567, 050-123-45-67, 0501234567, (050)123-45-67): ")
        email = input("Електронна пошта: ")

        # Додатково: питаємо користувача про день народження і дозволяємо різні формати
        while True:
            try:
                birthday = input("Дата народження (день-місяць-рік): ")
                birthday_date = parser.parse(birthday).date()
                break  # Якщо парсинг відбувся успішно, виходимо з циклу
            except ValueError:
                console.print("[bold red]Помилка:[/bold red] Некоректний формат дати. Спробуйте ще раз.")

        self.add_contact(name, address, phone, email, birthday_date)

    def add_contact(self, name, address, phone, email, birthday):
        """
        Додає новий контакт до книги контактів після перевірки правильності введених даних.
        Args:
            name (str): Ім'я контакту.
            address (str): Адреса контакту.
            phone (str): Номер телефону контакту.
            email (str): Адреса електронної пошти контакту.
            birthday (datetime.date): День народження контакту.
        Returns:
            None
        """
        # Перевірка правильності формату кожного номера телефону

        if not self.is_valid_phone(phone):
            console.print("[bold red]Помилка:[/bold red] Некоректний номер телефону.")
            return

        if not self.is_valid_email(email):
            console.print("[bold red]Помилка:[/bold red] Некоректна електронна пошта.")
            return

        # Перевірка наявності контакту з такими номерами телефонів в книзі контактів
        existing_contact = next((contact for contact in self.contacts if set(contact.phone) == set(phone)), None)

        if existing_contact:
            console.print(f"[bold red]Помилка:[/bold red] Контакт з такими номерами телефонів вже існує.")
            return

        # Додавання нового контакту до книги контактів
        new_contact = Contact(name, address, phone, email, birthday)
        self.contacts.append(new_contact)
        console.print(f"[green]Контакт {name} успішно доданий до книги контактів.[/green]")

    def dump(self):
        """
        Зберігає книгу контактів у файл CSV.
        """
        with open('addressbook.csv', 'w', newline='\n', encoding='utf-8') as fh:
            field_names = ['name', 'address', 'phone', 'email', 'birthday']
            writer = csv.DictWriter(fh, fieldnames=field_names)
            writer.writeheader()
            for contact in self.contacts:
                writer.writerow({'name': contact.name, 'address': contact.address,
                                 'phone': contact.phone, 'email': contact.email,
                                 'birthday': contact.birthday.strftime('%d-%m-%Y')})

    def load(self):
        """
        Завантажує книгу контактів з файлу CSV.
        """
        file_path = 'addressbook.csv'
        if os.path.exists(file_path):
            with open(file_path, newline='\n') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    name = row['name']
                    address = row['address']
                    phone = row['phone']
                    email = row['email']

                    # Перетворення рядка дати у об'єкт datetime.date
                    birthday_str = row['birthday']
                    birthday = datetime.strptime(birthday_str, '%d-%m-%Y').date()

                    new_contact = Contact(
                        name, address, phone, email, birthday)
                    self.contacts.append(new_contact)

            if self.contacts:
                print("Контакти успішно завантажені.")
            else:
                print("Не вдалося завантажити контакти або файл порожній.")
        else:
            print(f"Файл '{file_path}' не знайдено. Спробуйте створити файл або перевірити шлях.")

    def dump_notes(self):
        """
        Зберігає нотатки у файл CSV.
        """
        with open('notes.csv', 'w', newline='\n') as fh:
            field_names = ['text', 'tags']
            writer = csv.DictWriter(fh, fieldnames=field_names)
            writer.writeheader()
            for note in self.notes:
                writer.writerow({'text': note.text, 'tags': ', '.join(note.tags)})

    def load_notes(self):
        """
        Завантажує нотатки з файлу CSV.
        """
        file_path = 'notes.csv'
        if os.path.exists(file_path):
            with open(file_path, newline='\n') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    text = row['text']
                    tags = row['tags'].split(', ')

                    new_note = Note(text, tags)
                    self.notes.append(new_note)

            if self.notes:
                print("Нотатки успішно завантажені.")
            else:
                print("Не вдалося завантажити нотатки або файл порожній.")
        else:
            print(f"Файл '{file_path}' не знайдено. Спробуйте створити файл або перевірити шлях.")

    def upcoming_birthdays(self, days):
        """
        Виводить інформацію про найближчі дні народження у наступні визначені дні.
        Args:
            days (int): Кількість днів для виводу інформації про найближчі дні народження.
        """
        today = datetime.today().date()
        upcoming_birthdays = [contact for contact in self.contacts if
                              today < self.get_next_birthday(contact) <= today + timedelta(days)]
        if not upcoming_birthdays:
            console.print(f'[yellow]У {days} днів немає найближчих днів народження.[/yellow]')
        else:
            table = Table(title=f'Дні народження у наступні {days} днів')
            table.add_column("[blue]Ім'я[/blue]")
            table.add_column("[magenta]Дата народження[/magenta]")
            table.add_column("[yellow]Залишилося днів[/yellow]")
            table.add_column("[green]Вік[/green]")

            for contact in upcoming_birthdays:
                remaining_days = (self.get_next_birthday(contact) - today).days
                birthday_str = contact.birthday.strftime('%d-%m-%Y')

                age = today.year - contact.birthday.year + 1 - (
                            (today.month, today.day) < (contact.birthday.month, contact.birthday.day))

                table.add_row(
                    Text(contact.name, style="blue"),
                    Text(birthday_str, style="magenta"),
                    Text(str(remaining_days), style="yellow"),
                    Text(str(age), style="green")
                )
            # Встановлення відстані від верхнього краю екрану
            console.print("\n" * 2)
            console.print(table, justify="center")

    def get_next_birthday(self, contact):
        """
        Отримує дату наступного дня народження для вказаного контакту.
        Args:
            contact (Contact): Контакт, для якого потрібно отримати наступний день народження.
        Returns:
            datetime.date: Дата наступного дня народження.
        """
        today = datetime.today().date()

        # Перевірка, чи birthday є рядком, і якщо так, конвертувати його у datetime.date
        if isinstance(contact.birthday, str):
            birthday = datetime.strptime(contact['birthday'], "%d-%m-%Y").date()
        else:
            birthday = contact.birthday
        next_birthday = birthday.replace(year=today.year)

        if today > date(today.year, birthday.month, birthday.day):
            next_birthday = next_birthday.replace(year=today.year + 1)

        return next_birthday

    def search_contacts(self, query=None):
        """
        Шукає контакти, які відповідають введеному запиту.
        Args:
            query (str, optional): Запит для пошуку контактів. За замовчуванням - None.
        Returns:
            Contact or None: Знайдений контакт або None, якщо нічого не знайдено.
        """

        if query is None:
            query = input("Введіть запит для пошуку контактів: ")

        matching_contacts = [contact for contact in self.contacts if query.lower() in contact.name.lower()]

        if matching_contacts:
            console.print(f"[bold green]Результати пошуку:[/bold green]")

            # Виведення знайдених контактів в таблицю
            table = Table(title="Знайдені контакти")
            table.add_column("[blue]Ім'я[/blue]", justify="center")
            table.add_column("[green]Адреса[/green]", justify="center")
            table.add_column("[yellow]Телефон[/yellow]", justify="center")
            table.add_column("[cyan]Електронна пошта[/cyan]", justify="center")
            table.add_column("[magenta]День народження[/magenta]", justify="center")

            for contact in matching_contacts:
                table.add_row(
                    Text(contact.name, style="blue"),
                    Text(contact.address, style="green"),
                    Text(contact.phone, style="yellow"),
                    Text(contact.email, style="cyan"),
                    Text(contact.birthday.strftime('%d-%m-%Y'), style="magenta")
                )

            # Центрування таблиці
            console.print(table, justify="center")

            # Повернення першого знайденого контакту
            return matching_contacts[0] if matching_contacts else None
        else:
            console.print(f"[red]Немає результатів пошуку для запиту: {query}[/red]")
            return None

    def edit_contact(self, contact):
        if contact is None:
            console.print("[bold red]Помилка:[/bold red] Контакт не знайдено.")
            return

        console.print(f"[bold]Редагування контакту: {contact.name}[/bold]")

        # Редагування імені
        new_name = input(f"Теперішнє ім'я: {contact.name}\nВведіть нове ім'я (або Enter, щоб залишити без змін): ")
        if new_name:
            contact.name = new_name

        # Редагування адреси
        new_address = input(
            f"Теперішня адреса: {contact.address}\nВведіть нову адресу (або Enter, щоб залишити без змін): ")
        if new_address:
            contact.address = new_address

        # Редагування номеру телефону
        new_phone = input(
            f"Теперішній телефон: {contact.phone}\nВведіть новий телефон (або Enter, щоб залишити без змін): ")
        if new_phone:
            if self.is_valid_phone(new_phone):
                contact.phone = new_phone
            else:
                console.print("[bold red]Помилка:[/bold red] Некоректний номер телефону.")

        # Редагування пошти
        new_email = input(
            f"Теперішня електронна пошта: {contact.email}\nВведіть нову пошту (або Enter, щоб залишити без змін): ")
        if new_email:
            if self.is_valid_email(new_email):
                contact.email = new_email
            else:
                console.print("[bold red]Помилка:[/bold red] Некоректна електронна пошта.")

        # Редагування дня народження
        new_birthday = input(
            f"Теперішній день народження: {contact.birthday.strftime('%d-%m-%Y')}\nВведіть новий день народження (або Enter, щоб залишити без змін): ")
        if new_birthday:
            try:
                new_birthday_date = parser.parse(new_birthday).date()
                contact.birthday = new_birthday_date
            except ValueError:
                console.print("[bold red]Помилка:[/bold red] Некоректний формат дати. Залишено попередню дату.")
        self.dump()
        console.print(f"[green]Контакт {contact.name} успішно відредаговано.[/green]")

    # Видалення контакту
    def delete_contact(self, contact=None):
        """
        Видаляє вказаний контакт або викликає search_contacts для вибору контакту.
        Args:
            contact (Contact, optional): Контакт для видалення. За замовчуванням - None.
        """
        if contact is None:
            # Якщо contact не передано, спробуйте викликати search_contacts для вибору контакту
            contact = self.search_contacts()

        if contact in self.contacts:
            contact_name = contact.name
            self.contacts.remove(contact)
            console.print(f"[green]Контакт {contact_name} успішно видалено.[/green]")
        else:
            console.print("[red]Помилка: Контакт не знайдено або не вибрано для видалення.[/red]")

    def add_note(self, text=None, tags=None):
        """
        Додає нові нотатки.
        Args:
            text (str, optional): Текст нотатки. За замовчуванням - None.
            tags (list, optional): Список тегів для нотатки. За замовчуванням - None.
        """

        while True:
            text = input("Текст нотатки (або введіть 'закінчити' чи 'вийти' для завершення): ")

            if text.lower() == 'закінчити' or text.lower() == 'вийти':
                break

            tags = input("Теги (розділіть їх комою): ").split(',')
            # Додавання нової нотатки
            formatted_tags = [tag.strip() if tag.startswith('#') else f"#{tag.strip()}" for tag in tags]
            new_note = Note(text, tags=formatted_tags)
            self.notes.append(new_note)
            console.print(f"[green]Нотатка успішно додана.[/green]")

    def search_notes(self, text_query=None, tag_query=None):
        """
        Пошук нотаток за текстом або тегом.
        Args:
            text_query (str, optional): Текст для пошуку в нотатках. За замовчуванням - None.
            tag_query (str, optional): Тег для пошуку в нотатках. За замовчуванням - None.
        """
        specify_query = input(
            "Введіть слово 'текст' для пошуку за текстом або введіть слово 'тег' для пошуку за тегом: ")
        if specify_query == 'текст':
            text_query = input("Введіть текст для пошуку: ")
        elif specify_query == 'тег':
            tag_query = input("Введіть тег для пошуку: ")

        matching_notes = []
        if text_query is not None:
            matching_notes_text = [note for note in self.notes if text_query.lower() in note.text.lower()]
            matching_notes.extend(matching_notes_text)
        if tag_query is not None:
            matching_notes_tag = [note for note in self.notes if
                                  any(tag_query.lower() in tag.lower() for tag in note.tags)]
            matching_notes.extend(matching_notes_tag)

        if matching_notes:
            console.print(f"[bold green]Результати пошуку:[/bold green]")

            # Виведення знайдених нотаток в таблицю
            table = Table(title="Знайдені нотатки")
            table.add_column("[cyan]Номер[/cyan]")
            table.add_column("[blue]Нотатка[/blue]")
            table.add_column("[green]Теги[/green]")

            for i, note in enumerate(matching_notes, start=0):
                table.add_row(
                    Text(str(i), style='cyan'),
                    Text(note.text, style='blue'),
                    Text(", ".join(note.tags), style='green')
                )

            console.print(table, justify='center')

        else:
            if text_query is None:
                console.print(f"[red]Немає результатів пошуку за тегом: '{tag_query}'[/red]")
            if tag_query is None:
                console.print(f"[red]Немає результатів пошуку за текстом: '{text_query}'[/red]")

    def edit_note(self, note_index):
        """
        Редагує існуючу нотатку за індексом.
        Args:
            note_index (int): Індекс нотатки для редагування.
        """
        if 0 <= note_index < len(self.notes):
            # Отримання нотатки за індексом
            note_to_edit = self.notes[note_index]

            # Редагування тексту нотатки
            new_text = input("Введіть новий текст нотатки: ")
            note_to_edit.text = new_text

            # Редагування тегів нотатки
            new_tags = input("Введіть нові теги нотатки (через кому): ").split(",")
            note_to_edit.tags = [tag.strip() if tag.startswith('#') else f"#{tag.strip()}" for tag in new_tags]

            console.print(f"[green]Нотатка {note_index} успішно відредагована.[/green]")
        else:
            console.print("[red]Невірний індекс нотатки. Спробуйте ще раз.[/red]")

    def delete_note(self):
        """
        Видаляє нотатку користувача за текстом, назвою або тегом.
        Користувач вводить запит для пошуку нотаток. Знайдені нотатки виводяться, і користувач може
        обрати конкретну нотатку для видалення. Видалена нотатка видаляється зі списку нотаток.
        """
        # Отримання запиту від користувача або використання дефолтного значення
        query = console.input("Введіть текст, назву або тег для пошуку: ")

        # Пошук нотаток за текстом, назвою або тегом
        matching_notes = [note for note in self.notes if
                          query.lower() in note.text.lower() or query.lower() in note.tags]

        if matching_notes:
            console.print(f"[bold green]Результати пошуку:[/bold green]")
            for index, note in enumerate(matching_notes, start=0):
                console.print(f"{index}. {note.text}")

            # Отримання від користувача індексу нотатки для видалення
            note_index_str = console.input(
                "[bold cyan]Введіть номер нотатки для видалення (або 0, щоб скасувати):[/bold cyan] ")
            try:
                note_index = int(note_index_str)
            except ValueError:
                note_index = 0

            if 0 < note_index <= len(matching_notes):
                # Видалення вибраної нотатки
                deleted_note = matching_notes[note_index - 1]
                self.notes.remove(deleted_note)
                console.print(f"[bold green]Нотатка успішно видалена:[/bold green] {deleted_note.text}")
            elif note_index == 0:
                console.print("[cyan]Видалення скасовано користувачем.[/cyan]")
            else:
                console.print("[red]Введено невірний номер нотатки. Видалення скасовано.[/red]")
        else:
            console.print(f"[red]Немає результатів пошуку для запиту: {query}[/red]")

    def sort_notes_by_tags(self):
        """
        Сортує нотатки за тегами та виводить результат у вигляді табличного вигляду.
        Якщо немає жодних нотаток, виводить повідомлення про відсутність нотаток.
        """
        # Сортування нотаток за тегами
        if not self.notes:
            console.print("Немає нотаток для сортування.")
            return
        # створюємо словник для нотаток за тегами
        notes_by_tag_dict = {}
        for note in self.notes:
            for tag in note.tags:
                if tag not in notes_by_tag_dict:
                    notes_by_tag_dict[tag] = []
                # додаємо нотатку до списку за ключем(тегом)
                notes_by_tag_dict[tag].append(note)

        sorted_tags = sorted(notes_by_tag_dict.keys())

        # відображення нотаток
        table = Table(title="Сортування нотаток за тегами")
        table.add_column("[red]Тег[/red]")
        table.add_column("[green]Текст[/green]")

        for tag in sorted_tags:
            tag_notes = notes_by_tag_dict[tag]
            for note in tag_notes:
                table.add_row(Text(tag, style="red"), Text(note.text, style="green"))

        console.print(table)

    def analyze_user_input(self, user_input):
        normalized_input = user_input.lower()
        if "додати контакт" in normalized_input:
            console.print("[green]Пропоную вам додати новий контакт.[/green]")
        elif "список контактів" in normalized_input:
            console.print("[green]Ваш список контактів.[/green]")
        elif "пошук контактів" in normalized_input:
            console.print("[green]Для пошуку контактів введіть ім'я.[/green]")
        elif "дні народження" in normalized_input:
            console.print(
                "[green]Перегляньте список контактів у кого День народження впродовж наступного тижня.[/green]")
        elif "редагувати контакт" in normalized_input:
            console.print("[green]Для редагування контакту.[/green]")
        elif "видалити контакт" in normalized_input:
            console.print("[green]Для видалення контакту.[/green]")
        elif "додати нотатку" in normalized_input:
            console.print("[green]Додавання нових нотаток:[/green]")
        elif "пошук нотаток" in normalized_input:
            console.print("[green]Для пошуку нотаток: [/green]")
        elif "список нотаток" in normalized_input:
            console.print("[green]Ваш список нотаток.[/green]")
        elif "редагувати нотатку" in normalized_input:
            console.print("[green]Для редагування нотатки:[/green]")
        elif "сортувати нотатки" in normalized_input:
            console.print("[green]Відсортовані нотатки: [/green]")
        elif "сортувати файли" in normalized_input:
            console.print("[green]Для сортування файлів: [/green]")
        elif "вихід" in normalized_input:
            console.print("[green]До нових зустрічей![/green]")
        elif "допомога" in normalized_input:
            pass
        else:
            console.print("[red]Не можу розпізнати вашу команду. Пропоную Вам список доступних команд.[/red]")
            self.ui.display_commands_table()

    def run(self):
        completer = WordCompleter(self.commands, ignore_case=True)
        """ Основний цикл виконання програми. Полягає в тому, 
            що він виводить вітання та список команд, а потім 
            чекає на введення команди"""
        console = Console()
        console.print(
            "\n[bold yellow]Вітаю, я ваш особистий помічник![/bold yellow]\n",
            justify="center",
            style="bold",
            width=200,
        )

        self.ui.display_commands_table()

        sorter = FolderOrganizer()

        while True:
            user_input = prompt("Введіть команду: ", completer=completer).lower()
            self.analyze_user_input(user_input)  # self. instead of assistant.
            # Перевірка команд і виклик відповідного методу

            if "допомога" in user_input.lower():
                self.ui.display_commands_table()  # # self. instead of assistant.
            elif "додати контакт" in user_input.lower():
                self.add_contact_from_console()
            elif "список контактів" in user_input.lower():
                self.ui.list_contacts()
            elif "пошук контактів" in user_input.lower():
                self.search_contacts()
            elif 'редагувати контакт' in user_input.lower():
                contact_to_edit = self.search_contacts()
                self.edit_contact(contact=contact_to_edit)
            elif 'видалити контакт' in user_input.lower():
                self.delete_contact()
            elif "дні народження" in user_input.lower():
                self.upcoming_birthdays(7)
            elif "пошук нотаток" in user_input.lower():
                self.search_notes()
            elif "додати нотатку" in user_input.lower():
                self.add_note()
            elif "видалити нотатку" in user_input.lower():
                self.delete_note()
            elif "список нотаток" in user_input.lower():
                self.ui.list_notes()
            elif "редагувати нотатку" in user_input.lower():
                if "редагувати нотатку" in user_input.lower():
                    note_index = int(input("Введіть номер нотатки, яку ви хочете відредагувати: "))
                    self.edit_note(note_index)
            elif "сортувати нотатки" in user_input.lower():
                self.sort_notes_by_tags()
            elif "сортувати файли" in user_input.lower():
                local_path = input("Введіть назву папки або шлях до папки для сортування: ")
                sorter.organize_folder(local_path)
            elif "вихід" in user_input.lower():
                self.dump()
                self.dump_notes()
                break

def main():
    ui = AssistantInterface()
    assistant = AssistantFunctionality(ui)
    assistant.load()
    assistant.load_notes()
    assistant.run()
    return assistant

if __name__ == "__main__":
    assistant_instance = main()

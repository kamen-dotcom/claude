# Настройка на Google Sheets за формата "Запази час"

Това ръководство ще ви помогне да свържете формата за записване за час с Google Sheets.

## Стъпка 1: Създайте Google Sheet

1. Отидете на [Google Sheets](https://sheets.google.com)
2. Създайте нов документ
3. Наименувайте го (напр. "Записвания за преглед")
4. В първия ред добавете следните заглавия (колони A-I):

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| Дата/Час | Име | Фамилия | Телефон | Имейл | Предпочитана дата | Предпочитан час | Вид преглед | Допълнителна информация |

## Стъпка 2: Създайте Google Apps Script

1. В Google Sheet отидете на **Extensions > Apps Script**
2. Изтрийте примерния код и поставете следния:

```javascript
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);

    // Добавяне на нов ред с данните
    sheet.appendRow([
      data.timestamp,
      data.firstName,
      data.lastName,
      data.phone,
      data.email,
      data.date,
      data.time,
      data.service,
      data.message
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({ 'result': 'success' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({ 'result': 'error', 'error': error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService
    .createTextOutput("Appointment form backend is running!")
    .setMimeType(ContentService.MimeType.TEXT);
}
```

3. Запазете проекта (Ctrl+S) и го наименувайте (напр. "Appointment Form Handler")

## Стъпка 3: Публикувайте като Web App

1. Кликнете на **Deploy > New deployment**
2. Кликнете на иконата ⚙️ до "Select type"
3. Изберете **Web app**
4. Настройте:
   - **Description**: Appointment Form Handler
   - **Execute as**: Me
   - **Who has access**: Anyone
5. Кликнете **Deploy**
6. Ще ви поискат разрешение - кликнете **Authorize access**
7. Изберете вашия Google акаунт
8. Кликнете **Advanced > Go to [Project Name] (unsafe)**
9. Кликнете **Allow**
10. **КОПИРАЙТЕ URL адреса** на Web App (изглежда така: `https://script.google.com/macros/s/ABC...XYZ/exec`)

## Стъпка 4: Добавете URL в сайта

1. Отворете `katarakta/appointment.html`
2. Намерете този ред в JavaScript секцията:
```javascript
const GOOGLE_SCRIPT_URL = 'YOUR_GOOGLE_SCRIPT_URL_HERE';
```
3. Заменете `YOUR_GOOGLE_SCRIPT_URL_HERE` с URL адреса, който копирахте:
```javascript
const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/ABC...XYZ/exec';
```
4. Запазете файла и го качете отново в GitHub

## Готово!

Сега, когато някой попълни формата:
1. Данните се изпращат към Google Apps Script
2. Скриптът добавя нов ред в Google Sheet
3. Потребителят вижда съобщение за успех

---

## Допълнително: Имейл известия при нова заявка

Добавете този код вместо горния за да получавате имейл при нова заявка:

```javascript
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);

    // Добавяне на нов ред с данните
    sheet.appendRow([
      data.timestamp,
      data.firstName,
      data.lastName,
      data.phone,
      data.email,
      data.date,
      data.time,
      data.service,
      data.message
    ]);

    // Изпращане на имейл известие
    var emailAddress = "your-email@example.com"; // <-- СМЕНЕТЕ С ВАШИЯ ИМЕЙЛ
    var subject = "Нова заявка за преглед - " + data.firstName + " " + data.lastName;
    var body = "Нова заявка за преглед:\n\n" +
               "Име: " + data.firstName + " " + data.lastName + "\n" +
               "Телефон: " + data.phone + "\n" +
               "Имейл: " + data.email + "\n" +
               "Предпочитана дата: " + data.date + "\n" +
               "Предпочитан час: " + data.time + "\n" +
               "Вид преглед: " + data.service + "\n" +
               "Допълнителна информация: " + data.message;

    MailApp.sendEmail(emailAddress, subject, body);

    return ContentService
      .createTextOutput(JSON.stringify({ 'result': 'success' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({ 'result': 'error', 'error': error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService
    .createTextOutput("Appointment form backend is running!")
    .setMimeType(ContentService.MimeType.TEXT);
}
```

---

## Отстраняване на проблеми

**Проблем**: Данните не се записват
- Проверете дали URL адресът е правилен
- Уверете се, че сте публикували скрипта с достъп "Anyone"
- Проверете конзолата на браузъра за грешки (F12 > Console)

**Проблем**: Грешка при авторизация
- Отидете в Apps Script
- Deploy > Manage deployments
- Кликнете Edit на deployment
- Уверете се че "Who has access" е "Anyone"

**Проблем**: CORS грешки в браузъра
- Това е нормално! Използваме `mode: 'no-cors'`
- Ако данните се записват в Google Sheet, всичко работи правилно

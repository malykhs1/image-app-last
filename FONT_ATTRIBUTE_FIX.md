# 🔧 Исправление атрибута шрифта

## ❌ Проблема

**Ошибка:**
```
AttributeError: 'Label' object has no attribute 'font_family'
at Create, line 64
```

**Причина:**  
В Anvil компоненты (Label, Button и т.д.) используют атрибут **`font`**, а не `font_family`.

---

## ✅ Исправление

### Было:
```python
self.label_upload_title.font_family = 'Rubik'
self.button_create.font_family = 'Rubik'
self.step_indicator_1.font_family = 'Rubik'
```

### Стало:
```python
self.label_upload_title.font = 'Rubik'
self.button_create.font = 'Rubik'
self.step_indicator_1.font = 'Rubik'
```

---

## 📊 Статистика исправлений

**Замены по файлам:**

1. **`client_code/Create/__init__.py`**
   - 12 замен `font_family` → `font`
   - Компоненты: file_loader_1, button_create, label_upload_title, label_upload_subtitle, button_close, step_indicator_1, step_indicator_2, step_indicator_3

2. **`client_code/Creation/__init__.py`**
   - 2 замены `font_family` → `font`
   - Компоненты: button_add_to_cart, text_length

3. **`client_code/AddFramePopup/__init__.py`**
   - 3 замены `font_family` → `font`
   - Компоненты: heading_1, button_yes, button_no

**Всего:** 17 исправлений

---

## 📝 Правильный синтаксис для Anvil

### ✅ Правильно:
```python
# Установка шрифта
component.font = 'Rubik'
component.font = 'Arial'
component.font = 'Helvetica'

# Установка размера шрифта
component.font_size = 16

# Установка жирности
component.bold = True
```

### ❌ Неправильно:
```python
# НЕТ ТАКОГО АТРИБУТА В ANVIL!
component.font_family = 'Rubik'  # ← AttributeError!
```

---

## 🎯 Контекст использования

Шрифт Rubik используется для правильного отображения **иврита** (עברית):

```python
if self.locale == 'he':
  self.label_upload_title.text = 'העלה את התמונה שלך'
  self.label_upload_title.font = 'Rubik'  # ← Для иврита
```

---

## ✅ Результат

Все файлы исправлены! Приложение теперь корректно устанавливает шрифт Rubik для компонентов интерфейса.

**Проверено:**
- ✅ `client_code/Create/__init__.py` - 12 исправлений
- ✅ `client_code/Creation/__init__.py` - 2 исправления
- ✅ `client_code/AddFramePopup/__init__.py` - 3 исправления

**Итого:** 17 замен `font_family` → `font`


# 🛒 Настройка добавления в корзину Shopify

## 🎯 Проблема
Товар создается в Shopify, но не добавляется в корзину, когда нажимается кнопка "Add to cart" внутри iframe.

## ✅ Решение
Нужно добавить JavaScript код на страницу Shopify, который будет:
1. Слушать сообщения от iframe
2. Получать `variant_id` созданного товара
3. Добавлять товар в корзину через Shopify Cart API

---

## 📋 Пошаговая инструкция

### Шаг 1: Откройте редактор темы Shopify

1. Зайдите в **Shopify Admin**
2. **Online Store** → **Themes** → **Customize** (или **Edit code**)
3. Нажмите **Edit code**

### Шаг 2: Найдите страницу с iframe

Вариант A: Если iframe добавлен через **Page Template** или **Section**
- Найдите файл: `sections/[название-секции].liquid` или `templates/page.[название].liquid`

Вариант B: Если iframe в основном layout
- Откройте: `layout/theme.liquid`

### Шаг 3: Добавьте скрипт

**Добавьте этот код ПОСЛЕ iframe** (но перед закрывающим тегом `</body>` или в той же секции):

```html
<!-- String Art Cart Integration -->
<script>
(function() {
  console.log('🎨 String Art - Cart integration script loaded');

  window.addEventListener('message', function(event) {
    const data = event.data;
    
    if (!data || typeof data !== 'object') {
      return;
    }

    console.log('📨 Received postMessage:', data);

    // Когда пользователь нажимает "Add to cart" внутри iframe
    if (data.action === 'add' && data.variant_id) {
      console.log('🛒 Adding to cart:', {
        variant_id: data.variant_id,
        add_frame: data.add_frame
      });

      // Формируем товары для добавления
      const items = [{
        id: data.variant_id,
        quantity: 1
      }];

      // Если нужно добавить рамку
      if (data.add_frame && data.frame_id) {
        items.push({
          id: data.frame_id,
          quantity: 1
        });
      }

      // Добавляем в корзину через Shopify Cart API
      fetch('/cart/add.js', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: items })
      })
      .then(response => response.json())
      .then(data => {
        console.log('✅ Successfully added to cart:', data);
        
        // Отправляем подтверждение обратно в iframe
        event.source.postMessage({
          action: 'cart_add_success',
          variant_id: data.variant_id
        }, '*');

        // Открываем корзину (выберите один вариант)
        
        // ВАРИАНТ 1: Если у вас есть Cart Drawer (боковая панель корзины)
        if (typeof Shopify !== 'undefined' && Shopify.CartDrawer) {
          Shopify.CartDrawer.open();
        }
        
        // ВАРИАНТ 2: Редирект на страницу корзины (раскомментируйте если нужно)
        // window.location.href = '/cart';
        
        // ВАРИАНТ 3: Обновить счетчик корзины без открытия
        // document.dispatchEvent(new CustomEvent('cart:refresh'));
      })
      .catch(error => {
        console.error('❌ Error adding to cart:', error);
        alert('Failed to add product to cart. Please try again.');
      });
    }
  });

  console.log('✓ PostMessage listener registered');
})();
</script>
```

### Шаг 4: Сохраните изменения

1. Нажмите **Save** в редакторе кода
2. Вернитесь на страницу с iframe
3. Попробуйте создать товар и добавить в корзину

---

## 🔍 Проверка и отладка

### 1. Откройте консоль браузера (F12 → Console)

При загрузке страницы должно появиться:
```
🎨 String Art - Cart integration script loaded
✓ PostMessage listener registered
```

### 2. Создайте товар и нажмите "Add to cart"

В консоли должно появиться:
```
📨 Received postMessage: {action: 'add', variant_id: 12345678...}
🛒 Adding to cart: {variant_id: 12345678, add_frame: false}
✅ Successfully added to cart: {...}
```

### 3. Если не работает:

**Проблема:** Сообщения не приходят
- Проверьте, что скрипт добавлен на той же странице, где находится iframe
- Убедитесь, что iframe загружен до того, как вы нажимаете "Add to cart"

**Проблема:** Ошибка "Failed to add to cart"
- Проверьте, что `variant_id` существует в вашем магазине
- Убедитесь, что товар опубликован (Status: ACTIVE)
- Проверьте, что товар доступен для покупки (не "Draft")

**Проблема:** Корзина не открывается
- Если используете кастомную тему, измените способ открытия корзины:
  ```javascript
  // Для темы Dawn
  document.querySelector('cart-drawer')?.open();
  
  // Для старых тем
  window.location.href = '/cart';
  ```

---

## 🎨 Дополнительные настройки

### Показывать уведомление вместо открытия корзины

```javascript
.then(data => {
  console.log('✅ Successfully added to cart');
  
  // Показываем уведомление
  const notification = document.createElement('div');
  notification.innerHTML = '✓ Product added to cart!';
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #4CAF50;
    color: white;
    padding: 15px 25px;
    border-radius: 8px;
    z-index: 10000;
    font-weight: bold;
  `;
  document.body.appendChild(notification);
  
  setTimeout(() => notification.remove(), 3000);
});
```

### Добавить анимацию кнопки "Add to cart"

```javascript
// После успешного добавления
const button = document.querySelector('.your-add-to-cart-button');
if (button) {
  button.textContent = '✓ Added!';
  button.classList.add('success');
  
  setTimeout(() => {
    button.textContent = 'Add to cart';
    button.classList.remove('success');
  }, 2000);
}
```

---

## 📝 Альтернативный вариант: Загрузка как внешний файл

Если хотите хранить скрипт отдельно:

### 1. Создайте файл в Assets
- **Add a new asset** → Создайте `string-art-cart.js`
- Скопируйте содержимое из `shopify_page_script.js`

### 2. Подключите в theme.liquid
```liquid
{{ 'string-art-cart.js' | asset_url | script_tag }}
```

---

## ✅ Готово!

После этих изменений товары должны успешно добавляться в корзину Shopify! 🎉

Если возникнут проблемы, проверьте консоль браузера (F12) - там будут подробные логи всех операций.




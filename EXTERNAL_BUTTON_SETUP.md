# Настройка внешней кнопки Add to Cart для Anvil iframe

## 🎯 Проблема
У вас есть кнопка "Add to cart" **вне iframe** (в Shopify), которая должна добавлять в корзину **активный товар** из Anvil приложения (внутри iframe).

## ✅ Решение
Используем **postMessage API** для коммуникации между iframe и родительским окном.

---

## 📋 Шаг 1: Anvil приложение (уже готово ✓)

В `Create/__init__.py` добавлены:
- ✅ `setup_postmessage_listener()` - слушает сообщения от внешней кнопки
- ✅ `add_active_creation_to_cart()` - добавляет активный товар в корзину
- ✅ Отправка подтверждения/ошибки обратно во внешнее окно

---

## 📋 Шаг 2: Shopify (внешняя кнопка)

### Вариант A: Простой скрипт (рекомендуется)

Добавьте этот код в **theme.liquid** или в секцию с iframe:

```html
<script>
(function() {
  // ID или класс вашего iframe
  const iframe = document.querySelector('iframe[src*="anvil.app"]');
  
  // Класс вашей внешней кнопки
  const button = document.querySelector('.artwork-section__cta.artwork-section__cta_desktop');
  
  if (!iframe || !button) {
    console.error('Iframe or button not found');
    return;
  }

  button.addEventListener('click', function(e) {
    e.preventDefault();
    console.log('Sending add to cart message to iframe...');
    
    // Отправляем команду в iframe
    iframe.contentWindow.postMessage({
      action: 'add_active_to_cart'
    }, '*');
  });

  // Слушаем ответ от iframe
  window.addEventListener('message', function(event) {
    if (event.data?.action === 'cart_add_success') {
      console.log('✓ Product added to cart');
      // Открываем корзину (опционально)
      // window.location.href = '/cart';
    }
  });
})();
</script>
```

### Вариант B: Если iframe имеет ID

```html
<iframe id="anvil-artwork-app" src="https://your-app.anvil.app/..."></iframe>

<button class="artwork-section__cta artwork-section__cta_desktop">
  Add to cart
</button>

<script>
document.querySelector('.artwork-section__cta_desktop').onclick = function(e) {
  e.preventDefault();
  document.getElementById('anvil-artwork-app').contentWindow.postMessage({
    action: 'add_active_to_cart'
  }, '*');
};
</script>
```

---

## 📋 Шаг 3: Проверка

1. Откройте страницу с iframe в браузере
2. Сгенерируйте artwork в Anvil приложении
3. Откройте Console (F12)
4. Нажмите на внешнюю кнопку "Add to cart"
5. В консоли должны появиться:
   ```
   Sending add to cart message to iframe...
   CLIENT: Received postMessage: {action: 'add_active_to_cart'}
   CLIENT: Adding active creation to cart: variant_id=...
   ✓ Product added to cart
   ```

---

## 🎨 Улучшения (опционально)

### 1. Визуальная обратная связь при добавлении

```javascript
window.addEventListener('message', function(event) {
  if (event.data?.action === 'cart_add_success') {
    const button = document.querySelector('.artwork-section__cta_desktop');
    button.textContent = 'Added! ✓';
    button.style.background = '#4CAF50';
    
    setTimeout(() => {
      button.textContent = 'Add to cart';
      button.style.background = '';
    }, 2000);
  }
});
```

### 2. Автоматическое открытие корзины

```javascript
if (event.data?.action === 'cart_add_success') {
  // Shopify стандартный способ
  if (typeof Shopify !== 'undefined' && Shopify.CartDrawer) {
    Shopify.CartDrawer.open();
  } else {
    // Или редирект
    window.location.href = '/cart';
  }
}
```

### 3. Показ ошибок

```javascript
if (event.data?.action === 'cart_add_error') {
  alert('Failed to add product: ' + event.data.error);
}
```

---

## 🔍 Отладка

Если не работает, проверьте:

1. **iframe найден?**
   ```javascript
   console.log(document.querySelector('iframe[src*="anvil.app"]'));
   ```

2. **Кнопка найдена?**
   ```javascript
   console.log(document.querySelector('.artwork-section__cta_desktop'));
   ```

3. **Сообщения приходят?**
   - В консоли должно быть: `CLIENT: Received postMessage: ...`

4. **Есть ли товары?**
   - Убедитесь, что вы сгенерировали artwork перед кликом на кнопку

---

## 📝 Примечания

- ✅ Работает с любым количеством сгенерированных товаров
- ✅ Всегда добавляет **последний созданный** товар (в центре)
- ✅ Безопасно для production (postMessage стандартный API)
- ✅ Не требует изменений в Shopify theme кроме одного скрипта

---

## 🚀 Готовый код для копирования

```html
<!-- Вставьте этот код ПОСЛЕ iframe в вашем Shopify theme -->
<script>
(function() {
  const iframe = document.querySelector('iframe[src*="anvil.app"]');
  const btn = document.querySelector('.artwork-section__cta.artwork-section__cta_desktop');
  
  if (iframe && btn) {
    btn.onclick = (e) => {
      e.preventDefault();
      iframe.contentWindow.postMessage({action: 'add_active_to_cart'}, '*');
    };
    
    window.addEventListener('message', (e) => {
      if (e.data?.action === 'cart_add_success') {
        console.log('✓ Added to cart');
        // Добавьте здесь открытие корзины или редирект
      }
    });
  }
})();
</script>
```


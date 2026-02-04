// ============================================
// СКРИПТ ДЛЯ СТРАНИЦЫ SHOPIFY
// Добавьте этот код в theme.liquid или в секцию страницы с iframe
// ============================================

(function() {
  console.log('🎨 String Art - Cart integration script loaded');

  // Ждем, когда iframe загрузится
  window.addEventListener('message', function(event) {
    const data = event.data;
    
    // Проверяем, что это наше сообщение от Anvil iframe
    if (!data || typeof data !== 'object') {
      return;
    }

    console.log('📨 Received postMessage:', data);

    // ========================================
    // ОБРАБОТКА ДОБАВЛЕНИЯ В КОРЗИНУ
    // Когда пользователь нажимает "Add to cart" ВНУТРИ iframe
    // ========================================
    if (data.action === 'add' && data.variant_id) {
      console.log('🛒 Adding to cart:', {
        variant_id: data.variant_id,
        anvil_id: data.anvil_id,
        add_frame: data.add_frame,
        frame_id: data.frame_id
      });

      // Формируем данные для добавления в корзину
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
        console.log('🖼️ Adding frame to cart as well');
      }

      // Добавляем товар(ы) в корзину через Shopify Cart API
      console.log('🚀 Sending request to /cart/add.js with body:', JSON.stringify({ items: items }));
      
      fetch('/cart/add.js', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: items })
      })
      .then(response => {
        console.log('📡 Response status:', response.status, response.statusText);
        
        // Проверяем статус ответа
        if (!response.ok) {
          return response.json().then(errorData => {
            console.error('❌ Server returned error:', errorData);
            throw new Error(errorData.description || errorData.message || 'Failed to add to cart');
          });
        }
        
        return response.json();
      })
      .then(data => {
        console.log('✅ Successfully added to cart:', data);
        
        // Отправляем подтверждение обратно в iframe
        event.source.postMessage({
          action: 'cart_add_success',
          variant_id: data.variant_id || data.id
        }, '*');

        // Опция 1: Открываем корзину (если используется cart drawer)
        if (typeof Shopify !== 'undefined' && Shopify.CartDrawer) {
          Shopify.CartDrawer.open();
        }
        // Опция 2: Редирект на страницу корзины (раскомментируйте если нужно)
        else {
          window.location.href = '/cart';
        }

        // Опция 3: Показываем уведомление (если есть на вашей теме)
        // theme.showQuickCart && theme.showQuickCart();
      })
      .catch(error => {
        console.error('❌ Error adding to cart:', error);
        
        // Отправляем ошибку обратно в iframe
        event.source.postMessage({
          action: 'cart_add_error',
          error: error.message || 'Failed to add to cart'
        }, '*');

        alert('Failed to add product to cart: ' + error.message);
      });
    }

    // ========================================
    // ОБРАБОТКА ДРУГИХ СОБЫТИЙ (если нужно)
    // ========================================
    else if (data.action === 'cart_add_success') {
      console.log('✅ Cart operation confirmed by iframe');
    }
    else if (data.action === 'cart_add_error') {
      console.error('❌ Cart error from iframe:', data.error);
    }
  });

  console.log('✓ PostMessage listener registered for iframe cart operations');
})();




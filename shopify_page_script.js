// ============================================
// СКРИПТ ДЛЯ СТРАНИЦЫ SHOPIFY
// Добавьте этот код в theme.liquid или в секцию страницы с iframe
// ============================================

(function() {
  console.log('🎨 String Art - Cart integration script loaded (Line Item Properties version)');

  // Хранилище для кастомных изображений (по line item key)
  window.customArtImages = window.customArtImages || {};

  // ========================================
  // ФУНКЦИЯ: Замена изображения на странице продукта
  // ========================================
  function replaceProductPageImage(imageUrl) {
    console.log('🖼️ Replacing product page image with:', imageUrl);
    
    // Пробуем несколько селекторов (от специфичного к общему)
    const selectors = [
      '.product__gallery-container .product__media img',
      '.product__gallery-container .product__media-list img',
      '.product__media[data-media-type="image"] img',
      '.product__media-list img',
      '.product-single__photo img',
      '[data-product-single-media-wrapper] img'
    ];
    
    let totalReplaced = 0;
    
    selectors.forEach(function(selector) {
      const images = document.querySelectorAll(selector);
      if (images.length > 0) {
        console.log('📍 Found ' + images.length + ' image(s) with selector: ' + selector);
        images.forEach(function(img) {
          console.log('  - Current src: ' + img.src);
          console.log('  - New src: ' + imageUrl);
          
          // Заменяем src и srcset
          img.src = imageUrl;
          img.srcset = imageUrl;
          
          // Также заменяем data-src для lazy loading
          if (img.hasAttribute('data-src')) {
            img.setAttribute('data-src', imageUrl);
          }
          if (img.hasAttribute('data-srcset')) {
            img.setAttribute('data-srcset', imageUrl);
          }
          
          // Добавляем класс для отслеживания
          img.classList.add('custom-art-replaced');
          
          totalReplaced++;
        });
      }
    });
    
    if (totalReplaced > 0) {
      console.log('✅ Replaced ' + totalReplaced + ' product page image(s)');
      
      // Сохраняем URL в localStorage для восстановления после перезагрузки
      const variantId = getVariantIdFromUrl();
      if (variantId) {
        localStorage.setItem('custom_image_' + variantId, imageUrl);
        console.log('💾 Saved custom image URL to localStorage for variant ' + variantId);
      } else {
        console.warn('⚠️ Could not save to localStorage - no variant ID');
      }
      
      // Повторяем замену через 500мс и 1.5с на случай если theme перезаписывает
      setTimeout(function() {
        console.log('🔄 Re-applying image replacement (500ms delay)...');
        document.querySelectorAll('img.custom-art-replaced').forEach(function(img) {
          img.src = imageUrl;
          img.srcset = imageUrl;
        });
      }, 500);
      
      setTimeout(function() {
        console.log('🔄 Re-applying image replacement (1500ms delay)...');
        document.querySelectorAll('img.custom-art-replaced').forEach(function(img) {
          img.src = imageUrl;
          img.srcset = imageUrl;
        });
      }, 1500);
      
    } else {
      console.error('❌ Product images not found on page with any selector!');
      console.log('🔍 Available images on page:');
      document.querySelectorAll('img').forEach(function(img, index) {
        if (index < 10) { // Показываем первые 10
          console.log('  [' + index + '] ' + img.className + ' - ' + img.src);
        }
      });
    }
  }

  // ========================================
  // ФУНКЦИЯ: Получение variant ID из URL
  // ========================================
  function getVariantIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('variant');
  }

  // ========================================
  // ФУНКЦИЯ: Восстановление изображения из localStorage
  // ========================================
  function restoreProductPageImage() {
    // Вариант 1: Пробуем получить variant ID из URL
    let variantId = getVariantIdFromUrl();
    
    // Вариант 2: Если нет в URL, пробуем найти на странице
    if (!variantId) {
      const variantInput = document.querySelector('input[name="id"], select[name="id"]');
      if (variantInput) {
        variantId = variantInput.value;
        console.log('📍 Found variant ID from form input: ' + variantId);
      }
    }
    
    // Вариант 3: Пробуем найти в скриптах Shopify
    if (!variantId) {
      try {
        const metaVariant = document.querySelector('meta[property="product:variant"]');
        if (metaVariant) {
          variantId = metaVariant.getAttribute('content');
          console.log('📍 Found variant ID from meta tag: ' + variantId);
        }
      } catch(e) {
        console.log('Could not find variant in meta tags');
      }
    }
    
    if (!variantId) {
      console.log('ℹ️ No variant ID found, skipping image restore');
      return;
    }

    const savedImageUrl = localStorage.getItem('custom_image_' + variantId);
    if (savedImageUrl) {
      console.log('🔄 Restoring custom image from localStorage for variant ' + variantId);
      console.log('🔗 Image URL: ' + savedImageUrl);
      replaceProductPageImage(savedImageUrl);
    } else {
      console.log('ℹ️ No saved custom image for variant ' + variantId);
      
      // Дополнительно: показываем все сохраненные ключи для отладки
      console.log('💾 Available localStorage keys:');
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('custom_image_')) {
          console.log('  - ' + key + ': ' + localStorage.getItem(key).substring(0, 50) + '...');
        }
      }
    }
  }

  // ========================================
  // ФУНКЦИЯ: Замена изображений в корзине и cart-drawer
  // ========================================
  function replaceCartImages() {
    console.log('🛒 Replacing cart images...');
    
    // Получаем текущую корзину для доступа к line item properties
    fetch('/cart.js')
      .then(response => response.json())
      .then(cart => {
        console.log('📦 Current cart:', cart);
        
        cart.items.forEach((item, index) => {
          // Проверяем наличие кастомного изображения в properties
          const imageProperty = item.properties && item.properties._image_url;
          
          if (imageProperty) {
            console.log(`🎨 Found custom image for item ${index}:`, imageProperty);
            
            // Заменяем в cart-drawer
            const cartDrawerItems = document.querySelectorAll('.horizontal-product__media');
            if (cartDrawerItems[index]) {
              const img = cartDrawerItems[index].querySelector('img');
              if (img) {
                img.src = imageProperty;
                img.srcset = imageProperty;
                console.log(`✅ Replaced cart-drawer image for item ${index}`);
              }
            }
            
            // Заменяем на странице корзины (/cart)
            const cartPageItems = document.querySelectorAll('.cart-item__media');
            if (cartPageItems[index]) {
              const img = cartPageItems[index].querySelector('img');
              if (img) {
                img.src = imageProperty;
                img.srcset = imageProperty;
                console.log(`✅ Replaced cart page image for item ${index}`);
              }
            }
          }
        });
      })
      .catch(error => {
        console.error('❌ Error fetching cart:', error);
      });
  }

  // ========================================
  // СЛУШАТЕЛЬ: Обновление корзины
  // ========================================
  document.addEventListener('cart:refresh', function() {
    console.log('🔄 Cart refresh event detected, replacing images...');
    setTimeout(replaceCartImages, 300); // Небольшая задержка для загрузки DOM
  });

  // Замена изображений при загрузке страницы (для /cart)
  if (window.location.pathname.includes('/cart')) {
    setTimeout(replaceCartImages, 500);
  }

  // ========================================
  // НОВОЕ: Замена изображений при открытии/загрузке cart-drawer
  // ========================================
  
  // Наблюдаем за изменениями DOM для обнаружения открытия cart-drawer
  const cartDrawerObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      // Проверяем, появился ли cart-drawer в DOM
      if (mutation.addedNodes && mutation.addedNodes.length > 0) {
        for (let i = 0; i < mutation.addedNodes.length; i++) {
          const node = mutation.addedNodes[i];
          // Ищем элементы корзины
          if (node.nodeType === 1 && (
            node.classList && (
              node.classList.contains('cart-drawer') ||
              node.classList.contains('drawer') ||
              node.querySelector && node.querySelector('.horizontal-product__media')
            )
          )) {
            console.log('🔔 Cart drawer opened/updated, replacing images...');
            setTimeout(replaceCartImages, 300);
            break;
          }
        }
      }
      
      // Также проверяем изменения атрибутов (например, открытие drawer через класс)
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const target = mutation.target;
        if (target.classList && (
          target.classList.contains('cart-drawer') ||
          target.classList.contains('drawer')
        ) && target.classList.contains('is-open')) {
          console.log('🔔 Cart drawer opened via class change, replacing images...');
          setTimeout(replaceCartImages, 300);
        }
      }
    });
  });

  // Начинаем наблюдение за изменениями в body
  cartDrawerObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'open', 'data-open']
  });

  // ========================================
  // НОВОЕ: Замена изображений при загрузке страницы
  // ========================================
  window.addEventListener('load', function() {
    console.log('🌐 Page loaded, checking for cart items and product images...');
    
    // Восстанавливаем изображение на странице продукта (если есть)
    restoreProductPageImage();
    
    // Пробуем еще раз через 500мс (на случай если DOM еще не готов)
    setTimeout(restoreProductPageImage, 500);
    
    // И еще раз через 1.5 секунды (для медленных соединений)
    setTimeout(restoreProductPageImage, 1500);
    
    // Заменяем изображения в корзине
    setTimeout(replaceCartImages, 1000);
  });
  
  // ========================================
  // ДОПОЛНИТЕЛЬНО: Попытка при DOMContentLoaded
  // ========================================
  document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM ready, attempting to restore product image...');
    setTimeout(restoreProductPageImage, 100);
  });

  // ========================================
  // НОВОЕ: Отслеживание изменений внутри CartDrawer
  // ========================================
  function observeCartDrawer() {
    const cartDrawer = document.getElementById('CartDrawer');
    if (cartDrawer) {
      console.log('👁️ Setting up observer for #CartDrawer');
      let debounceTimer = null;
      
      const cartContentObserver = new MutationObserver(function(mutations) {
        // Используем debounce чтобы не вызывать replaceCartImages слишком часто
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
          console.log('🔄 CartDrawer content changed, replacing images...');
          replaceCartImages();
        }, 200);
      });
      
      cartContentObserver.observe(cartDrawer, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'data-quantity', 'src']
      });
    } else {
      // Если CartDrawer еще не существует, пробуем позже
      setTimeout(observeCartDrawer, 1000);
    }
  }
  
  // Запускаем наблюдение за CartDrawer
  observeCartDrawer();

  // ========================================
  // СЛУШАТЕЛЬ: Сообщения от Anvil iframe
  // ========================================
  window.addEventListener('message', function(event) {
    const data = event.data;
    
    // Проверяем, что это наше сообщение от Anvil iframe
    if (!data || typeof data !== 'object') {
      return;
    }

    console.log('📨 Received postMessage:', data);
    
    // ОТЛАДКА: Показываем тип и содержимое data
    if (data.action) {
      console.log('✅ Found action:', data.action);
    } else {
      console.log('⚠️ No action field in postMessage');
    }

    // ========================================
    // ОБРАБОТКА ДОБАВЛЕНИЯ В КОРЗИНУ
    // Когда пользователь нажимает "Add to cart" ВНУТРИ iframe
    // ========================================
    if (data.action === 'add' && data.variant_id) {
      console.log('🛒 Adding to cart with custom image:', {
        variant_id: data.variant_id,
        anvil_id: data.anvil_id,
        image_url: data.image_url,
        add_frame: data.add_frame,
        frame_id: data.frame_id
      });

      // ВАЖНО: Сначала заменяем изображение на странице продукта
      if (data.image_url) {
        console.log('🎯 Calling replaceProductPageImage with URL:', data.image_url);
        replaceProductPageImage(data.image_url);
      } else {
        console.error('❌ No image_url in postMessage data!');
      }

      // Формируем данные для добавления в корзину
      const items = [{
        id: String(data.variant_id),
        quantity: 1,
        properties: {
          '_image_url': data.image_url,  // Сохраняем URL изображения
          '_anvil_id': data.anvil_id     // Сохраняем Anvil ID
        }
      }];

      console.log('🔍 Debug: add_frame =', data.add_frame);
      console.log('🔍 Debug: frame_id =', data.frame_id);

      // Если нужно добавить рамку
      if (data.add_frame && data.frame_id) {
        items.push({
          id: String(data.frame_id),
          quantity: 1
        });
        console.log('🖼️ Adding frame to cart as well');
      } else {
        console.log('⏭️ Skipping frame (add_frame=' + data.add_frame + ')');
      }

      console.log('📦 Final items array:', JSON.stringify(items));

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

        console.log('Cart updated:', data);
        
        // Запускаем обновление корзины и открываем cart-drawer
        document.dispatchEvent(new CustomEvent('cart:refresh', {
          bubbles: true, 
          detail: { open: true }
        }));
        
        // Заменяем изображения после добавления в корзину
        setTimeout(replaceCartImages, 500);
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

  console.log('✓ PostMessage listener registered for iframe cart operations (Line Item Properties)');
})();




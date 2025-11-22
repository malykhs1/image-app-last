// Код для внешней кнопки Add to cart в Shopify
// Добавьте этот скрипт на страницу Shopify, где находится iframe

(function() {
  // Находим iframe с Anvil приложением
  const iframe = document.querySelector('iframe[src*="anvil.app"]');
  
  if (!iframe) {
    console.error('Anvil iframe not found');
    return;
  }

  // Находим внешнюю кнопку Add to cart
  const externalButton = document.querySelector('.artwork-section__cta.artwork-section__cta_desktop');
  
  if (!externalButton) {
    console.error('External Add to cart button not found');
    return;
  }

  // Обработчик клика на внешнюю кнопку
  externalButton.addEventListener('click', function(e) {
    e.preventDefault(); // Предотвращаем стандартное поведение
    
    console.log('External Add to cart button clicked, sending message to iframe...');
    
    // Отправляем сообщение в iframe
    iframe.contentWindow.postMessage({
      action: 'add_active_to_cart'
    }, '*');
  });

  // Слушаем ответы от iframe
  window.addEventListener('message', function(event) {
    const data = event.data;
    
    if (data && typeof data === 'object') {
      if (data.action === 'cart_add_success') {
        console.log('Product added to cart successfully:', data.variant_id);
        
        // Можно добавить визуальную обратную связь
        externalButton.textContent = 'Added! ✓';
        externalButton.style.background = '#4CAF50';
        
        setTimeout(() => {
          externalButton.textContent = 'Add to cart';
          externalButton.style.background = ''; // Вернуть исходный цвет
        }, 2000);
        
      } else if (data.action === 'cart_add_error') {
        console.error('Error adding to cart:', data.error);
        alert('Failed to add product to cart: ' + data.error);
      }
    }
  });

  console.log('External Add to cart button listener registered');
})();


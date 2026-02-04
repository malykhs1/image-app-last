from ._anvil_designer import CreationTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..AddFramePopup import AddFramePopup

WH_IMG_CARD = 350

def send_add_to_cart(variant_id, anvil_id, add_frame):
  """Добавляем товар в корзину Shopify"""
  frame_variant = 43092453359731 # product id 8003777167475

  # Получаем текущий URL приложения динамически
  app_origin = anvil.server.get_app_origin()

  # 1. Отправляем postMessage родительскому окну (для совместимости)
  message = {
    'sender': app_origin,  # Динамический URL приложения
    'action': 'add',
    'variant_id': str(variant_id),  # Передаем как строку
    'anvil_id': anvil_id,
    'add_frame': add_frame,  # Возвращаем обратно
    'frame_id': str(frame_variant),  # Передаем как строку
  }
  print("Sending postMessage to parent window: " + str(message))
  anvil.js.window.parent.postMessage(message, '*')

  # postMessage отправлено - родительское окно должно обработать его
  # и открыть cart-drawer автоматически

class Creation(CreationTemplate):
  def __init__(self, locale, is_in_grid=False, grid_index=None, on_click_callback=None, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Уменьшаем размер для grid карточек
    if is_in_grid:
      self.image_1.height = 200  # Меньше для превью
      # Добавляем роль к текущей роли компонента
      current_role = self.role or ''
      self.role = (current_role + ' grid-creation-card').strip()
    else:
      self.image_1.height = WH_IMG_CARD
    # self.image_1.width = WH_IMG_CARD
    self.image_1.source = self.item['out_image_medium']
    length_meters = int(self.item['wire_len_km']*1000)
    self.text_length.text = 'String length: ' + str(length_meters) + ' meters'
    self.locale = locale
    
    # Сохраняем параметры для grid
    self.is_in_grid = is_in_grid
    self.grid_index = grid_index
    self.on_click_callback = on_click_callback
    
    # Если это карточка в grid, добавляем обработчик клика на изображение
    if is_in_grid and on_click_callback:
      self.image_1.role = 'clickable-creation'
      # Добавляем JavaScript обработчик клика на изображение
      from anvil.js import get_dom_node
      try:
        img_node = get_dom_node(self.image_1)
        def click_handler(event):
          print("Creation image clicked, calling callback with index " + str(grid_index))
          on_click_callback(grid_index)
        img_node.onclick = click_handler
        img_node.style.cursor = 'pointer'
      except Exception as e:
        print("Error setting up click handler: " + str(e))

    if locale == 'he':
      self.button_add_to_cart.text = 'הוספה לעגלה'
      self.button_add_to_cart.font = 'Rubik'
      self.text_length.text = 'אורך חוט: ' + str(length_meters) + ' מטרים'
      self.text_length.font = 'Rubik'

  def button_add_to_cart_click(self, **event_args):
    self.linear_progress_cart.visible = True
    self.spacer_bottom.visible = True
    self.button_add_to_cart.visible = False

    try:
      task = anvil.server.call_s('launch_add_to_cart_task', self.item, self.locale)

      popup = AddFramePopup(locale=self.locale)
      add_frame = alert(content=popup, large=True, buttons=[])
      if add_frame is None:
        add_frame = False

      while task.is_completed() is False:
        waitHere = 1

      # Получаем результат: variant_id, anvil_id
      variant_id, anvil_id = task.get_return_value()

      print("Received variant_id: " + str(variant_id) + ", anvil_id: " + str(anvil_id))

      # Отправляем postMessage родительскому окну для добавления в корзину
      send_add_to_cart(variant_id, anvil_id, add_frame)

      # Показываем сообщение об успехе
      if self.locale == 'he':
        alert("המוצר נוסף לעגלה בהצלחה!", title="הצלחה")
      else:
        alert("Product added to cart successfully!", title="Success")

    except Exception as e:
      print("Error adding to cart: " + str(e))
      if self.locale == 'he':
        alert("נכשל בהוספת מוצר לעגלה: " + str(e), title="שגיאה")
      else:
        alert("Failed to add product to cart: " + str(e), title="Error")

    finally:
      self.button_add_to_cart.visible = True
      self.linear_progress_cart.visible = False
      self.spacer_bottom.visible = False

  def link_delete_click(self, **event_args):
    """Удаляем товар из списка и обновляем отображение"""
    parent_form = get_open_form()
    
    # Удаляем товар из списка all_creations родительской формы
    if hasattr(parent_form, 'all_creations') and self.item in parent_form.all_creations:
      parent_form.all_creations.remove(self.item)
      print("CLIENT: Removed creation from list, remaining: " + str(len(parent_form.all_creations)))
    
    # Удаляем из базы данных
    anvil.server.call_s('delete_creation', self.item)
    
    # Обновляем отображение всех карточек
    if hasattr(parent_form, 'refresh_creations_display'):
      parent_form.refresh_creations_display()
    else:
      # Если refresh_creations_display недоступен, просто удаляем компонент
      self.remove_from_parent()


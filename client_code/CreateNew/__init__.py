from ._anvil_designer import CreateTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..Creation import Creation

import time
import anvil.js
from anvil.js import get_dom_node, call_js
from anvil.js.window import navigator

MAX_MB_IMG = 15
WH_IMG = 625
CARD_WIDTH = '360px'  

class Point():
  def __init__(self,x,y,rad,op_id):
    self.x = x
    self.y = y
    self.rad = rad
    self.op_id = op_id

class Create(CreateTemplate):
  def __init__(self, **properties):
    url_params = anvil.js.call_js('getUrlParams')
    self.locale = url_params.get('locale', 'en')
    self.current_step = 1  # Текущий этап: 1, 2 или 3
    self.brush_size = 10
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Check if userAgentData is available
    if hasattr(navigator, "userAgentData") and navigator.userAgentData is not None:
      platform = navigator.userAgentData.platform
    else:
      platform = navigator.userAgent  # Use userAgent string instead
    # Determine if the user is from mobile or PC
    self.is_mobile = any(p in platform for p in ["Android", "iPhone", "iPad", "iOS"])

    # Локализация
    if self.locale == 'he':
      self.file_loader_1.text = 'העלאת תמונה'
      self.file_loader_1.font_family = 'Rubik'
      self.button_create.text = 'צור הדמיית חוטים'
      self.button_create.font_family = 'Rubik'
      self.label_upload_title.text = 'העלה את התמונה שלך'
      self.label_upload_title.font_family = 'Rubik'
      self.label_upload_subtitle.text = 'אנו תומכים בקבצי png ו-jpg'
      self.label_upload_subtitle.font_family = 'Rubik'
      self.button_close.text = 'סגור'
      self.button_close.font_family = 'Rubik'
      self.step_indicator_1.text = '1/3    העלאת קובץ'
      self.step_indicator_1.font_family = 'Rubik'
      self.step_indicator_2.text = '2/3    התאמת חיתוך'
      self.step_indicator_2.font_family = 'Rubik'
      self.step_indicator_3.text = '3/3    קבל את היצירה שלך'
      self.step_indicator_3.font_family = 'Rubik'

    self.erase_mode = False
    self.enhance_mode = False
    self.pointer_xy = None
    self.erase_points = []
    self.enhance_points = []
    self.brush_size = 10
    self.curr_op_id = 0
    self.ops_history = []

    if self.is_mobile:
      if self.locale == 'he':
        self.up_image_obj = anvil.URLMedia(anvil.server.get_app_origin() + "/_/theme/uploadImageHe.png")
      else:
        self.up_image_obj = anvil.URLMedia(anvil.server.get_app_origin() + "/_/theme/uploadImage.png")
    else:
      if self.locale == 'he':
        self.up_image_obj = anvil.URLMedia(anvil.server.get_app_origin() + "/_/theme/uploadImageDragHe.png")
      else:
        self.up_image_obj = anvil.URLMedia(anvil.server.get_app_origin() + "/_/theme/uploadImageDrag.png")
    self.img = None
    self.mvRatio = 1
    self.resetMoveAndZoom()  
    self.cvsW = 300
    self.canvas_1.height = self.cvsW
    self.canvas_1.width = self.cvsW
    self.canvas_1.remove_from_parent()
    self.flow_panel_canvas.add_component(self.canvas_1)
    self.canvas_1.visible = False  # Скрываем canvas до загрузки изображения
    self.drawCanvas()
    self.setup_drag_and_drop()

    # Очищаем старые creations (если есть)
    for comp in self.flow_panel_creations.get_components():
      comp.remove_from_parent()

    # Устанавливаем начальный этап
    self.set_step(1)

  def form_show(self, **event_args):
    """This method is called when the form is shown on the page"""
    pass

  # Методы управления этапами
  def set_step(self, step):
    """Переключение между этапами"""
    print(f"CLIENT: set_step({step}) called")
    print(f"CLIENT: Creations in flow_panel before set_step: {len(self.flow_panel_creations.get_components())}")
    self.current_step = step

    # Скрываем все панели
    self.step1_panel.visible = False
    self.step2_panel.visible = False
    self.flow_panel_creations.visible = False

    # Обновляем индикаторы этапов
    self.step_indicator_1.role = 'step-inactive'
    self.step_indicator_1.bold = False
    self.step_indicator_2.role = 'step-inactive'
    self.step_indicator_2.bold = False
    self.step_indicator_3.role = 'step-inactive'
    self.step_indicator_3.bold = False

    # Показываем нужную панель и активируем индикатор
    if step == 1:
      self.step1_panel.visible = True
      self.step_indicator_1.role = 'step-active'
      self.step_indicator_1.bold = True
      self.button_close.visible = False
    elif step == 2:
      self.step2_panel.visible = True
      self.step_indicator_2.role = 'step-active'
      self.step_indicator_2.bold = True
      self.button_close.visible = True
      self.canvas_1.visible = True
      self.flow_panel_canvas.visible = True  # Показываем canvas panel
      self.flow_panel_zoom.visible = True
      self.button_create.visible = True
      self.drawCanvas()
    elif step == 3:
      self.flow_panel_creations.visible = True
      self.step_indicator_3.role = 'step-active'
      self.step_indicator_3.bold = True
      self.button_close.visible = True
      # Скрываем canvas и элементы управления на этапе 3
      self.flow_panel_canvas.visible = False
      self.flow_panel_zoom.visible = False
      self.button_create.visible = False

  def step_indicator_1_click(self, **event_args):
    """Переход к этапу 1"""
    self.set_step(1)

  def step_indicator_2_click(self, **event_args):
    """Переход к этапу 2"""
    if self.img is not None:  # Можно перейти только если изображение загружено
      self.set_step(2)

  def step_indicator_3_click(self, **event_args):
    """Переход к этапу 3"""
    if len(self.flow_panel_creations.get_components()) > 0:  # Есть результаты
      self.set_step(3)

  def button_close_click(self, **event_args):
    """Закрытие: на 3-м этапе -> к этапу 2, на 2-м этапе -> к этапу 1"""
    print(f"CLIENT: button_close_click, current_step={self.current_step}")
    if self.current_step == 3:
      # С третьего этапа возвращаемся ко второму
      self.set_step(2)
    else:
      # Со второго этапа возвращаемся к первому и сбрасываем изображение
      self.img = None
      self.resetMoveAndZoom()
      self.canvas_1.visible = False
      self.set_step(1)

  def setup_drag_and_drop(self):
    drop_panel_node = get_dom_node(self.flow_panel_canvas)
    call_js("setUpListeners", drop_panel_node)

  def refresh_creations(self, my_creations):
    #my_creations = anvil.server.call('get_my_creations')
    for comp in self.flow_panel_creations.get_components():
      comp.remove_from_parent()
    for c in my_creations.search(tables.order_by('created_at', ascending=False)):
      self.flow_panel_creations.add_component(Creation(locale=self.locale,item=c), width=CARD_WIDTH)

  def handle_drag_drop(self, content_type, data, name):
    if 'image' in content_type:
      data = bytes([ord(c) for c in data])
      dropped_file = BlobMedia(content_type, data, name=name)
      self.file_loaded(dropped_file)
    else:
      alert("File must be an image!")

  def file_loader_1_change(self, file, **event_args):
    self.file_loaded(file)

  def file_loaded(self,file):
    """This method is called when a new file is loaded into this FileLoader"""
    if file is None:
      return
    if file.length < MAX_MB_IMG*1024*1024:
      self.img = file
      self.imgW, self.imgH = anvil.image.get_dimensions(self.img)
      self.minWH = min(self.imgW,self.imgH)
      self.resetMoveAndZoom()
      self.mvRatio = self.minWH/self.canvas_1.width
      self.drawCanvas()
      # Автоматически переходим к этапу 2 после загрузки изображения
      self.set_step(2)
    else:
      alert(f"Maximal size is {MAX_MB_IMG} MB",title="File size too large",large=True,dismissible=False)


  ##### CALL SERVER FUNC #####
  def button_create_click(self, **event_args):
    print(f"CLIENT: button_create_click called")
    print(f"CLIENT: Current creations in UI BEFORE: {len(self.flow_panel_creations.get_components())}")

    # Защита от двойного нажатия
    if hasattr(self, 'is_creating') and self.is_creating:
      print("CLIENT: Already creating, ignoring duplicate click")
      return

    self.is_creating = True
    print("CLIENT: Starting creation process...")

    speedText = "very fast"
    effectIntensity = 2
    effectType = "clahe"
    noMask = True
    mask_img = None
    cloth = False
    discDiam = 400

    #sub-rect of image we want to run on (l,t,r,b)
    zoom = self.zoom + self.dz
    left = round(self.sx+self.dx)
    top = round(self.sy+self.dy)
    right = left + int(self.minWH*zoom)
    bot = top + int(self.minWH*zoom)

    subRect = (left,top,right,bot)
    cropped_img = self.get_cropped_img()

    paramsDict = {"speedText": speedText, "effectType": effectType, "effectIntensity": effectIntensity,
                  "cloth": cloth, "noMask": noMask, "subRect": subRect, "discDiam": discDiam}

    self.linear_progress.visible = True
    self.spacer_progress.visible = True
    self.button_create.visible = False
    ############# call SERVER function ################
    print(f"CLIENT: Calling server create() for {self.img.name}")
    try:
      row = anvil.server.call('create',cropped_img,paramsDict,mask_img,self.img.name) #nLines,resMediaImg
      print(f"CLIENT: Server returned row with ID: {row.get_id()}")
    except Exception as e:
      print(e)
      self.linear_progress.visible = False
      self.spacer_progress.visible = False
      self.button_create.visible = True
      self.is_creating = False  # Разрешаем повторное нажатие после ошибки
      # Telegram отключен
      # anvil.server.call('send_telegram_message','Someone is trying to create and server is down!')
      alert('The server is currently unreachable. Please try again soon.')
      return

    self.linear_progress.visible = False
    self.spacer_progress.visible = False
    self.button_create.visible = True
    self.is_creating = False  # Разрешаем повторное нажатие после завершения

    #display results
    print(f"CLIENT: Adding creation to UI, row ID: {row.get_id()}")
    comp = Creation(locale=self.locale,item=row)
    self.flow_panel_creations.add_component(comp, width=CARD_WIDTH, index=0)
    print(f"CLIENT: Total creations in UI: {len(self.flow_panel_creations.get_components())}")

    # Автоматически переходим к этапу 3 после генерации
    self.set_step(3)

    #on mobile - scroll to the result
    if self.is_mobile:
      anvil.js.window.setTimeout(lambda: comp.scroll_into_view(), 100)


  def drop_down_effect_change(self, **event_args):
    """This method is called when an item is selected"""
    shouldDisplay = self.drop_down_effect.selected_value == "Effect1"
    print(shouldDisplay)
    #self.text_strength.enabled = shouldDisplay
    self.text_strength.visible = shouldDisplay
    self.label_strength.visible = shouldDisplay

  def drop_down_to_show_change(self, **event_args):
    #self.refresh_creations()
    show_all = self.drop_down_to_show.selected_value == "All"
    components = self.flow_panel_creations.get_components()
    for c in components:
      if show_all:
        c.visible = True
      else:
        c.visible = c.liked

  def drop_down_mask_change(self, **event_args):
    is_manual = self.drop_down_mask.selected_value == "Manual mask"
    self.flow_panel_mask.visible = is_manual
    if not is_manual:
      self.button_drag_click()
    is_auto = self.drop_down_mask.selected_value == "Auto mask"
    self.check_box_cloth.visible = is_auto
    self.check_box_1.visible = is_auto

  ################# CANVAS #######################################################################################################


  def resetMoveAndZoom(self):
    self.sx = 0
    self.sy = 0
    self.dx = 0
    self.dy = 0
    self.zoom = 1
    self.dz = 0
    self.dragging = False
    self.zooming = False
    self.erase_points = []
    self.enhance_points = []

  ## CANVAS drawing
  def drawCanvas(self):
    # Reset and clear the canvas
    self.canvas_1.global_composite_operation = "source-over"
    self.canvas_1.clear_rect(0,0,self.canvas_1.get_width(), self.canvas_1.get_height())

    if self.img is None:
      self.canvas_1.draw_image_part(self.up_image_obj,0,0,1024,1024,
                                    0,0,self.canvas_1.width,self.canvas_1.height)
    else:
      zoom = self.zoom + self.dz
      #self.canvas_1.global_alpha = 1

      #background image
      self.canvas_1.draw_image_part(self.img,self.sx+self.dx,self.sy+self.dy,self.minWH*zoom,self.minWH*zoom,
                                    0,0,self.canvas_1.width,self.canvas_1.height)

      # mask - highlighted
      self.canvas_1.global_composite_operation = "screen"
      for point in self.enhance_points:
        self.canvas_1.begin_path()
        self.canvas_1.arc(point.x,point.y,point.rad)
        self.canvas_1.fill_style = 'red'
        self.canvas_1.fill()

      #mask only inside big circle
      # For compositing reference, see: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation
      self.canvas_1.global_composite_operation = "destination-in"
      self.canvas_1.begin_path()
      self.canvas_1.arc(self.canvas_1.width/2,self.canvas_1.height/2,self.canvas_1.width/2-1)
      self.canvas_1.fill_style = 'black'
      self.canvas_1.fill()

      # mask - erased
      self.canvas_1.global_composite_operation = "destination-out"
      for point in self.erase_points:
        self.canvas_1.begin_path()
        self.canvas_1.arc(point.x,point.y,point.rad)
        self.canvas_1.fill()

      #large circle stroke (blue)
      self.canvas_1.global_composite_operation = "source-over"
      self.canvas_1.begin_path()
      self.canvas_1.arc(self.canvas_1.width/2,self.canvas_1.height/2,self.canvas_1.width/2-1)
      self.canvas_1.stroke_style = "#1f1f1f" # "#2196F3"
      self.canvas_1.line_width = 1
      self.canvas_1.stroke()

      #small pointer circle stroke (white-difference)
      if self.pointer_xy is not None and (self.erase_mode or self.enhance_mode):
        self.canvas_1.global_composite_operation = "difference"
        self.canvas_1.begin_path()
        self.canvas_1.arc(self.pointer_xy[0],self.pointer_xy[1],self.brush_size)
        self.canvas_1.stroke_style = 'white'
        self.canvas_1.line_width = 1
        self.canvas_1.stroke()

      self.canvas_1.global_composite_operation = "source-over"

  def get_cropped_img(self):
    new_size = WH_IMG
    self.canvas_1.height = new_size
    self.canvas_1.width = new_size
    self.canvas_1.reset_context()
    self.canvas_1.clear_rect(0,0,self.canvas_1.get_width(), self.canvas_1.get_height())

    self.canvas_1.global_composite_operation = "source-over"
    zoom = self.zoom + self.dz
    self.canvas_1.draw_image_part(self.img,self.sx+self.dx,self.sy+self.dy,self.minWH*zoom,self.minWH*zoom,
                                  0,0,self.canvas_1.width,self.canvas_1.height)
    cropped_img = self.canvas_1.get_image()

    self.canvas_1.height = self.cvsW
    self.canvas_1.width = self.cvsW
    self.canvas_1.reset_context()
    self.drawCanvas()
    return cropped_img

  def generate_mask_img(self):
    #erase
    self.canvas_1.global_composite_operation = "source-over"
    self.canvas_1.clear_rect(0,0,self.canvas_1.get_width(), self.canvas_1.get_height())

    # fill large circle gray
    self.canvas_1.arc(self.canvas_1.width/2,self.canvas_1.height/2,self.canvas_1.width/2-4)
    val = 128
    self.canvas_1.fill_style = f'rgb({val},{val},{val})'
    self.canvas_1.fill()

    # fill highlighted with white
    self.canvas_1.global_composite_operation = "source-atop"
    self.canvas_1.fill_style = 'white'
    for point in self.enhance_points:
      self.canvas_1.begin_path()
      self.canvas_1.arc(point.x,point.y,point.rad)
      self.canvas_1.fill()

    # fill erased with black
    self.canvas_1.global_composite_operation = "source-over"
    self.canvas_1.fill_style = 'black'
    for point in self.erase_points:
      self.canvas_1.begin_path()
      self.canvas_1.arc(point.x,point.y,point.rad)
      self.canvas_1.fill()

    # fill black background behind
    self.canvas_1.global_composite_operation = "destination-over"
    self.canvas_1.fill_style = 'black'
    self.canvas_1.fill_rect(0,0,self.canvas_1.get_width(), self.canvas_1.get_height())

    mask_img = self.canvas_1.get_image()
    self.drawCanvas()
    return mask_img

  def clipXY(self):
    odx = self.dx
    ody = self.dy
    if self.sx + self.dx < 0:
      self.dx = -self.sx
    if self.sy + self.dy < 0:
      self.dy = -self.sy
    zoom = self.zoom + self.dz
    if self.sx + self.dx + self.minWH*zoom > self.imgW - 1:
      self.dx = self.imgW - self.sx - self.minWH*zoom - 1
    if self.sy + self.dy + self.minWH*zoom > self.imgH - 1:
      self.dy = self.imgH - self.sy - self.minWH*zoom - 1
    return self.dx-odx,self.dy-ody

  def clipZoom(self):
    if self.zoom+self.dz > 1:
      self.dz = 1-self.zoom
    if self.zoom+self.dz<0.1:
      self.dz = 0.1-self.zoom

  def move_canvas(self,x,y):
    self.dx = (self.xds - x)*self.mvRatio*self.zoom
    self.dy = (self.yds - y)*self.mvRatio*self.zoom
    self.clipXY()
    self.saveXY()
    self.xds = x
    self.yds = y

  def move_points(self,dx,dy):
    factor = 1/(self.mvRatio*(self.zoom+self.dz))
    dx = dx*factor
    dy = dy*factor
    for point in self.erase_points:
      point.x -= dx
      point.y -= dy
    for point in self.enhance_points:
      point.x -= dx
      point.y -= dy

  def saveXY(self,zooming=False):
    self.sx = self.sx + self.dx
    self.sy = self.sy + self.dy
    if not zooming:
      self.move_points(self.dx,self.dy)
    self.dx = 0
    self.dy = 0

  def scale_point(self,point,center,scale):
    point.x = center + scale*(point.x-center)
    point.y = center + scale*(point.y-center)
    point.rad = scale*point.rad

  def scale_points(self):
    halfW = self.canvas_1.get_width()/2
    scale = self.zoom/(self.zoom+self.dz)
    for point in self.erase_points:
      self.scale_point(point,halfW,scale)
    for point in self.enhance_points:
      self.scale_point(point,halfW,scale)

  def zoom_canvas(self,dz):
    self.dz = dz
    #clip zoom
    self.clipZoom()

    self.dx = -(self.dz)*self.minWH/2
    self.dy = -(self.dz)*self.minWH/2

    self.scale_points()

    dx,dy = self.clipXY()
    self.move_points(dx,dy)
    self.saveXY(zooming=True)

  def save_zoom_canvas(self,dz):
    dz = self.zoom*dz
    self.zoom_canvas(dz)
    self.zoom = self.zoom + self.dz
    self.dz = 0

  ## CANVAS SIGNALS

  #canvas reset
  def canvas_1_reset(self, **event_args):
    self.drawCanvas()

  def new_op(self):
    self.curr_op_id += 1
    self.ops_history.append(self.curr_op_id)

  def in_circle(self,x,y):
    cX = self.canvas_1.width/2
    cY = self.canvas_1.height/2
    r_2 = cX*cX
    if (x-cX)*(x-cX) + (y-cY)*(y-cY) < r_2:
      return True
    return False

  #mouse press
  def canvas_1_mouse_down(self, x, y, button, **event_args):
    if self.img is None:
      self.file_loader_1.open_file_selector()
      return
    if button == 2:
      self.zooming = True
      self.zys = y
    else:# button == 1:
      if self.erase_mode:
        self.new_op()
        self.erase_points.append(Point(x,y,self.brush_size,self.curr_op_id))
      elif self.enhance_mode:
        self.new_op()
        self.enhance_points.append(Point(x,y,self.brush_size,self.curr_op_id))
      if self.in_circle(x,y):
        self.dragging = True
        self.xds = x
        self.yds = y

  #mouse release
  def canvas_1_mouse_up(self, x, y, button, **event_args):
    if self.img is None:
      return
    if button == 2 and self.zooming:
      self.zooming = False
      self.save_zoom_canvas((y-self.zys)/500)
      self.drawCanvas()
    if button != 2 and self.dragging:
      self.dragging = False
      if not self.erase_mode and not self.enhance_mode:
        self.move_canvas(x,y)
      self.drawCanvas()

  #mouse leave
  def canvas_1_mouse_leave(self, x, y, **event_args):
    self.pointer_xy = None
    if self.dragging:
      self.dragging = False
      if not self.erase_mode and not self.enhance_mode:
        self.move_canvas(x,y)      
    if self.zooming:
      self.zooming = False
      self.save_zoom_canvas((y-self.zys)/500)
    self.drawCanvas()

  def canvas_1_mouse_move(self, x, y, **event_args):
    if self.img is None:
      return
    need_redraw = False
    if self.erase_mode or self.enhance_mode:
      self.pointer_xy = [x,y]
      need_redraw = True
    #moving
    if self.dragging:
      if self.erase_mode:
        self.erase_points.append(Point(x,y,self.brush_size,self.curr_op_id))
      elif self.enhance_mode:
        self.enhance_points.append(Point(x,y,self.brush_size,self.curr_op_id))
      else:
        self.move_canvas(x,y)
      need_redraw = True
    #zooming
    if self.zooming:
      self.save_zoom_canvas((y-self.zys)/500)
      need_redraw = True
    if need_redraw:
      self.drawCanvas()

  def button_plus_click(self, **event_args):
    if self.img is not None:
      self.save_zoom_canvas(-0.1)
      self.drawCanvas()


  def button_minus_click(self, **event_args):
    if self.img is not None:
      self.save_zoom_canvas(0.1)
      self.drawCanvas()

  def button_reset_mask_click(self, **event_args):
    self.erase_points = []
    self.enhance_points = []
    self.drawCanvas()

  def refresh_edit_mode(self):
    self.button_mask_eraser.foreground = 'theme:Black' if self.erase_mode else ''
    self.button_mask_enhancer.foreground = 'theme:Black' if self.enhance_mode else ''
    self.button_drag.foreground = '' if self.enhance_mode or self.erase_mode else 'theme:Black'
    if self.erase_mode or self.enhance_mode:
      self.canvas_1.role = 'canvas-none'
    else:
      self.canvas_1.role = 'canvas-grab'

  def button_mask_eraser_click(self, **event_args):
    self.erase_mode = not self.erase_mode
    self.enhance_mode = False
    self.refresh_edit_mode()
    self.drawCanvas()

  def button_mask_enhancer_click(self, **event_args):
    self.enhance_mode = not self.enhance_mode
    self.erase_mode = False
    self.refresh_edit_mode()
    self.drawCanvas()

  def button_drag_click(self, **event_args):
    self.erase_mode = self.enhance_mode = False
    self.refresh_edit_mode()
    self.drawCanvas()

  def button_dl_m_click(self, **event_args):
    anvil.media.download(self.generate_mask_img())

  def button_undo_click(self, **event_args):
    if len(self.ops_history) > 0:
      id = self.ops_history.pop()
      self.erase_points = [point for point in self.erase_points if point.op_id!=id]
      self.enhance_points = [point for point in self.enhance_points if point.op_id!=id]
      self.drawCanvas()

  def text_box_brush_size_change(self, **event_args):
    if self.text_box_brush_size.text is None:
      return
    new_num = int(self.text_box_brush_size.text)
    if new_num > 0:
      self.brush_size = int(self.text_box_brush_size.text)
    else:
      self.text_box_brush_size.text = str(self.brush_size)

  def button_brush_size_click(self, **event_args):
    self.text_box_brush_size.visible = not self.text_box_brush_size.visible

  def timer_1_tick(self, **event_args):
    # ОТКЛЮЧЕНО: автоматическая загрузка старых creations
    # Это вызывало дубликаты - загружались старые изображения из БД
    pass
    # with anvil.server.no_loading_indicator:
    #   if self.task is not None:
    #     if self.task.is_completed():
    #       my_creations = self.task.get_return_value()
    #       self.refresh_creations(my_creations)
    #       self.task = None
    #       self.timer_1.interval = 0

  def timer_0_tick(self, **event_args):
    # ОТКЛЮЧЕНО: автоматическая загрузка старых creations
    # Это вызывало дубликаты - загружались старые изображения из БД
    pass
    # self.task = None
    # with anvil.server.no_loading_indicator:
    #   self.timer_0.interval = 0
    #   self.task = anvil.server.call_s('launch_bg_get_creations')
    #   self.timer_1.interval = 0.5












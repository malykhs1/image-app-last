from ._anvil_designer import CreateNewTemplate
from anvil import *
import anvil.server

import anvil.js
from anvil.js import window

MAX_MB_IMG = 15
WH_IMG = 625
CARD_WIDTH = '360px'


class Point():
  def __init__(self, x, y, rad, op_id):
    self.x = x
    self.y = y
    self.rad = rad
    self.op_id = op_id


class CreateNew(CreateNewTemplate):
  def __init__(self, **properties):
    # Сначала инициализируем компоненты
    self.init_components(**properties)

    # Состояние
    self.locale = "en"
    self.img = None
    self.canvas_1 = None
    self.zoom = 1
    self.dz = 0
    self.dx = 0
    self.dy = 0
    self.sx = 0
    self.sy = 0
    self.minWH = 300
    self.cvsW = 300

    print("✅ Create initialized (awaiting canvas)")

  # ====== JS → Python мост через anvil.call(...) ======

  @anvil.js.callable
  def set_canvas_ref(self, js_canvas):
    """Получаем canvas из HTML и сохраняем ссылку"""
    try:
      # Если пришёл "сырой" DOM-элемент — оборачиваем
      if not hasattr(js_canvas, "getContext"):
        js_canvas = anvil.js.wrap_dom_element(js_canvas)
      self.canvas_1 = js_canvas
      print("🎨 Canvas connected successfully.")
      self.drawCanvas()
    except Exception as e:
      print("❌ Canvas init error:", e)

  @anvil.js.callable
  def file_loader_1_change(self, file, **event_args):
    """Получаем загруженный файл из HTML input"""
    try:
      print("📁 File received:", file)
      self.file_loaded(file)
    except Exception as e:
      print("❌ file_loader_1_change error:", e)

  @anvil.js.callable
  def button_create_click(self, **event_args):
    """Нажатие Download / Create — вызывается из HTML"""
    print("🚀 Starting artwork creation...")
    if not self.img:
      alert("Please upload an image first!")
      return
    try:
      # Здесь твоя прежняя логика — параметры генерации
      speedText = "very fast"
      effectIntensity = 2
      effectType = "clahe"
      noMask = True
      mask_img = None
      cloth = False
      discDiam = 400

      # subRect — как раньше (если надо — доработаем позже)
      zoom = self.zoom + self.dz
      left = round(self.sx + self.dx)
      top = round(self.sy + self.dy)
      right = left + int(self.minWH * zoom)
      bot = top + int(self.minWH * zoom)
      subRect = (left, top, right, bot)

      cropped_img = self.get_cropped_img()

      paramsDict = {
        "speedText": speedText,
        "effectType": effectType,
        "effectIntensity": effectIntensity,
        "cloth": cloth,
        "noMask": noMask,
        "subRect": subRect,
        "discDiam": discDiam
      }

      print("📡 Calling backend...")
      row = anvil.server.call('create', cropped_img, paramsDict, mask_img, getattr(self.img, "name", "uploaded.jpg"))
      print("✅ Product created successfully in Shopify!")
      alert("Product created successfully!")

      # Если хочешь — здесь можно показать превью / добавить в список
      # comp = Creation(locale=self.locale, item=row)

    except Exception as e:
      print("❌ Error:", e)
      alert("Server is currently unreachable. Please try again soon.")

  # ====== Клиентская логика работы с картинкой ======

  def file_loaded(self, file):
    if not file:
      return
    # File может прийти как JS File (имеет .size), либо Anvil Media (имеет .length)
    size = getattr(file, "size", None) or getattr(file, "length", None)
    if size and size > MAX_MB_IMG * 1024 * 1024:
      alert(f"Maximal size is {MAX_MB_IMG} MB", title="File too large")
      return

    self.img = file
    print("🖼️ Image loaded successfully")

    if self.canvas_1:
      self.drawCanvas()
    else:
      print("⚠️ Canvas not ready yet — skipping draw.")

  def drawCanvas(self):
    """Простая отрисовка-заглушка: круг + подпись.
       Реальный crop/zoom/drag добавим отдельным шагом."""
    if not self.canvas_1:
      print("⚠️ Canvas not connected yet.")
      return

    try:
      ctx = self.canvas_1.getContext("2d")
      ctx.clearRect(0, 0, self.canvas_1.width, self.canvas_1.height)

      if not self.img:
        # Placeholder до загрузки
        ctx.fillStyle = "#f3f3f3"
        ctx.fillRect(0, 0, self.canvas_1.width, self.canvas_1.height)
        ctx.fillStyle = "#777"
        ctx.font = "16px Inter"
        ctx.textAlign = "center"
        ctx.fillText("Upload your image", self.canvas_1.width / 2, self.canvas_1.height / 2)
        return

      # Пока просто рисуем «рамку»
      ctx.fillStyle = "#FFD48A"
      ctx.beginPath()
      ctx.arc(self.canvas_1.width / 2, self.canvas_1.height / 2, 120, 0, 6.283)
      ctx.fill()
      ctx.fillStyle = "#000"
      ctx.font = "16px Inter"
      ctx.textAlign = "center"
      ctx.fillText("Your uploaded image", self.canvas_1.width / 2, self.canvas_1.height / 2 + 150)
      print("🖌️ Canvas drawn successfully.")
    except Exception as e:
      print("❌ drawCanvas error:", e)

  def get_cropped_img(self):
    """Если используешь Anvil-Canvas API на клиенте — можно кропнуть здесь.
       Сейчас возвращаем исходный файл, чтобы не блокировать сценарий.
       (Позже добавим реальный crop из HTML5 canvas → BlobMedia → Python)"""
    return self.img
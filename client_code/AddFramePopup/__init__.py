from ._anvil_designer import AddFramePopupTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class AddFramePopup(AddFramePopupTemplate):
  def __init__(self, locale, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.locale = locale
    if self.is_IL():
      self.heading_1.text = 'השלימו את העיצוב למראה מושלם עם מסגרת עץ מעוצבת'
      self.heading_1.font_family = 'Rubik'
      self.button_yes.text = 'מאוחר יותר'
      self.button_yes.font_family = 'Rubik'
      self.button_no.text = 'כן בבקשה'
      self.button_no.font_family = 'Rubik'

  def is_IL(self):
    return self.locale == 'he'

  def button_yes_click(self, **event_args):
    if self.is_IL():
      self.raise_event("x-close-alert", value=False)
    else:
      self.raise_event("x-close-alert", value=True)

  def button_no_click(self, **event_args):
    if self.is_IL():
      self.raise_event("x-close-alert", value=True)
    else:
      self.raise_event("x-close-alert", value=False)

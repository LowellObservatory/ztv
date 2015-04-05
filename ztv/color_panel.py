import wx
from wx.lib.pubsub import Publisher
from matplotlib import cm
import numpy as np


class ColorPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.ztv_frame = self.GetTopLevelParent()
        # TODO: figure out why min size is not being respected by comparing with the framebuilder example
        self.SetSizeHintsSz( wx.Size( 1024,512 ), wx.DefaultSize )
        self.eventID_to_cmap = {wx.NewId(): x for x in self.ztv_frame.available_cmaps}
        self.cmap_to_eventID = {self.eventID_to_cmap[x]: x for x in self.eventID_to_cmap}

        v_sizer1 = wx.BoxSizer(wx.VERTICAL)
        values_sizer = wx.FlexGridSizer( 3, 5, 0, 0 )
        values_sizer.SetFlexibleDirection( wx.BOTH )
        values_sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.minval_static_text = wx.StaticText( self, wx.ID_ANY, u"Min", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.minval_static_text.Wrap( -1 )
        values_sizer.Add(self.minval_static_text, 0, wx.ALL, 0)

        textentry_font = wx.Font(14, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.FONTWEIGHT_LIGHT, False)

        self.minval_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                           wx.TE_PROCESS_ENTER)
        self.minval_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.minval_textctrl, 0, wx.ALL, 2)
        self.minval_textctrl.Bind(wx.EVT_TEXT, self.minval_textctrl_changed)
        self.minval_textctrl.Bind(wx.EVT_TEXT_ENTER, self.minval_textctrl_entered)

        self.set_min_button = wx.Button(self, wx.ID_ANY, u"Min", wx.DefaultPosition, wx.DefaultSize, 0)
        values_sizer.Add(self.set_min_button, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        self.set_min_button.Bind(wx.EVT_BUTTON, self.on_set_min_button)
        # TODO: italicize "min" text on button if limits are at Auto
        values_sizer.AddSpacer((0,0), 0, wx.EXPAND)
        temp_list = self.ztv_frame.available_value_modes_on_new_image[:]
        temp_list[temp_list.index('data-min/max')] = 'min'
        self.choose_min_value_mode_on_new_image = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                                            temp_list, 0)
        self.choose_min_value_mode_on_new_image.SetSelection(0)
        values_sizer.Add(self.choose_min_value_mode_on_new_image, 0,
                         wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        self.Bind(wx.EVT_CHOICE, self.on_choose_min_value_mode_on_new_image, self.choose_min_value_mode_on_new_image)

        values_sizer.AddSpacer((0,0), 0, wx.EXPAND)

        self.auto_set_minmax_button = wx.Button(self, wx.ID_ANY, u"Auto", wx.DefaultPosition, wx.DefaultSize, 0)
        values_sizer.Add(self.auto_set_minmax_button, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        self.auto_set_minmax_button.Bind(wx.EVT_BUTTON, self.on_auto_set_minmax_button)
        # TODO: italicize "auto" text on button if limits are at Auto

        self.set_minmax_button = wx.Button(self, wx.ID_ANY, u"Min/Max", wx.DefaultPosition, wx.DefaultSize, 0)
        values_sizer.Add(self.set_minmax_button, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        self.set_minmax_button.Bind(wx.EVT_BUTTON, self.on_set_minmax_button)
        # TODO: italicize "min/max" text on button if limits are at Auto

        self.minval_static_text = wx.StaticText(self, wx.ID_ANY, u"On load image:",
                                                wx.DefaultPosition, wx.DefaultSize, 0 )
        self.minval_static_text.Wrap( -1 )
        values_sizer.Add(self.minval_static_text, 0, wx.ALL, 2)
        temp_list = self.ztv_frame.available_value_modes_on_new_image[:]
        temp_list[temp_list.index('data-min/max')] = 'min/max'
        temp_list.insert(0, '-'),
        self.choose_minmax_value_mode_on_new_image = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                                               temp_list, 0)
        self.choose_minmax_value_mode_on_new_image.SetSelection(1)
        values_sizer.Add(self.choose_minmax_value_mode_on_new_image, 0,
                         wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        self.Bind(wx.EVT_CHOICE, self.on_choose_minmax_value_mode_on_new_image,
                  self.choose_minmax_value_mode_on_new_image)

        maxval_static_text = wx.StaticText( self, wx.ID_ANY, u"Max", wx.DefaultPosition, wx.DefaultSize, 0 )
        maxval_static_text.Wrap( -1 )
        values_sizer.Add(maxval_static_text, 0, wx.ALL, 2)

        self.maxval_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                           wx.TE_PROCESS_ENTER)
        self.maxval_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.maxval_textctrl, 0, wx.ALL, 2)
        self.maxval_textctrl.Bind(wx.EVT_TEXT, self.maxval_textctrl_changed)
        self.maxval_textctrl.Bind(wx.EVT_TEXT_ENTER, self.maxval_textctrl_entered)

        self.set_max_button = wx.Button(self, wx.ID_ANY, u"Max", wx.DefaultPosition, wx.DefaultSize, 0)
        values_sizer.Add(self.set_max_button, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        self.set_max_button.Bind(wx.EVT_BUTTON, self.on_set_max_button)
        # TODO: italicize "max" text on button if limits are at Auto
        values_sizer.AddSpacer((0,0), 0, wx.EXPAND)
        temp_list = self.ztv_frame.available_value_modes_on_new_image[:]
        temp_list[temp_list.index('data-min/max')] = 'max'
        self.choose_max_value_mode_on_new_image = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                                            temp_list, 0)
        self.choose_max_value_mode_on_new_image.SetSelection(0)
        values_sizer.Add(self.choose_max_value_mode_on_new_image, 0,
                         wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        self.Bind(wx.EVT_CHOICE, self.on_choose_max_value_mode_on_new_image, self.choose_max_value_mode_on_new_image)

        v_sizer1.Add(values_sizer, 0)
        v_sizer1.AddSpacer((0, 6), 0, 0)
        v_sizer1.Add(wx.StaticLine(self), flag=wx.EXPAND)
        v_sizer1.AddSpacer((0, 6), 0, 0)
        cmap_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.init_cmap_popup_menu()
        self.cmap_button = wx.Button(self, wx.ID_ANY, 'X'*max([len(a) for a in self.ztv_frame.available_cmaps]),
                                     wx.DefaultPosition, wx.DefaultSize, 0)
        self.cmap_button.SetBitmap(self.cmap_button_bitmaps[self.ztv_frame.cmap])
        cmap_sizer.Add(self.cmap_button, 0, wx.ALL|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 2)
        self.cmap_button.Bind(wx.EVT_LEFT_DOWN, self.on_cmap_button)
        cmap_options_sizer = wx.BoxSizer(wx.VERTICAL)
        self.is_cmap_inverted_checkbox = wx.CheckBox(self, -1, 'inverted', wx.DefaultPosition, wx.DefaultSize, 0)
        cmap_options_sizer.Add(self.is_cmap_inverted_checkbox, 0)
        self.Bind(wx.EVT_CHECKBOX, self.on_is_cmap_inverted_checkbox, self.is_cmap_inverted_checkbox)
        self.choose_scaling = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                        self.ztv_frame.available_scalings, 0)
        self.choose_scaling.SetSelection(0)
        scaling_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scaling_sizer.Add(wx.StaticText( self, wx.ID_ANY, u"Scaling", wx.DefaultPosition, wx.DefaultSize, 0 ), 0)
        scaling_sizer.Add(self.choose_scaling, 0)
        cmap_options_sizer.Add(scaling_sizer, 0)
        self.Bind(wx.EVT_CHOICE, self.on_choose_scaling, self.choose_scaling)
        cmap_sizer.Add(cmap_options_sizer, 0)
        v_sizer1.Add(cmap_sizer, 0)
        v_sizer1.AddSpacer((0, 0), 0, wx.EXPAND)
        self.SetSizer(v_sizer1)
        self.last_minval_string = ''
        self.last_maxval_string = ''
        Publisher().subscribe(self.on_clim_changed, "clim-changed")
        Publisher().subscribe(self.on_cmap_changed, "cmap-changed")
        Publisher().subscribe(self.on_is_cmap_inverted_changed, "is_cmap_inverted-changed")
        Publisher().subscribe(self.on_scaling_changed, "scaling-changed")
        self.Bind(wx.EVT_NAVIGATION_KEY, self.on_navigation_key)

    def on_choose_scaling(self, evt):
        wx.CallAfter(Publisher().sendMessage, "set_scaling", evt.GetString())

    def init_cmap_popup_menu(self):
        cmap_button_bitmap_height = 30
        cmap_button_bitmap_width = 200
        cmap_menu_bitmap_height = 20
        cmap_menu_bitmap_width = 200
        self.cmap_button_bitmaps = {}
        self.cmap_menu_bitmaps = {}
        for cmap in self.ztv_frame.available_cmaps:
            temp = cm.ScalarMappable(cmap=cmap)
            rgba = temp.to_rgba(np.outer(np.ones(cmap_button_bitmap_height, dtype=np.uint8),
                                         np.arange(cmap_button_bitmap_width, dtype=np.uint8)))
            self.cmap_button_bitmaps[cmap] = wx.BitmapFromBufferRGBA(cmap_button_bitmap_width, cmap_button_bitmap_height,
                                                                     np.uint8(np.round(rgba*255)))
            rgba = temp.to_rgba(np.outer(np.ones(cmap_menu_bitmap_height, dtype=np.uint8),
                                         np.arange(cmap_menu_bitmap_width, dtype=np.uint8)))
            self.cmap_menu_bitmaps[cmap] = wx.BitmapFromBufferRGBA(cmap_menu_bitmap_width, cmap_menu_bitmap_height,
                                                                   np.uint8(np.round(rgba*255)))
        menu = wx.Menu()
        for cmap in self.ztv_frame.available_cmaps:
            menu_item = menu.AppendCheckItem(self.cmap_to_eventID[cmap], cmap)
            wx.EVT_MENU(menu, self.cmap_to_eventID[cmap], self.on_change_cmap_event)
            menu_item.SetBitmap(self.cmap_menu_bitmaps[cmap])
        self.cmap_popup_menu = menu

    def on_change_cmap_event(self, event):
        wx.CallAfter(Publisher().sendMessage, "set_cmap", self.eventID_to_cmap[event.GetId()])

    def on_navigation_key(self, evt):
        # TODO: figure out how to make tab order work the way I want.  Currently the following code works partly, but is ignored by some tabs.  Weird. Looks like it's an issue that tab is triggering some *other* event when it's a button that has focus.  Might have to play around with catching all key-presses inside of ColorPanel & passing along the non-tab keypresses???
        tab_order = [self.minval_textctrl, self.maxval_textctrl,
                     self.auto_set_minmax_button,
                     self.set_min_button, self.set_minmax_button, self.set_max_button,
                     self.choose_min_value_mode_on_new_image,
                     self.choose_minmax_value_mode_on_new_image,
                     self.choose_max_value_mode_on_new_image]
        if evt.GetCurrentFocus() not in tab_order:
            new_focus = tab_order[0]
        else:
            if evt.GetDirection():
                direction = 1
            else:
                direction = -1
            new_focus = tab_order[(tab_order.index(evt.GetCurrentFocus()) + direction) % len(tab_order)]
        # following debugging line demonstrates that on_navigation_key is only being called when focus is on a textctrl, not when on a button or dropdown menu
#         sys.stderr.write("\n\nnew_focus = {}\n\n".format(new_focus))
        new_focus.SetFocus()

    def on_is_cmap_inverted_checkbox(self, evt):
        wx.CallAfter(Publisher().sendMessage, "set_cmap_inverted", evt.IsChecked())

    def on_is_cmap_inverted_changed(self, *args):
        self.is_cmap_inverted_checkbox.SetValue(self.ztv_frame.is_cmap_inverted)

    def on_scaling_changed(self, *args):
        self.choose_scaling.SetSelection(self.ztv_frame.available_scalings.index(self.ztv_frame.scaling))

    def on_cmap_button(self, evt):
        for cmap in self.ztv_frame.available_cmaps:
            self.cmap_popup_menu.Check(self.cmap_to_eventID[cmap], False)
        self.cmap_popup_menu.Check(self.cmap_to_eventID[self.ztv_frame.cmap], True)
        pos = self.ScreenToClient(wx.GetMousePosition())
        self.PopupMenu(self.cmap_popup_menu, pos)

    def on_choose_min_value_mode_on_new_image(self, evt):
        new_val = [a for a in self.ztv_frame.available_value_modes_on_new_image if
                   evt.GetString() in a][0]
        self.ztv_frame.min_value_mode_on_new_image = new_val
        if (self.choose_min_value_mode_on_new_image.GetSelection() ==
            self.choose_max_value_mode_on_new_image.GetSelection()):
            self.choose_minmax_value_mode_on_new_image.SetSelection( \
                        self.choose_min_value_mode_on_new_image.GetSelection() + 1)
        else:
            self.choose_minmax_value_mode_on_new_image.SetSelection(0)

    def on_choose_max_value_mode_on_new_image(self, evt):
        new_val = [a for a in self.ztv_frame.available_value_modes_on_new_image if
                   evt.GetString() in a][0]
        self.ztv_frame.max_value_mode_on_new_image = new_val
        if (self.choose_min_value_mode_on_new_image.GetSelection() ==
            self.choose_max_value_mode_on_new_image.GetSelection()):
            self.choose_minmax_value_mode_on_new_image.SetSelection( \
                        self.choose_min_value_mode_on_new_image.GetSelection() + 1)
        else:
            self.choose_minmax_value_mode_on_new_image.SetSelection(0)

    def on_choose_minmax_value_mode_on_new_image(self, evt):
        if evt.GetString != '':
            new_val = [a for a in self.ztv_frame.available_value_modes_on_new_image if
                       evt.GetString() in a][0]
            self.ztv_frame.min_value_mode_on_new_image = new_val
            self.ztv_frame.max_value_mode_on_new_image = new_val
            new_index = self.ztv_frame.available_value_modes_on_new_image.index(new_val)
            self.choose_min_value_mode_on_new_image.SetSelection(new_index)
            self.choose_max_value_mode_on_new_image.SetSelection(new_index)

    def on_auto_set_minmax_button(self, evt):
        self.ztv_frame.set_clim_to_auto()

    def on_set_minmax_button(self, evt):
        self.ztv_frame.set_clim_to_minmax()

    def on_set_min_button(self, evt):
        self.ztv_frame.set_clim([self.ztv_frame.display_image.min(), None])
        if self.FindFocus() == self.minval_textctrl:
            self.minval_textctrl.SetSelection(-1, -1)

    def on_set_max_button(self, evt):
        self.ztv_frame.set_clim([None, self.ztv_frame.display_image.max()])
        if self.FindFocus() == self.maxval_textctrl:
            self.maxval_textctrl.SetSelection(-1, -1)

    def force_textctrl_color_update(self, textctrl):
        cur_focused_item = self.FindFocus()
        insertion_point = textctrl.GetInsertionPoint()
        self.set_max_button.SetFocus()  # need to shift focus away & then back to force color update in GUI
        textctrl.SetFocus()
        textctrl.SetInsertionPoint(insertion_point)
        if cur_focused_item is not None:
            cur_focused_item.SetFocus()

    def set_textctrl_background_color(self, textctrl_name, mode, tooltip=None):
        if mode == 'ok':
            color = (255,255,255)
        elif mode == 'enter-needed':
            color = (200,255,200)
        elif mode == 'invalid':
            # TODO:  implement: escape key brings up last valid value??
            color = (255,200,200)
        if textctrl_name == 'minval':
            cur_textctrl = self.minval_textctrl
        elif textctrl_name == 'maxval':
            cur_textctrl = self.maxval_textctrl
        cur_textctrl.SetBackgroundColour(color)
        cur_textctrl.Refresh()
        if tooltip is not None and not isinstance(tooltip, wx.ToolTip):
            tooltip = wx.ToolTip(tooltip)
        cur_textctrl.SetToolTip(tooltip)
        self.force_textctrl_color_update(cur_textctrl)

    def on_clim_changed(self, *args):
        new_minval_str = "{: .9g}".format(self.ztv_frame.clim[0])
        new_maxval_str = "{: .9g}".format(self.ztv_frame.clim[1])
        if new_minval_str != self.last_minval_string:
            self.minval_textctrl.SetValue(new_minval_str)
            self.set_textctrl_background_color('minval', 'ok')
            self.last_minval_string = new_minval_str
        if new_maxval_str != self.last_maxval_string:
            self.maxval_textctrl.SetValue(new_maxval_str)
            self.set_textctrl_background_color('maxval', 'ok')
            self.last_maxval_string = new_maxval_str

    def on_cmap_changed(self, *args):
        self.cmap_button.SetBitmap(self.cmap_button_bitmaps[self.ztv_frame.cmap])
        self.cmap_button.SetLabel(self.ztv_frame.cmap)

    def validate_minval_str(self):
        try:
            newval = float(self.minval_textctrl.GetValue())
            if self.minval_textctrl.GetValue() == self.last_minval_string:
                self.set_textctrl_background_color('minval', 'ok')
            else:
                self.set_textctrl_background_color('minval', 'enter-needed',
                                                   'Press enter in this field to set new minimum value')
            return True
        except ValueError:
            self.set_textctrl_background_color('minval', 'invalid', 'Entry cannot be converted to float')
            return False

    def minval_textctrl_changed(self, evt):
        self.validate_minval_str()

    def minval_textctrl_entered(self, evt):
        if self.validate_minval_str():
            self.last_minval_string = self.minval_textctrl.GetValue()
            self.ztv_frame.set_clim([float(self.minval_textctrl.GetValue()), None])
            self.minval_textctrl.SetSelection(-1, -1)

    def validate_maxval_str(self):
        try:
            newval = float(self.maxval_textctrl.GetValue())
            if self.maxval_textctrl.GetValue() == self.last_maxval_string:
                self.set_textctrl_background_color('maxval', 'ok')
            else:
                self.set_textctrl_background_color('maxval', 'enter-needed',
                                                   'Press enter in this field to set new maximum value')
            return True
        except ValueError:
            self.set_textctrl_background_color('maxval', 'invalid', 'Entry cannot be converted to float')
            return False

    def maxval_textctrl_changed(self, evt):
        self.validate_maxval_str()

    def maxval_textctrl_entered(self, evt):
        if self.validate_maxval_str():
            self.ztv_frame.set_clim([None, float(self.maxval_textctrl.GetValue())])
            self.maxval_textctrl.SetSelection(-1, -1)


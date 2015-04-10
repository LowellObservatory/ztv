import wx
from wx.lib.pubsub import Publisher
from wx.lib.pubsub.core.datamsg import Message
import matplotlib
matplotlib.interactive(True)
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.patches import Circle, Wedge
from scipy.optimize import curve_fit
from .quick_phot import centroid, aperture_phot
from .ztv_lib import validate_textctrl_str
import numpy as np

import sys

class PhotPlotPanel(wx.Panel):
    def __init__(self, parent, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, **kwargs)
        self.ztv_frame = self.GetTopLevelParent()
        self.figure = Figure(dpi=None, figsize=(1.,1.))
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        self.Bind(wx.EVT_SIZE, self._onSize)

    def _onSize(self, event):
        self._SetSize()

    def _SetSize(self):
        pixels = tuple(self.GetClientSize())
        self.SetSize(pixels)
        self.canvas.SetSize(pixels)
        self.figure.set_size_inches(float(pixels[0])/self.figure.get_dpi(), float(pixels[1])/self.figure.get_dpi())


def fixed_gauss(x, fwhm, peakval):
    """
    Fit FWHM & peakval for a gaussian fixed at 0 and that baseline is 0.
    """
    c = fwhm / (2. * np.sqrt(2. * np.log(2.)))
    xc = 0.
    return peakval * np.exp(-((x - xc)**2) / (2.*c**2))


class PhotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.ztv_frame = self.GetTopLevelParent()
        # TODO: figure out why min size is not being respected by comparing with the framebuilder example
        self.SetSizeHintsSz( wx.Size( 1024,512 ), wx.DefaultSize )
        self.star_center_patch = None
        self.star_aperture_patch = None
        self.sky_aperture_patch = None

        self.last_string_values = {'aprad':'', 'skyradin':'', 'skyradout':''}
        self.xclicked = 0.
        self.yclicked = 0.
        self.xcentroid = 0.
        self.ycentroid = 0.
        self.aprad = 10.
        self.skyradin = 20.
        self.skyradout = 30.
        
        textentry_font = wx.Font(14, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.FONTWEIGHT_LIGHT, False)
        values_sizer = wx.FlexGridSizer( 3, 5, 0, 0 )
        values_sizer.SetFlexibleDirection( wx.BOTH )
        values_sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.aprad_static_text = wx.StaticText( self, wx.ID_ANY, u"Aperture radius", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.aprad_static_text.Wrap( -1 )
        values_sizer.Add(self.aprad_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.aprad_textctrl = wx.TextCtrl(self, wx.ID_ANY, str(self.aprad), wx.DefaultPosition, wx.DefaultSize,
                                       wx.TE_PROCESS_ENTER)
        self.aprad_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.aprad_textctrl, 0, wx.ALL, 2)
        self.aprad_textctrl.Bind(wx.EVT_TEXT, self.aprad_textctrl_changed)
        self.aprad_textctrl.Bind(wx.EVT_TEXT_ENTER, self.aprad_textctrl_entered)
        values_sizer.AddSpacer((30,0), 0, wx.EXPAND)
        self.x_static_text = wx.StaticText( self, wx.ID_ANY, u"x", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL )
        self.x_static_text.Wrap( -1 )
        values_sizer.Add(self.x_static_text, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM, 0)
        self.y_static_text = wx.StaticText( self, wx.ID_ANY, u"y", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL )
        self.y_static_text.Wrap( -1 )
        values_sizer.Add(self.y_static_text, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM, 0)

        self.skyradin_static_text = wx.StaticText(self, wx.ID_ANY, u"Sky inner radius", 
                                                  wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.skyradin_static_text.Wrap( -1 )
        values_sizer.Add(self.skyradin_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.skyradin_textctrl = wx.TextCtrl(self, wx.ID_ANY, str(self.skyradin), wx.DefaultPosition, wx.DefaultSize,
                                       wx.TE_PROCESS_ENTER)
        self.skyradin_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.skyradin_textctrl, 0, wx.ALL, 2)
        self.skyradin_textctrl.Bind(wx.EVT_TEXT, self.skyradin_textctrl_changed)
        self.skyradin_textctrl.Bind(wx.EVT_TEXT_ENTER, self.skyradin_textctrl_entered)
        self.clicked_static_text = wx.StaticText(self, wx.ID_ANY, u"Clicked", wx.DefaultPosition, 
                                                 wx.DefaultSize, wx.ALIGN_RIGHT )
        self.clicked_static_text.Wrap( -1 )
        values_sizer.Add(self.clicked_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.xclicked_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.TE_PROCESS_ENTER)
        self.xclicked_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.xclicked_textctrl, 0, wx.ALL, 2)
        self.yclicked_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.TE_PROCESS_ENTER)
        self.yclicked_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.yclicked_textctrl, 0, wx.ALL, 2)

        self.skyradout_static_text = wx.StaticText(self, wx.ID_ANY, u"Sky outer radius", wx.DefaultPosition, 
                                                   wx.DefaultSize, wx.ALIGN_RIGHT )
        self.skyradout_static_text.Wrap( -1 )
        values_sizer.Add(self.skyradout_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.skyradout_textctrl = wx.TextCtrl(self, wx.ID_ANY, str(self.skyradout), wx.DefaultPosition, wx.DefaultSize,
                                              wx.TE_PROCESS_ENTER)
        self.skyradout_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.skyradout_textctrl, 0, wx.ALL, 2)
        self.skyradout_textctrl.Bind(wx.EVT_TEXT, self.skyradout_textctrl_changed)
        self.skyradout_textctrl.Bind(wx.EVT_TEXT_ENTER, self.skyradout_textctrl_entered)
        self.centroid_static_text = wx.StaticText(self, wx.ID_ANY, u"Centroid", wx.DefaultPosition, 
                                                  wx.DefaultSize, wx.ALIGN_RIGHT )
        self.centroid_static_text.Wrap( -1 )
        values_sizer.Add(self.centroid_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.xcentroid_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                              wx.TE_PROCESS_ENTER)
        self.xcentroid_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.xcentroid_textctrl, 0, wx.ALL, 2)
        self.ycentroid_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                       wx.TE_PROCESS_ENTER)
        self.ycentroid_textctrl.SetFont(textentry_font)
        values_sizer.Add(self.ycentroid_textctrl, 0, wx.ALL, 2)


        v_sizer1 = wx.BoxSizer(wx.VERTICAL)
        v_sizer1.Add(values_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
#         v_sizer1.AddSpacer((0, 1), 0, wx.EXPAND)
        v_sizer1.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5)
#         v_sizer1.AddSpacer((0, 1), 0, wx.EXPAND)

        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sky_static_text = wx.StaticText( self, wx.ID_ANY, u"Sky", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.sky_static_text.Wrap( -1 )
        h_sizer1.Add(self.sky_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.sky_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                        wx.TE_PROCESS_ENTER)
        self.sky_textctrl.SetFont(textentry_font)
        h_sizer1.Add(self.sky_textctrl, 0, wx.ALL, 2)
        # TODO: look up how to do nice plus/minus symbol
        self.pm_static_text = wx.StaticText( self, wx.ID_ANY, u"+-", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.pm_static_text.Wrap( -1 )
        h_sizer1.Add(self.pm_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.skyerr_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                        wx.TE_PROCESS_ENTER)
        self.skyerr_textctrl.SetFont(textentry_font)
        h_sizer1.Add(self.skyerr_textctrl, 0, wx.ALL, 2)
        self.perpixel_static_text = wx.StaticText( self, wx.ID_ANY, u"/pixel", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.perpixel_static_text.Wrap( -1 )
        h_sizer1.Add(self.perpixel_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        v_sizer1.Add(h_sizer1, 0, wx.ALIGN_LEFT)
        
        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.object_static_text = wx.StaticText( self, wx.ID_ANY, u"Object", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.object_static_text.Wrap( -1 )
        h_sizer2.Add(self.object_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.flux_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                        wx.TE_PROCESS_ENTER)
        self.flux_textctrl.SetFont(textentry_font)
        h_sizer2.Add(self.flux_textctrl, 0, wx.ALL, 2)
        self.cts_static_text = wx.StaticText( self, wx.ID_ANY, u"cts with FWHM", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.cts_static_text.Wrap( -1 )
        h_sizer2.Add(self.cts_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        self.fwhm_textctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                        wx.TE_PROCESS_ENTER)
        self.fwhm_textctrl.SetFont(textentry_font)
        h_sizer2.Add(self.fwhm_textctrl, 0, wx.ALL, 2)
        self.pix_static_text = wx.StaticText( self, wx.ID_ANY, u"pix", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        self.pix_static_text.Wrap( -1 )
        h_sizer2.Add(self.pix_static_text, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        h_sizer2.AddSpacer([30, 0], 0, 1)
        self.clear_button = wx.Button(self, wx.ID_ANY, u"Clear", wx.DefaultPosition, wx.DefaultSize, 0)
        h_sizer2.Add(self.clear_button, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 2)
        self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear_button)

        v_sizer1.Add(h_sizer2, 0, wx.ALIGN_LEFT)

        self.plot_panel = PhotPlotPanel(self)
        v_sizer1.Add(self.plot_panel, 1, wx.LEFT | wx.TOP | wx.EXPAND)

        self.SetSizer(v_sizer1)
        Publisher().subscribe(self.update_phot_xy, "new_phot_xy")
        Publisher().subscribe(self.recalc_phot, "redraw_image")

    def on_clear_button(self, evt):
        if self.star_center_patch is not None:
            self.ztv_frame.primary_image_panel.axes.patches.remove(self.star_center_patch)
            self.star_center_patch = None
        if self.star_aperture_patch is not None:
            self.ztv_frame.primary_image_panel.axes.patches.remove(self.star_aperture_patch)
            self.star_aperture_patch = None
        if self.sky_aperture_patch is not None:
            self.ztv_frame.primary_image_panel.axes.patches.remove(self.sky_aperture_patch)
            self.sky_aperture_patch = None
        self.ztv_frame.primary_image_panel.figure.canvas.draw()

    def update_phot_xy(self, msg):
        if isinstance(msg, Message):
            x,y = msg.data
        else:
            x,y = msg
        self.xclicked, self.yclicked = x,y
        self.recalc_phot()
        
    def recalc_phot(self, msg=None):
        self.xclicked_textctrl.SetValue("{:8.2f}".format(self.xclicked))
        self.yclicked_textctrl.SetValue("{:8.2f}".format(self.yclicked))
        self.xcentroid,self.ycentroid = centroid(self.ztv_frame.display_image, self.xclicked, self.yclicked)
        self.xcentroid_textctrl.SetValue("{:8.2f}".format(self.xcentroid))
        self.ycentroid_textctrl.SetValue("{:8.2f}".format(self.ycentroid))
        phot = aperture_phot(self.ztv_frame.display_image, self.xcentroid, self.ycentroid, 
                             self.aprad, self.skyradin, self.skyradout, return_distances=True)
        aprad = phot['star_radius']
        skyradin = phot['sky_inner_radius']
        skyradout = phot['sky_outer_radius']
        self.flux_textctrl.SetValue("{:0.6g}".format(phot['flux']))
        self.sky_textctrl.SetValue("{:0.6g}".format(phot['sky_per_pixel']))
        self.skyerr_textctrl.SetValue("{:0.6g}".format(phot['sky_per_pixel_err']))
        aprad_color = 'blue'
        skyrad_color = 'red'
        self.plot_panel.axes.cla()
        if self.star_center_patch is not None:
            self.ztv_frame.primary_image_panel.axes.patches.remove(self.star_center_patch)
        if self.star_aperture_patch is not None:
            self.ztv_frame.primary_image_panel.axes.patches.remove(self.star_aperture_patch)
        if self.sky_aperture_patch is not None:
            self.ztv_frame.primary_image_panel.axes.patches.remove(self.sky_aperture_patch)
        if len(phot['distances']) > 5:
            unrounded_xmax = skyradout + 0.2 * (skyradout - skyradin)
            nice_factor = 10./5.
            sensible_xmax = ((nice_factor*10**np.floor(np.log10(unrounded_xmax))) * 
                             np.ceil(unrounded_xmax / (nice_factor*10**np.floor(np.log10(unrounded_xmax)))))
            mask = phot['distances'] <= sensible_xmax
            self.plot_panel.axes.plot(phot['distances'][mask].ravel(), self.ztv_frame.display_image[mask].ravel(), 
                                      'ko', markersize=1)
            ylim = self.plot_panel.axes.get_ylim()
            n_sigma = 6.
            if (phot['sky_per_pixel'] - n_sigma*phot['sky_per_pixel_err']*np.sqrt(phot['n_sky_pix'])) > 0.:
                ylim = (phot['sky_per_pixel'] - n_sigma*phot['sky_per_pixel_err']*np.sqrt(phot['n_sky_pix']), ylim[1])
            self.plot_panel.axes.set_ylim(ylim)
            alpha = 0.25
            self.plot_panel.axes.fill_between([0., aprad], [ylim[0], ylim[0]], [ylim[1], ylim[1]], 
                                              facecolor=aprad_color, alpha=alpha)
            self.plot_panel.axes.fill_between([skyradin, skyradout], [ylim[0], ylim[0]], [ylim[1], ylim[1]], 
                                              facecolor=skyrad_color, alpha=alpha)
            self.plot_panel.axes.plot([0, sensible_xmax], [phot['sky_per_pixel'], phot['sky_per_pixel']], '-r')
            self.plot_panel.axes.plot([0, sensible_xmax], [phot['sky_per_pixel'] - phot['sky_per_pixel_err'], 
                                                           phot['sky_per_pixel'] - phot['sky_per_pixel_err']], ':r')
            self.plot_panel.axes.plot([0, sensible_xmax], [phot['sky_per_pixel'] + phot['sky_per_pixel_err'], 
                                                           phot['sky_per_pixel'] + phot['sky_per_pixel_err']], ':r')
            self.plot_panel.axes.set_xlim([0, sensible_xmax])
            mask = phot['distances'] <= aprad
            xs = phot['distances'][mask]
            vals = self.ztv_frame.display_image[mask] - phot['sky_per_pixel']
            p0 = [aprad*0.3, vals.max()]
            popt, pcov = curve_fit(fixed_gauss, xs, vals, p0=p0)
            xs = np.arange(0, aprad+0.1, 0.1)
            c = popt[0] / (2. * np.sqrt(2. * np.log(2.)))
            self.plot_panel.axes.plot(xs, phot['sky_per_pixel'] + 
                                          popt[1] * np.exp(-((xs)**2) / (2.*c**2)), '-', color=aprad_color)
            self.fwhm_textctrl.SetValue("{:0.3g}".format(np.abs(popt[0])))
        
            self.star_center_patch = Circle([self.xcentroid, self.ycentroid], 0.125, color=aprad_color)
            self.ztv_frame.primary_image_panel.axes.add_patch(self.star_center_patch)
            self.star_aperture_patch = Circle([self.xcentroid, self.ycentroid], aprad, color=aprad_color, alpha=alpha)
            self.ztv_frame.primary_image_panel.axes.add_patch(self.star_aperture_patch)
            self.sky_aperture_patch = Wedge([self.xcentroid, self.ycentroid], skyradout, 0., 360., 
                                            width=skyradout-skyradin, color=skyrad_color, alpha=alpha)
            self.ztv_frame.primary_image_panel.axes.add_patch(self.sky_aperture_patch)
        self.plot_panel.figure.canvas.draw()
        self.ztv_frame.primary_image_panel.figure.canvas.draw()

    def aprad_textctrl_changed(self, evt):
        validate_textctrl_str(self.aprad_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                              self.last_string_values['aprad'])

    def aprad_textctrl_entered(self, evt):
        if validate_textctrl_str(self.aprad_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                                 self.last_string_values['aprad']):
            self.last_string_values['aprad'] = self.aprad_textctrl.GetValue()
            self.aprad = float(self.last_string_values['aprad'])
            self.recalc_phot()
            validate_textctrl_str(self.aprad_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                                  self.last_string_values['aprad'])
            self.aprad_textctrl.SetSelection(-1, -1)

    def skyradin_textctrl_changed(self, evt):
        validate_textctrl_str(self.skyradin_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                              self.last_string_values['skyradin'])

    def skyradin_textctrl_entered(self, evt):
        if validate_textctrl_str(self.skyradin_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                                 self.last_string_values['skyradin']):
            self.last_string_values['skyradin'] = self.skyradin_textctrl.GetValue()
            self.skyradin = float(self.last_string_values['skyradin'])
            self.recalc_phot()
            validate_textctrl_str(self.skyradin_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                                  self.last_string_values['skyradin'])
            self.skyradin_textctrl.SetSelection(-1, -1)

    def skyradout_textctrl_changed(self, evt):
        validate_textctrl_str(self.skyradout_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                              self.last_string_values['skyradout'])

    def skyradout_textctrl_entered(self, evt):
        if validate_textctrl_str(self.skyradout_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                                 self.last_string_values['skyradout']):
            self.last_string_values['skyradout'] = self.skyradout_textctrl.GetValue()
            self.skyradout = float(self.last_string_values['skyradout'])
            self.recalc_phot()
            validate_textctrl_str(self.skyradout_textctrl, lambda x: float(x) if float(x) > 0 else float('x'), 
                                  self.last_string_values['skyradout'])
            self.skyradout_textctrl.SetSelection(-1, -1)
            
#TODO: set up reasonable defaults for aprad, skyradin, & skyradout
# TODO; clear button?  or just toggle switch for turning circles on/off?  maybe latter?


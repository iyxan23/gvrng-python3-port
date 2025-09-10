# -*- coding: utf-8 -*-

# Copyright (c) 2006 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           Widgets.py
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# additional non-glade widgets and misc stuff
import gi
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango, PangoCairo, GLib
import logging
import cairo
from .SimpleGladeApp import bindtextdomain
from .SimpleGladeApp import SimpleGladeApp
import utils
import sys
import os
# from ..worldMap import lookup_dir_dict
lookup_dir_dict = {'N': 'N', 'S': 'S', 'E': 'E', 'W': 'W'}
_WDEBUG = 0
gi.require_version('Gtk', '3.0')


app_name = "gvr_gtk"

# locale_dir = utils.LOCALEDIR
# bindtextdomain(app_name, locale_dir)
# utils.set_locale()

glade_dir = utils.FRONTENDDIR


class WarningDialog(Gtk.MessageDialog):
    def __init__(self, parent=None, flags=Gtk.DialogFlags.MODAL, type=Gtk.MessageType.WARNING,
                 buttons=Gtk.ButtonsType.CLOSE, message_format='', txt=''):
        Gtk.MessageDialog.__init__(self, parent=parent,
                                   flags=flags,
                                   type=type,
                                   buttons=buttons,
                                   message_format=message_format)
        self.connect("response", self.response)
        self.set_markup('%s%s%s' % ('<b>', txt, '</b>'))
        self.set_title('Warning')
        self.show()

    def response(self, *args):
        """destroys itself on a respons, we don't care about the response value"""
        self.destroy()


class ErrorDialog(WarningDialog):
    def __init__(self, txt):
        WarningDialog.__init__(self, parent=None,
                               flags=Gtk.DialogFlags.MODAL,
                               type=Gtk.MessageType.ERROR,
                               buttons=Gtk.ButtonsType.CLOSE,
                               message_format='',
                               txt=txt)
        self.set_title('Error')


class InfoDialog(WarningDialog):
    def __init__(self, txt):
        WarningDialog.__init__(self, parent=None,
                               flags=Gtk.DialogFlags.MODAL,
                               type=Gtk.MessageType.INFO,
                               buttons=Gtk.ButtonsType.CLOSE,
                               message_format='',
                               txt=txt)
        self.set_title('Information')


class YesNoDialog(Gtk.MessageDialog):
    def __init__(self, parent=None, flags=Gtk.DialogFlags.MODAL, type=Gtk.MessageType.INFO,
                 buttons=Gtk.ButtonsType.YES_NO, message_format='', txt=''):
        Gtk.MessageDialog.__init__(self, transient_for=parent,
                                   flags=flags,
                                   message_type=type,
                                   buttons=buttons,
                                   text=message_format)
        # self.connect("response", self.response)
        self.set_markup('%s%s%s' % ('<b>', txt, '</b>'))
        self.set_title('Question ?')
        self.show()


class BeeperDialog(YesNoDialog):
    def __init__(self, parent=None, flags=Gtk.DialogFlags.MODAL, type=Gtk.MessageType.QUESTION,
                 buttons=Gtk.ButtonsType.OK_CANCEL, message_format='', txt=''):
        YesNoDialog.__init__(self, parent=parent,
                             flags=flags,
                             type=type,
                             buttons=buttons,
                             message_format=message_format,
                             txt=txt)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        label = Gtk.Label(label="Number of beepers:")
        self.entrybox = Gtk.Entry()
        self.entrybox.set_can_focus(True)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.entrybox, False, False, 0)
        self.get_content_area().pack_start(hbox, True, True, 0)
        self.entrybox.grab_focus()
        self.get_content_area().show_all()

    def get_choice(self):
        choice = self.entrybox.get_text()
        try:
            beepers = int(choice)
        except ValueError as info:
            print(info)
            beepers = 0
        if beepers < 0:
            beepers = 0
        return beepers

# As a reminder:
# The toplevel window on the XO is always fullscreen with a size of 1200x900
# and the canvas widget has a size of 638x737 (x,y)


class Canvas(Gtk.DrawingArea):
    """Wraps a Gtk.DrawingArea and a adds a few abstraction methods.
    Based on the example from the pygtk FAQ."""

    def __init__(self, parent=None):
        self.logger = logging.getLogger("gvr.Widgets.Canvas")
        self.logger.debug("start canvas creation")
        Gtk.DrawingArea.__init__(self)
        self.gvrparent = parent
        self.width = 0
        self.height = 0
        self.connect('size-allocate', self._on_size_allocate)
        self.connect('draw',  self._on_draw)
        self._load_images()
        # image sizes
        self.spi_x = self.splash_pixbuf.get_width()
        self.spi_y = self.splash_pixbuf.get_height()

        # all guidos are the same size and square
        self.guido_x = self.robot_n_pixbuf.get_width()
        self.guido_y = self.guido_x
        # size of the matrix cells
        self.square = 40
        self.offset = (0, 0)

        self.stuff_to_draw = [self._draw_splash]

    def __repr__(self):
        return "Canvas"

    def _load_images(self):
        """Put loading in a seperate method which can be overridden by WBCanvas
        to load different images"""
        self.dot_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'dot.png'))
        self.splash_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'gvr-splash.png'))
        self.robot_n_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_n.png'))
        self.robot_e_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_e.png'))
        self.robot_s_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_s.png'))
        self.robot_w_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_w.png'))

    def _on_draw(self, widget, cr):
        # This is where the drawing takes place
        for func in self.stuff_to_draw:
            func(widget, cr)
        return True

    def _on_size_allocate(self, widget, allocation):
        self.width = allocation.width
        self.height = allocation.height
        # print 'x,y', self.width,self.height
        self.screenX = self.width/self.square
        self.screenY = self.height/self.square
        return True

    def _fill_background(self, widget, cr, color=None):
        if color is None:
            color = Gdk.RGBA(1.0, 1.0, 1.0, 1.0)  # White
        Gdk.cairo_set_source_rgba(cr, color)
        cr.paint()

    def _draw_splash(self, widget, cr):
        """Draws the GvR splash screen onto the canvas."""
        self.world_size = (10, 10)
        x = self.world_size[0] * self.square
        y = self.world_size[1] * self.square
        self.set_size_request(x, y)
        self._fill_background(widget, cr)
        Gdk.cairo_set_source_pixbuf(cr, self.splash_pixbuf, 8, 8)
        cr.paint()

    # these methods are used to blit the world for the first time
    def _reset_offset(self):
        self.offset = (0, 0)
        self.screenX = self.width/self.square
        self.screenY = self.height/self.square

    def _draw_empty_world(self, widget, cr):
        if repr(self) == "WBCanvas":
            col = Gdk.RGBA(0.0, 0.0, 1.0, 1.0)  # Blue
        else:
            col = Gdk.RGBA(1.0, 0.0, 0.0, 1.0)  # Red
        self._fill_background(widget, cr)

        cr.set_line_width(2)

        # set numbers and outer walls
        y = self.height - self.square + 4
        step = self.square
        self.orig_x, self.orig_y = step+9, y-self.square+6
        end = self.width/self.square

        # draw horizontal outer red wall
        Gdk.cairo_set_source_rgba(cr, col)
        cr.move_to(step+4, y)
        cr.line_to(self.width, y)
        cr.stroke()

        step_y = self.height - self.square*2
        # draw vertical outer red wall
        cr.move_to(self.square+4, step_y+self.square+4)
        cr.line_to(self.square+4, 0)
        cr.stroke()

        # draw vertical labels
        Gdk.cairo_set_source_rgba(cr, Gdk.RGBA(0.0, 0.0, 0.0, 1.0))  # Black
        x_range_dots = range(int(self.square*2), self.width, self.square)
        for y_dot in range(1, self.height):
            # draw dots on x-axes
            for x_dot in x_range_dots:
                Gdk.cairo_set_source_pixbuf(cr, self.dot_pixbuf, x_dot, step_y)
                cr.paint()
            step_y -= self.square
        return True

    def _draw_labels(self, widget, cr):
        offset_x, offset_y = self.offset
        pangolayout = self.create_pango_layout('')
        font_desc = Pango.FontDescription('Serif 8')
        pangolayout.set_font_description(font_desc)

        Gdk.cairo_set_source_rgba(cr, Gdk.RGBA(0.0, 0.0, 0.0, 1.0))  # Black
        end = self.width/self.square
        y = self.height - self.square + 8
        step = self.square
        for x in range(1+offset_x, int(end)+offset_x+1):
            pangolayout.set_text('%d' % x)
            cr.move_to(step, y)
            PangoCairo.show_layout(cr, pangolayout)
            step += self.square

        step = self.height - self.square*2
        for y_label in range(1+offset_y, self.height+offset_y):
            pangolayout.set_text('%d' % y_label)
            cr.move_to(self.square/2, step+self.square/2)
            PangoCairo.show_layout(cr, pangolayout)
            step -= self.square

    def _draw_walls(self, widget, cr):
        Gdk.cairo_set_source_rgba(cr, Gdk.RGBA(1.0, 0.0, 0.0, 1.0))  # Red
        cr.set_line_width(3)
        walls = self.world.get_walls_position()
        offset_x, offset_y = self.offset
        for x, y in walls['west_wall']:
            x_pos = x * self.square + 4
            y_pos = self.height - self.square - y*self.square + 8
            cr.move_to(x_pos, y_pos)
            cr.line_to(x_pos, y_pos+(self.square-8))
            cr.stroke()
        for x, y in walls['south_wall']:
            x_pos = x * self.square + 8
            y_pos = self.height - y*self.square + 4
            cr.move_to(x_pos, y_pos)
            cr.line_to(x_pos+(self.square-8), y_pos)
            cr.stroke()

    def _remove_wall(self, d, x, y):
        # This needs a cairo context, so it should be called from _on_draw
        # For now, just queue a redraw
        self.queue_draw()

    def _draw_beepers(self, widget, cr):
        Gdk.cairo_set_source_rgba(cr, Gdk.RGBA(0.0, 0.0, 1.0, 1.0))  # Blue
        cr.set_line_width(4)
        for key, value in self.world.get_beepers().items():
            self._draw_beeper(cr, key, value)
        cr.set_line_width(2)

    def _draw_beeper(self, cr, pos, value):
        pos_x = self.orig_x + self.square*(pos[0]-1)
        pos_y = self.orig_y - self.square*(pos[1]-1)

        cr.arc(pos_x+2+11, pos_y+2+12, 11, 0, 2 * 3.14159)
        cr.stroke()

        pangolayout_beeper = self.create_pango_layout('')
        if utils.platform == 'XO':
            fn_size = '8'
        else:
            fn_size = '12'
        font_desc = Pango.FontDescription('Serif '+fn_size)
        pangolayout_beeper.set_font_description(font_desc)
        pangolayout_beeper.set_text('%d' % value)

        if value < 10:
            pos_x_text = pos_x + 8
        else:
            pos_x_text = pos_x + 4
        cr.move_to(pos_x_text, pos_y+4)
        PangoCairo.show_layout(cr, pangolayout_beeper)

    def _draw_robot(self, widget, cr):
        pos = self.world.get_robots_position()
        pos_x = self.orig_x + self.square*(pos[0]-1)
        pos_y = self.orig_y - self.square*(pos[1]-1)
        pixbuf = self._get_direction_pixbuf()
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, pos_x, pos_y)
        cr.paint()

    def _get_direction_pixbuf(self):
        return {
            'E': self.robot_e_pixbuf, 'W': self.robot_w_pixbuf,
            'N': self.robot_n_pixbuf, 'S': self.robot_s_pixbuf
        }[self.world.get_robots_direction()]

    def draw_splash(self):
        self.stuff_to_draw = [self._draw_splash]
        self.queue_draw()

    def draw_world(self, world):
        """Draws the complete world represented in @world"""
        self.world = world
        self.stuff_to_draw = [self._draw_empty_world,
                              self._draw_labels,
                              self._draw_walls,
                              self._draw_robot,
                              self._draw_beepers]
        self.queue_draw()

    def draw_scrolling_world(self, offset):
        self.logger.debug("draw_scrolling_world called")
        self.stuff_to_draw = [self._draw_empty_world,
                              self._draw_walls,
                              self._draw_beepers,
                              self._draw_labels]
        self.queue_draw()

    def draw_robot(self, obj, oldcoords):
        self.queue_draw()

    def draw_beeper(self, pos, value):
        self.queue_draw()

    def draw_beepers(self, obj):
        self.queue_draw()


class WBCanvas(Canvas):
    """Canvas used for the worldbuilder.
    It extends the canvas object used by the GUI.
    """

    def __init__(self, parent=None, wcode=[]):
        Canvas.__init__(self, parent=parent)
        if wcode:
            n_wcode = []
            for line in wcode:
                n_wcode.append(line+'\n')
            wcode = n_wcode
        self.wcode = wcode
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('button-press-event', self.on_button_press_event_cb)

        self.grab_focus()

    def __repr__(self):
        return "WBCanvas"

    def _load_images(self):
        """Override the Canvas._load_images method to provide different
        world dots."""
        self.dot_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'dot_wb.png'))
        self.splash_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'gvr-splash.png'))
        self.robot_n_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_n.png'))
        self.robot_e_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_e.png'))
        self.robot_s_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_s.png'))
        self.robot_w_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(utils.PIXMAPSDIR, 'guido_w.png'))

    def _calculate_position(self, mx, my):
        height = self.get_allocated_height() + 4
        mx -= 4
        x = int(mx) / self.square
        rx = max(1, int(mx) % self.square)
        y = (height - int(my)) / self.square
        ry = max(1, (height - int(my)) % self.square)
        if _WDEBUG:
            print("mouse x,y", mx, my)
            print("grid x,rx,y,ry", x, rx, y, ry)
        return (x, rx, y, ry)

    def reload_button_activated(self, wcode):
        n_wcode = []
        for line in wcode:
            n_wcode.append(line+'\n')
        self.wcode = n_wcode

    def on_button_press_event_cb(self, widget, event):
        wline, bline = '', ''
        if event.button == 1:
            valid = False
            x, rx, y, ry = self._calculate_position(event.x, event.y)
            if x < 1 or y < 1:
                return
            wline = "%s " % 'wall'
            if 30 <= rx <= 39:
                wline += "%s %s %s\n" % (x, y, 'E')
                valid = True
            elif 1 <= rx <= 10 and x > 1:
                wline += "%s %s %s\n" % (x-1, y, 'E')
                valid = True
            elif 30 <= ry <= 39:
                wline += "%s %s %s\n" % (x, y, 'N')
                valid = True
            elif 1 <= ry <= 10 and y > 1:
                wline += "%s %s %s\n" % (x, y-1, 'N')
                valid = True
            if not valid:
                return True
            if _WDEBUG:
                print(wline)

        elif event.button == 2:
            line = self.wcode[0].split(' ')
            if not 'robot' in line[0]:
                print("no robot statement found in the first line")
                return True

            dlg = RobotDialog()
            dlg.entry_x.set_text(line[1])
            dlg.entry_y.set_text(line[2])
            dlg.entry_dir.set_text(line[3])
            dlg.entry_beepers.set_text(line[4][:-1])
            response = dlg.RobotDialog.run()

            if response == Gtk.ResponseType.OK:
                choice = dlg.get_choice()
                dlg.RobotDialog.destroy()
            else:
                dlg.RobotDialog.destroy()
                return True

            line[1] = choice[0]
            line[2] = choice[1]
            line[3] = choice[2]
            line[4] = choice[3]
            self.wcode[0] = ' '.join(line)+'\n'
            self.gvrparent.world_editor.editor.set_text(self.wcode)
            self.gvrparent.on_button_reload()
            return True

        elif event.button == 3:
            x, xx, y, yy = self._calculate_position(event.x, event.y)
            if x < 1 or y < 1:
                return True
            dlg = BeeperDialog(
                txt="Please give the number of beepers\nto place on %d,%d\n (Number must be > 0)" % (x, y))
            beepersline = '%s %s %s' % ('beepers'), x, y
            for line in self.wcode:
                if line.find(beepersline) != -1:
                    self.wcode.remove(line)
                    dlg.entrybox.set_text(line.split(' ')[3][:-1])
                    break
            response = dlg.run()
            if response == Gtk.ResponseType.OK:
                num_beepers = dlg.get_choice()
                if not num_beepers:
                    self.gvrparent.world_editor.editor.set_text(self.wcode)
                    self.gvrparent.on_button_reload()
                    dlg.destroy()
                    WarningDialog(
                        txt='Beeper values must be zero or more.\nUse zero as the value to remove beeper(s)')
                    return True
                bline = "%s %d %d %d\n" % ('beepers'), x, y, num_beepers
            dlg.destroy()

        wcode = list(filter(None, [wline, bline]))
        if wcode:
            if event.button == 1:
                t, x, y, d = wline.split(' ')
                result = self.world.setWall_wb(x, y, lookup_dir_dict[d[:-1]])
                if result[2] == 0:
                    self._remove_wall(result[0], result[1][0], result[1][1])
                    self.wcode.remove(wcode[0])
                else:
                    self.queue_draw()
                    if wcode[0] not in self.wcode:
                        self.wcode = self.wcode + wcode
            if event.button == 3:
                if wcode[0] not in self.wcode:
                    self.wcode = self.wcode + wcode
            self.gvrparent.world_editor.editor.set_text(self.wcode)
            if event.button == 3:
                self.gvrparent.on_button_reload()
        return True


class Timer:
    def __init__(self):
        self.timer_id = None
        import atexit
        atexit.register(self.stop)

    def wakeup(self):
        if self.timer_id:
            self.func()
            return True
        return False

    def start(self):
        print("Starting timer...")
        self.timer_id = GLib.timeout_add(self.interval, self.wakeup)

    def stop(self):
        try:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
        except:
            pass

    def set_func(self, func):
        self.func = func

    def set_interval(self, interval):
        self.interval = interval


class RobotDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.ui", root="RobotDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        pass

    def get_choice(self):
        return (self.entry_x.get_text(),
                self.entry_y.get_text(),
                self.entry_dir.get_text(),
                self.entry_beepers.get_text())

    def on_RobotDialog_delete_event(self, widget, *args):
        self.RobotDialog.destroy()


class StatusBar:
    def __init__(self, glade_obj):
        self.logger = logging.getLogger("gvr.Widgets.StatusBar")
        self.statusbar = glade_obj
        self.context_id = self.statusbar.get_context_id('gvr_gtk')
        self.barmesg = "Robots position is %s %s %s and carrying %s beepers"
        self.beep = 0
        self.pos = ((1, 1), 'N')
        self.data = [self.pos[0][0], self.pos[0][1], self.pos[1], self.beep]

    def update_robotposition(self, pos):
        self.data[0], self.data[1], self.data[2] = pos[0][0], pos[0][1], pos[1]
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, self.barmesg % tuple(self.data))

    def update_robotbeepers(self, beep):
        self.data[3] = beep
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, self.barmesg % tuple(self.data))

    def set_text(self, text):
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, text)

    def clear(self):
        self.statusbar.pop(self.context_id)


class WebToolbar(Gtk.Toolbar):
    def __init__(self, browser):
        try:
            from sugar3.graphics.toolbutton import ToolButton
        except ImportError:
            from gi.repository.Gtk import ToolButton
        self.logger = logging.getLogger("gvr.Widgets.WebToolbar")
        Gtk.Toolbar.__init__(self)
        self._browser = browser

        self._back = ToolButton('go-previous')
        self._back.set_tooltip_text('Go back one page')
        self._back.connect('clicked', self._go_back_cb)
        self.insert(self._back, -1)
        self._back.show()

        self._forw = ToolButton('go-next')
        self._forw.set_tooltip_text('Go one page forward')
        self._forw.connect('clicked', self._go_forward_cb)
        self.insert(self._forw, -1)
        self._forw.show()

    def _go_forward_cb(self, button):
        self._browser.go_forward()

    def _go_back_cb(self, button):
        self._browser.go_back()


def get_active_text(combobox):
    if isinstance(combobox, Gtk.ComboBoxText):
        return combobox.get_active_text()

    model = combobox.get_model()
    active = combobox.get_active()
    if active < 0:
        return None
    return model[active][0]

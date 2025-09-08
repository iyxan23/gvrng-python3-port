#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           gvr_gtk.py
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation. A copy of this license should
# be included in the file GPL-3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import version
from .SimpleGladeApp import SimpleGladeApp
from .SimpleGladeApp import bindtextdomain
from gi.repository import Gtk, Gdk, GLib
import logging
import os
import sys
import Text
import utils
import gui.Widgets
import gi
gi.require_version('Gtk', '3.0')
app_name = "gvrng"  # used to set gettext
app_version = version.VERSION


glade_dir = utils.FRONTENDDIR
locale_dir = utils.LOCALEDIR

module_logger = logging.getLogger("gvr.gvr_gtk")

PLATFORM = utils.platform
if PLATFORM == 'XO':
    try:
        from sugar3.activity import activity as sgactivity
    except ImportError:
        from . import fake_sugar_activity as sgactivity
else:
    from . import fake_sugar_activity as sgactivity
module_logger.debug("Using sugar activity module: %s" % sgactivity)

if sys.platform == 'win32':
    from . import Win_Editors as Editors
else:
    from . import Editors

bindtextdomain(app_name, utils.get_locale(), locale_dir)


class Globals:
    speed = 'Medium'


class Window(SimpleGladeApp):
    def __init__(self, parent=None, path="gvr_gtk.ui", root="window_main", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

        self.logger = logging.getLogger("gvr.gvr_gtk.Window")
        if PLATFORM != 'XO':
            self.parentGUI = self.window_main
            self.windowtitle = "GvRng"
            self.parentGUI.set_title(self.windowtitle)
            file = os.path.join(os.getcwd(), 'gui-gtk',
                                'pixmaps', 'gvrIcon.bmp')
            try:
                self.parentGUI.set_icon_from_file(file)
            except GLib.Error:
                self.logger.exception("Can't load window icon")
            self.parentGUI.connect('delete_event', self.stop)

            self.parentGUI.add_events(Gdk.EventMask.KEY_PRESS_MASK)

            if hasattr(self, 'eventboxlessons'):
                self.eventboxlessons.destroy()
            if hasattr(self, 'lessons'):
                self.lessons.destroy()

        txt = Text.OnRefText
        buffer = Gtk.TextBuffer(table=None)
        try:
            txt = ''.join(txt)
            utxt = str(txt)
        except Exception as info:
            self.logger.exception(
                "Failed to set reference text in source buffer")
            return
        buffer.set_text(utxt)
        self.textview_languagereference.set_buffer(buffer)
        self.textview_languagereference.show_all()

        txt = Text.OnIntroText
        buffer = Gtk.TextBuffer(table=None)
        try:
            txt = ''.join(txt)
            utxt = str(txt)
        except Exception as info:
            self.logger.exception("Failed to set intro text in source buffer")
            return
        buffer.set_text(utxt)
        self.textview_intro.set_buffer(buffer)
        self.textview_intro.show_all()

        try:
            if utils.RCDICT['default']['intro'].lower() == 'yes':
                self.notebook1.set_current_page(-1)
                utils.setRcEntry('intro', 'no')
        except KeyError:
            pass

    def new(self):
        self.statusbar = gui.Widgets.StatusBar(self.statusbar7)
        self._setup_canvas()
        self.new_world_editor()
        self.new_program_editor()
        self._set_sensitive_button('all', True)
        self.timerinterval = 150

    def new_world_editor(self):
        self.world_editor = WorldTextEditorWin(parent=self)

    def new_program_editor(self):
        self.program_editor = CodeTextEditorWin(parent=self)

    def _setup_canvas(self):
        self._canvas = gui.Widgets.Canvas()
        self.viewport = Gtk.Viewport()
        self.scrolledwindow8.add(self.viewport)
        self.viewport.add(self._canvas)
        self.scrolledwindow8.show_all()
        self._set_sensitive_button('all', False)
        self.WB_ACTIVATED = False

    def _set_sensitive_button(self, button, value):
        if button == 'all':
            for b in (self.button_abort, self.button_execute,
                      self.button_reload, self.button_step):
                b.set_sensitive(value)
        else:
            but = {'abort': self.button_abort,
                   'reload': self.button_reload,
                   'execute': self.button_execute,
                   'step': self.button_step}[button]
            but.set_sensitive(value)
        if (button == 'all' or button in ('reload', 'step')) and not value:
            self.statusbar.clear()

    def start(self, *args):
        self.logger.debug("start called with args: %s" % str(args))
        if args and len(args) > 1 and args[0] and args[1]:
            wfile, pfile = args[0], args[1]
            self.world_editor.on_open1_activate(file=wfile)
            self.program_editor.on_open1_activate(file=pfile)
        if PLATFORM != 'XO':
            self.parentGUI.show()
            self.run()

    def get_timer(self):
        return gui.Widgets.Timer()

    def get_timer_interval(self):
        return self.timerinterval

    def stop(self, *args):
        Gtk.main_quit()

    def set_controller(self, contr):
        self.logger.debug("controller set in %s" % self)
        self.controller = contr

    def worldwin_gettext(self):
        if self.world_editor:
            wcode = self.world_editor.get_all_text()
            if wcode:
                return wcode
        self.show_warning("You don't have a world file loaded.")

    def codewin_gettext(self):
        if self.program_editor:
            pcode = self.program_editor.get_all_text()
            if pcode:
                return pcode
        self.show_warning("You don't have a program file loaded.")

    def highlight_line_code_editor(self, line):
        try:
            self.program_editor.editor.set_highlight(line)
        except Exception as info:
            print(info)

    def show_warning(self, txt):
        gui.Widgets.WarningDialog(txt=txt)

    def show_error(self, txt):
        gui.Widgets.ErrorDialog(txt=txt)

    def show_info(self, txt):
        gui.Widgets.InfoDialog(txt=txt)

    def update_world(self, obj):
        self._canvas.draw_world(obj)
        pos = self.controller.get_robot_position()
        self.logger.debug(
            "received from controller robot position %s,%s" % pos)
        self.statusbar.update_robotposition(pos)
        beep = self.controller.get_robot_beepers()
        self.logger.debug(
            "received from controller number of beepers %s" % beep)
        self.statusbar.update_robotbeepers(beep)

    def update_robot_world(self, obj, oldcoords=None):
        self._canvas.draw_robot(obj, oldcoords)
        pos = self.controller.get_robot_position()
        self.statusbar.update_robotposition(pos)

    def update_beepers_world(self, obj):
        self._canvas.draw_beepers(obj)
        beep = self.controller.get_robot_beepers()
        self.statusbar.update_robotbeepers(beep)

    def on_MainWin_delete_event(self, widget, *args):
        self.on_quit1_activate(widget)
        return True

    def on_open_worldbuilder1_activate(self, widget, *args):
        self.logger.debug("worldbuilder_activate")
        self.WB_ACTIVATED = True
        if PLATFORM != 'XO':
            self.windowtitle = self.parentGUI.get_title()
            self.parentGUI.set_title("GvR - Worldbuilder")

        self._set_sensitive_button('all', False)
        self._set_sensitive_button('reload', True)
        self._set_sensitive_button('abort', True)

        wcode = ["%s 1 1 %s 0" % ("robot", "E")]
        if self.world_editor.get_all_text():
            wcode = self.world_editor.get_all_text()
        else:
            self.world_editor.editor.set_text(wcode)

        self.oldcanvas = self._canvas
        self.viewport.remove(self._canvas)
        self._canvas = gui.Widgets.WBCanvas(parent=self, wcode=wcode)
        self.viewport.add(self._canvas)
        self.scrolledwindow8.show_all()
        self.on_button_reload()
        self.statusbar.set_text("Running Worldbuilder")

    def on_quit1_activate(self, widget, *args):
        self.logger.debug("on_quit1_activate called")
        try:
            self.program_editor.on_quit2_activate()
        except Exception as info:
            pass
        try:
            self.world_editor.on_quit2_activate()
        except Exception as info:
            pass
        dlg = QuitDialog()
        dlg.QuitDialog.show()

    def on_set_speed1_activate(self, widget, *args):
        dlg = SetSpeedDialog()
        response = dlg.SetSpeedDialog.run()
        if response == Gtk.ResponseType.OK:
            self.timerinterval = dlg.get_choice()
        dlg.SetSpeedDialog.destroy()

    def on_gvr_lessons1_activate(self, widget, *args):
        import webbrowser
        file = os.path.join(utils.get_rootdir(), 'docs', 'lessons', utils.get_locale()[
                            :2], 'html', 'index.html')
        self.logger.debug("Looking for the lessons in %s" % file)
        if not os.path.exists(file) and utils.get_locale()[:2] != 'en':
            file = os.path.join(utils.get_rootdir(), 'docs',
                                'lessons', 'en', 'html', 'index.html')
            self.logger.debug("Looking for the lessons in %s" % file)
        if os.path.exists(file):
            try:
                webbrowser.open('file://' + os.path.abspath(file), new=0)
            except webbrowser.Error as info:
                txt = str(
                    info) + '\n' + "Be sure to set your env. variable 'BROWSER' to your preffered browser."
                self.show_warning(txt)
        else:
            self.show_warning(
                "Can't find the lessons.\nMake sure you have installed the GvR-Lessons package.\nCheck the GvR website for the lessons package.\nhttp://gvr.sf.net")

    def on_gvr_worldbuilder1_activate(self, *args):
        dlg = SummaryDialog()
        dlg.set_text(Text.OnWBText)

    def on_about1_activate(self, widget, *args):
        dlg = AboutDialog()

    def on_button_reload(self, *args):
        wcode = self.worldwin_gettext()
        if wcode:
            self.controller.on_button_reload(wcode)
        self.program_editor.reset_highlight()
        self._canvas._reset_offset()
        if self.WB_ACTIVATED and wcode:
            self._canvas.reload_button_activated(wcode)
        return True

    def on_button_step(self, widget, *args):
        self.controller.on_button_step()
        return True

    def on_button_execute(self, widget, *args):
        self.controller.on_button_execute()
        return True

    def on_button_abort(self, widget=None, *args):
        if self.WB_ACTIVATED:
            if PLATFORM != 'XO':
                self.parentGUI.set_title(self.windowtitle)
            self._set_sensitive_button('all', False)
            self.scrolledwindow8.remove(self.viewport)
            self._setup_canvas()
            if not widget:
                self.world_editor = None
            if self.world_editor:
                self._set_sensitive_button('reload', True)
                self.on_button_reload()
            if self.program_editor:
                for b in ('execute', 'step', 'abort'):
                    self._set_sensitive_button(b, True)
        else:
            self.controller.on_button_abort()

    def on_statusbar1_text_popped(self, widget, *args):
        pass

    def on_statusbar1_text_pushed(self, widget, *args):
        pass


class WindowXO(Window):
    def __init__(self, handle, parent=None, path="gvr_gtk.ui", root="window_main", domain=app_name, **kwargs):
        Window.__init__(self, parent=parent, path=path,
                        root=root, domain=domain)
        self._parent = parent
        self.logger = logging.getLogger("gvr.gvr_gtk.WindowXO")

        toolbox = sgactivity.ActivityToolbox(self._parent)
        self._parent.set_toolbox(toolbox)
        toolbox.show()

        self._frame = self.frame5
        self.window_main.remove(self._frame)
        self._parent.set_canvas(self._frame)
        self._frame.show()

        self.separatormenuitem14.destroy()
        self.imagemenuitem49.destroy()

        self.logger.debug("import webview")
        try:
            gi.require_version('WebKit2', '4.0')
            from gi.repository import WebKit2
            self.WV = WebKit2.WebView()
            file = os.path.join(utils.get_rootdir(), 'docs', 'lessons', utils.get_locale()[
                                :2], 'html', 'index.html')
            self.logger.debug("Looking for the lessons in %s" % file)
            if not os.path.exists(file):
                self.logger.debug(
                    "%s not found, loading default English lessons" % file)
                file = os.path.join(utils.get_rootdir(), 'docs',
                                    'lessons', 'en', 'html', 'index.html')
            self.WV.load_uri('file:///' + os.path.abspath(file))
            self.WV.show()
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            vbox.pack_start(gui.Widgets.WebToolbar(self.WV), False, False, 2)
            vbox.pack_start(self.WV, True, True, 2)
            vbox.show_all()
            self.eventboxlessons.add(vbox)
        except (ImportError, ValueError) as e:
            self.logger.error("Could not import WebKit2: %s" % e)


class QuitDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.ui", root="QuitDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        pass

    def on_QuitDialog_delete_event(self, widget, *args):
        self.QuitDialog.destroy()

    def on_dialog_okbutton1_clicked(self, widget, *args):
        self.quit()


class AboutDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.ui", root="AboutDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        txt = version.ABOUT_TEXT % app_version
        self.text_label.set_text(txt)
        self.text_label.show()
        self.AboutDialog.show()

    def on_AboutDialog_delete_event(self, widget, *args):
        self.AboutDialog.destroy()


class FileDialog(Gtk.FileChooserDialog):
    def __init__(self, action='open', title='', path=os.path.expanduser('~'), ext='wld'):
        if action == 'open':
            act = Gtk.FileChooserAction.OPEN
            but_text = "_Open"
        else:
            act = Gtk.FileChooserAction.SAVE
            but_text = "_Save"
        Gtk.FileChooserDialog.__init__(self, title=title, action=act)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         but_text, Gtk.ResponseType.OK)

        try:
            startpath = utils.PROGRAMSDIR
        except:
            startpath = utils.get_rootdir()
        self.set_current_folder(startpath)
        wfilter = Gtk.FileFilter()
        wfilter.set_name("Worlds")
        wfilter.add_pattern('*.wld')
        self.add_filter(wfilter)

        pfilter = Gtk.FileFilter()
        pfilter.set_name("Programs")
        pfilter.add_pattern('*.gvr')
        self.add_filter(pfilter)

        if ext == 'wld':
            self.set_filter(wfilter)
        else:
            self.set_filter(pfilter)


class TextEditorWin(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.ui", root="EditorWin", domain=app_name, parent=None, **kwargs):
        path = os.path.join(glade_dir, path)
        self.logger = logging.getLogger("gvr_gtk.TextEditorWin")
        self.parent = parent
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)
        self.loaded_file_path = ''
        self.loaded_txt = []

    def new(self):
        self.editor = Editors.Editor(self.scrolledwindow1)
        self.observers = []

    def set_title(self, title):
        self.EditorWin.set_title(title)

    def get_all_text(self):
        try:
            txt = self.editor.get_all_text()
        except:
            txt = []
        return txt

    def set_text(self, path, txt):
        self.loaded_file_path = path
        self.editor.set_text(txt)
        self.loaded_txt = self.get_all_text()

    def on_new1_activate(self, widget, *args):
        pass

    def on_open1_activate(self, widget, *args, file=''):
        pass

    def on_save1_activate(self, widget=None, txt=[]):
        if not txt:
            txt = self.get_all_text()
            self.loaded_txt = txt
        if not txt:
            gui.Widgets.WarningDialog(txt="No content to save")
            return
        if self.loaded_file_path:
            ext = '.'+str(self)
            if not self.loaded_file_path.endswith(ext):
                self.loaded_file_path = self.loaded_file_path+ext
            status = utils.save_file(self.loaded_file_path, txt)
            if status:
                gui.Widgets.ErrorDialog(txt=status)
            else:
                return True
        else:
            self.on_save_as1_activate(txt=txt)

    def on_save_as1_activate(self, widget=None, txt=[]):
        dlg = FileDialog(action='save', title='Choose a file', ext=str(self))
        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            path = dlg.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            self.logger.debug('Closed, no files selected')
            dlg.destroy()
            return True
        dlg.destroy()
        self.loaded_file_path = path
        if self.on_save1_activate(txt=txt):
            self.set_title(path)

    def on_quit2_activate(self, widget=None, *args):
        edittxt = self.get_all_text()
        if edittxt != self.loaded_txt:
            dlg = gui.Widgets.YesNoDialog(
                txt="The %s editor's content is changed.\nDo you want to save it?" % self.name())
            response = dlg.run()
            dlg.destroy()
            if response == Gtk.ResponseType.YES:
                self.on_save_as1_activate(txt=edittxt)
            else:
                return True

    def on_cut1_activate(self, widget, *args):
        self.editor.srcview.get_buffer().cut_clipboard(
            Gtk.Clipboard.get('CLIPBOARD'), True)

    def on_copy1_activate(self, widget, *args):
        self.editor.srcview.get_buffer().copy_clipboard(Gtk.Clipboard.get('CLIPBOARD'))

    def on_paste1_activate(self, widget, *args):
        self.editor.srcview.get_buffer().paste_clipboard(
            Gtk.Clipboard.get('CLIPBOARD'), None, True)

    def on_delete1_activate(self, widget, *args):
        self.editor.srcview.get_buffer().delete_selection(True, True)

    def on_print1_activate(self, widget, *args):
        # Printing is complex in GTK3, requires a Gtk.PrintOperation
        # This is a simplified placeholder
        print("Printing not fully implemented in this port.")

    def reset_highlight(self):
        self.editor.reset_highlight()


class CodeTextEditorWin(TextEditorWin):
    def __init__(self, path="gvr_gtk.ui", root="EditorWin", domain=app_name, parent=None, **kwargs):
        TextEditorWin.__init__(self, path, root, domain, parent, **kwargs)
        self.parent = parent
        self.EditorWin.remove(self.vbox4)
        for child in self.parent.alignment19.get_children():
            self.parent.alignment19.remove(child)
        self.parent.alignment19.add(self.vbox4)

    def __str__(self):
        return 'gvr'

    def name(self):
        return 'Code'

    def on_new1_activate(self, widget=None, file=''):
        self.on_quit2_activate()
        self.parent.new_program_editor()

    def on_open1_activate(self, widget=None, file=''):
        if not file:
            dlg = FileDialog(
                action='open', title="Open GvR program", ext='gvr')
            response = dlg.run()
            if response == Gtk.ResponseType.OK:
                file = dlg.get_filename()
                if os.path.splitext(file)[1] != '.gvr':
                    self.show_error("Selected path is not a program file")
                    dlg.destroy()
                    return
            elif response == Gtk.ResponseType.CANCEL:
                self.logger.debug('Closed, no files selected')
                dlg.destroy()
                return
            dlg.destroy()
        txt = utils.load_file(file)
        if txt:
            self.set_text(file, txt)
        for b in ('execute', 'step', 'abort'):
            self.parent._set_sensitive_button(b, True)
        return


class WorldTextEditorWin(TextEditorWin):
    def __init__(self, path="gvr_gtk.ui", root="EditorWin", domain=app_name, parent=None, **kwargs):
        TextEditorWin.__init__(self, path, root, domain, parent, **kwargs)
        self.parent = parent
        self.EditorWin.remove(self.vbox4)
        for child in self.parent.alignment18.get_children():
            self.parent.alignment18.remove(child)
        self.parent.alignment18.add(self.vbox4)

    def __str__(self):
        return 'wld'

    def name(self):
        return 'World'

    def on_new1_activate(self, widget=None, file=''):
        self.on_quit2_activate()
        self.parent.new_world_editor()

    def on_open1_activate(self, widget=None, file=''):
        self.on_quit2_activate()
        if not file:
            dlg = FileDialog(action='open', title="Open GvR world", ext='wld')
            response = dlg.run()
            if response == Gtk.ResponseType.OK:
                file = dlg.get_filename()
                if os.path.splitext(file)[1] != '.wld':
                    self.show_error("Selected path is not a world file")
                    dlg.destroy()
                    return
            elif response == Gtk.ResponseType.CANCEL:
                self.logger.debug('Closed, no files selected')
                dlg.destroy()
                return
            dlg.destroy()
        txt = utils.load_file(file)
        if txt:
            self.set_text(file, txt)
            self.parent.on_button_reload()
        return


class SetLanguageDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.ui", root="SetLanguageDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        pass

    def get_choice(self):
        try:
            choice = {'Catalan': 'ca', 'Dutch': 'nl', 'English': 'en', 'French': 'fr',
                      'Norwegian': 'no', 'Romenian': 'ro', 'Spanish': 'es', 'Italian': 'it'}[gui.Widgets.get_active_text(self.comboboxentry_language)]
        except Exception as info:
            print(info)
            choice = 'en'
        return choice

    def on_SetLanguageDialog_delete_event(self, widget, *args):
        self.SetLanguageDialog.destroy()


class SetSpeedDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.ui", root="SetSpeedDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        choice = {'Instant': 0, 'Fast': 1,
                  'Medium': 2, 'Slow': 3}[Globals.speed]
        self.comboboxentry_speed.set_active(choice)

    def get_choice(self):
        try:
            txt = gui.Widgets.get_active_text(self.comboboxentry_speed)
            choice = {'Instant': 5, 'Fast': 50,
                      'Medium': 150, 'Slow': 500}[txt]
        except Exception as info:
            print(info)
            choice = 150
        Globals.speed = txt
        return choice

    def on_SetSpeedDialog_delete_event(self, widget, *args):
        self.SetSpeedDialog.destroy()


class SummaryDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.ui", root="SummaryDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        pass

    def set_text(self, txt):
        title = txt.split('\n')[0]
        buffer = Gtk.TextBuffer(table=None)
        try:
            txt = ''.join(txt)
            utxt = str(txt)
        except Exception as info:
            print("Failed to set text in source buffer")
            print(info)
            return
        self.SummaryDialog.set_title(title)
        buffer.set_text(utxt)
        self.textview1.set_buffer(buffer)

    def on_SummaryDialog_delete_event(self, widget, *args):
        self.SummaryDialog.destroy()


def main():
    main_win = Window()
    main_win.start()


if __name__ == "__main__":
    main()

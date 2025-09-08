# -*- coding: utf-8 -*-

# Copyright (c) 2006 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           Win_Editors.py
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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango, PangoCairo

E_DEBUG = 0

class Editor:
    """Wraps a textview widget and adds a few abstraction methods."""
    def __init__(self,parent,title=''):
        self.parent = parent
        
        self.frame = Gtk.Frame()
        
        self.txttagtable = Gtk.TextTagTable()
        self.txtbuffer = Gtk.TextBuffer(table=self.txttagtable)
        
        self.tag_h = self.txtbuffer.create_tag(None, background='lightblue')
        
        self.txtview = Gtk.TextView(buffer=self.txtbuffer)
        self.txtview.set_border_window_size(Gtk.TextWindowType.LEFT, 30)
        self.txtview.connect("draw", self.line_numbers_draw)
        
        self.parent.add(self.txtview)
        self.parent.show_all()
        
        self.old_start_iter = None

    def get_all_text(self):
        """Return all text from the widget"""
        startiter = self.txtbuffer.get_start_iter()
        enditer = self.txtbuffer.get_end_iter()
        txt = self.txtbuffer.get_text(startiter,enditer, True)
        if not txt:
            return []
        if '\n' in txt:
            txt = txt.split('\n')
        else:# assuming a line without a end of line
            txt = [txt]
        return txt
        
    def set_text(self,txt):
        """Load a text in the widget"""
        if E_DEBUG: print(self.__class__,'set_text',txt)
        try:
            txt = ''.join(txt)
            utxt = str(txt)
        except Exception as info:
            print("Failed to set text in source buffer")
            print(info)
            return
        self.txtbuffer.set_text(utxt.rstrip('\n'))
        
    def set_highlight(self,line):
        """Highlight the line in the editor"""
        if self.old_start_iter:
            self.txtbuffer.remove_tag(self.tag_h,self.old_start_iter,self.old_end_iter)
        if line > 0:
            start_iter = self.txtbuffer.get_iter_at_line(line - 1)
            end_iter = self.txtbuffer.get_iter_at_line(line - 1)
            end_iter.forward_to_line_end()  
            self.txtbuffer.apply_tag(self.tag_h,start_iter,end_iter)
            self.old_start_iter,self.old_end_iter = start_iter,end_iter
    
    def reset_highlight(self):
        if self.old_start_iter:
            self.txtbuffer.remove_tag(self.tag_h,self.old_start_iter,self.old_end_iter)
            self.old_start_iter = None

    def line_numbers_draw(self, widget, cr):
        left_win = self.txtview.get_window(Gtk.TextWindowType.LEFT)
        if not left_win:
            return

        cr.set_source_rgb(0.8, 0.8, 0.8)
        cr.paint()

        cr.set_source_rgb(0, 0, 0)
        layout = PangoCairo.create_layout(cr)
        font_desc = Pango.FontDescription("Monospace 10")
        layout.set_font_description(font_desc)

        visible_rect = self.txtview.get_visible_rect()
        start_iter, end_iter = self.txtview.get_buffer().get_bounds()

        line_num = start_iter.get_line() + 1
        while not start_iter.is_end():
            y, line_height = self.txtview.get_line_yrange(start_iter)
            if y >= visible_rect.y + visible_rect.height:
                break

            if y >= visible_rect.y:
                layout.set_text(str(line_num), -1)
                x, _ = self.txtview.buffer_to_window_coords(Gtk.TextWindowType.LEFT, 0, y)
                cr.move_to(5, y)
                PangoCairo.show_layout(cr, layout)

            start_iter.forward_line()
            line_num += 1
# -*- coding: utf-8 -*-
# Copyright (c) 2006-2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           Editors.py
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

# Wraps the gtksourceview

import re
import gi
import utils
import os
import logging
module_logger = logging.getLogger("gvr.Editors")
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, GtkSource
GtkSource.init()


class Editor:
    """Wraps a GtkSource.View widget and adds a few abstraction methods."""

    def __init__(self, parent, title=''):
        self.parent = parent
        self.logger = logging.getLogger("gvr.Editors.Editor")
        # remove any children from previous sessions
        for child in self.parent.get_children():
            self.parent.remove(child)
        # Look for the locale to which the syntax highlighting should be set
        # We assume the locale is available, if not there won't be any higlighting.
        try:
            loc = utils.get_locale()[:2]
        except Exception as info:
            self.logger.exception("Error in checking locale")
            loc = ''
        if loc:
            mime = 'gvr_%s' % loc
        else:
            mime = 'gvr_en'

        self.srcbuffer = GtkSource.Buffer()
        self.srcview = GtkSource.View(buffer=self.srcbuffer)
        man = GtkSource.LanguageManager.get_default()
        self.logger.debug("set search path to %s" % utils.GTKSOURCEVIEWPATH)
        search_path = man.get_search_path()
        search_path.append(utils.GTKSOURCEVIEWPATH)
        man.set_search_path(search_path)

        self.srcbuffer.set_highlight_syntax(True)
        lang = man.get_language(mime)
        if lang:
            self.logger.debug(
                "gtksourceview buffer syntax higlight set to %s" % mime)
            self.srcbuffer.set_language(lang)
        else:
            self.logger.warning(
                "Could not find language definition for %s" % mime)

        self.srcview.set_tab_width(4)
        self.tag_h = self.srcbuffer.create_tag(None, background='lightblue')
        self.srcbuffer.set_max_undo_levels(10)
        self.srcview.set_show_line_numbers(True)
        self.srcview.set_insert_spaces_instead_of_tabs(True)
        self.srcview.set_auto_indent(True)
        self.parent.add(self.srcview)
        self.parent.show_all()

        self.srcbuffer.connect("delete-range", self.delete_tabs)
        self.srcbuffer.connect("insert-text", self.format)
        self.old_start_iter = None

    def get_all_text(self):
        """Return all text from the widget"""
        startiter = self.srcbuffer.get_start_iter()
        enditer = self.srcbuffer.get_end_iter()
        txt = self.srcbuffer.get_text(startiter, enditer, True)
        if not txt:
            return []
        if '\n' in txt:
            txt = txt.split('\n')
        else:  # assuming a line without a end of line
            txt = [txt]
        return txt

    def set_text(self, txt):
        """Load a text in the widget"""
        try:
            txt = ''.join(txt)
            utxt = str(txt)
        except Exception as info:
            print("Failed to set text in source buffer")
            print(info)
            return

        self.srcbuffer.set_text(utxt)

    def set_highlight(self, line):
        """Highlight the line in the editor"""
        if self.old_start_iter:
            self.srcbuffer.remove_tag(
                self.tag_h, self.old_start_iter, self.old_end_iter)

        if line > 0:
            start_iter = self.srcbuffer.get_iter_at_line(line - 1)
            end_iter = self.srcbuffer.get_iter_at_line(line - 1)
            end_iter.forward_to_line_end()
            self.srcbuffer.apply_tag(self.tag_h, start_iter, end_iter)
            self.old_start_iter, self.old_end_iter = start_iter, end_iter

    def reset_highlight(self):
        if self.old_start_iter:
            self.srcbuffer.remove_tag(
                self.tag_h, self.old_start_iter, self.old_end_iter)
            self.old_start_iter = None

    def format(self, srcview, iter, text, leng):
        if text == "\n":
            startiter = self.srcbuffer.get_start_iter()
            enditer = self.srcbuffer.get_iter_at_mark(
                self.srcbuffer.get_insert())
            code = self.srcbuffer.get_text(startiter, enditer, False)
            if len(code) > 0 and code.rstrip().endswith(":"):
                line = code.split('\n')[-1]
                indent = re.match(r"^\s*", line).group()
                self.srcbuffer.insert_at_cursor("\n"+indent + "    ")

    def delete_tabs(self, srcview, start, end):
        # This seems to be custom backspace logic. It might need review.
        pass

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# canvas.py by:
#    Agustin Zubiaga <aguz@sugarlabs.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import gobject
import gconf
import pango
import threading
import utils

from gettext import gettext as _
from sugar.graphics.icon import CellRendererIcon
from sugar.graphics.xocolor import XoColor
from sugar.graphics import style

BTN_COLOR = gtk.gdk.color_parse("blue")
ITERS = []

# Logging
_logger = utils.get_logger()

# Xo Color #
client = gconf.client_get_default()
color = XoColor(client.get_string('/desktop/sugar/user/color'))


def _gen_activity(_id, parent):
        _id = _id
        _activity_props = parent._list[_id]
        text1 = "<b>Description: </b>%s" % _activity_props[3]
        text2 = "<b>Version: </b>%s" % _activity_props[4]
        text3 = "<b>Works with: </b>%s" % (_activity_props[5] + ' - ' + _activity_props[6])
        text4 = "<b>Updated: </b>%s" % _activity_props[7]
        text5 = "<b>Downloads: </b>%s" % _activity_props[8]
        text6 = "<b>Homepage: </b>%s" % _activity_props[9]
        text =  text1 + "\n" + text2 + "\n" + text3 + "\n" + text4 + "\n" + text5 + "\n" + text6 

        pixbuf_icon = _activity_props[0]
	name = "<b>%s</b>" % _activity_props[2]	

        status = _activity_props[1]              
        if status == "E":
		status = _("Experimental")
	else:
		status = _("Public")
	info = [pixbuf_icon, name, text, status]
        return info



class Canvas(gtk.Notebook):

    def __init__(self, parent):
        gtk.Notebook.__init__(self)

        self._parent = parent

        # Search List
        self.gtk_list = List(self._parent)

        eventbox = gtk.EventBox()
        eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#FFFFFF"))
        eventbox.add(self.gtk_list)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.add_with_viewport(eventbox)

        self.append_page(scroll)

        # Download List
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        scroll.add_with_viewport(self.gtk_list.download_list)
        self.append_page(scroll)

        self.set_property('show-tabs', False)

        self.show_all()

    def switch_to_list(self, widget):
        self.set_page(0)
        if not widget:
            self._parent.store_list.set_active(True)

    def switch_to_downloads_list(self, widget):
        self.set_page(1)


class List(gtk.TreeView):

    def __init__(self, parent):
        gtk.TreeView.__init__(self)

        self._model = gtk.ListStore(str, str, str, str)
        self.set_model(self._model)

        self.icon = CellRendererIcon(self)
	self.icon._buffer.width = style.zoom(100)
	self.icon._buffer.height = style.zoom(100)
	self.icon._xo_color = color
        self._name = gtk.CellRendererText()
        self.description = gtk.CellRendererText()
        self.status = gtk.CellRendererText()
        self.description.props.wrap_mode = True
        
        self.icon_column = gtk.TreeViewColumn(_("Icon"))
        self._name_column = gtk.TreeViewColumn(_("Activity"))
        self.description_column = gtk.TreeViewColumn(_("Description"))
        self.status_column = gtk.TreeViewColumn(_("Status"))


        self.icon_column.pack_start(self.icon, False)
        self._name_column.pack_start(self._name, True)
        self.description_column.pack_start(self.description, True)
        self.status_column.pack_start(self.status, False)

        self.icon_column.add_attribute(self.icon, 'icon_name', 0)
        self._name_column.add_attribute(self._name, "markup", 1)
        self.description_column.add_attribute(self.description, "markup", 2)
        self.status_column.add_attribute(self.status, "text", 3)

        self.current = 0

        self.append_column(self.icon_column)
        self.append_column(self._name_column)
        self.append_column(self.description_column)
        self.append_column(self.status_column)
        
        self.download_list = DownloadList()

        self._parent = parent
        self.thread = None
        self.words = ''
        self._list = utils.get_store_list()
        self.can_search = True
        self.stopped = False

        self.show_all()

    def up(self):
        self.current += 1

    def down(self):
        self.current -= 1

    def stop_search(self, *args):
        self.stopped = True

    def _add_activity(self, info):
        iter = self._model.insert(self.current, info)
        ITERS.append(iter)
        self.up()

    def clear(self):
        for child in self.get_children():
            self.remove(child)
            child = None

    def search(self, entry):
        #_logger.debug(threading.enumerate())
        if self.can_search:
            self.can_search = False
            self.w = entry.get_text().lower()
            self.clear()
            self.thread = threading.Thread(target=self._search)
            self.thread.start()
        else:
            self.stop_search()
            gobject.idle_add(self.search, entry)

    def _search(self):
        w = str(self.w)
        _id = -1
        for x in ITERS:
            self._model.remove(x)
        for activity in self._list:
            if self.stopped:
                break
            _id += 1
            name = activity[1].lower()
            description = activity[2].lower()
            if (w in name) or (w in description):
                activity_widget = _gen_activity(_id, self)
                self._add_activity(activity_widget)
        self.can_search = True


class DownloadList(gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)

        self._model = gtk.ListStore(str, str, int)
        self.set_model(self._model)

        renderer_text = gtk.CellRendererText()
        column_text = gtk.TreeViewColumn(_("Name"), renderer_text, text=0)
        self.append_column(column_text)

        renderer_text = gtk.CellRendererText()
        column_text = gtk.TreeViewColumn(_("State"), renderer_text, text=1)
        self.append_column(column_text)

        renderer_progress = gtk.CellRendererProgress()
        column_progress = gtk.TreeViewColumn(_("Progress"), renderer_progress,
            value=2)
        self.append_column(column_progress)

        self.show_all()

    def add_download(self, name):
        _iter = self._model.append([name, _("Starting download..."), 0])
        return _iter

    def set_download_progress(self, _id, progress):
        if progress <= 100:
            self._model[_id][2] = int(progress)

        if progress > 0:
            self._model[_id][1] = _("Downloading...")

        if progress >= 150:
            self._model[_id][1] = _("Installing...")
            self._model[_id][2] = 100

        if progress == 200:
            self._model[_id][1] = _("Installed!")

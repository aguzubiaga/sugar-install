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
import threading
import utils

from gettext import gettext as _

BTN_COLOR = gtk.gdk.color_parse("blue")

# Logging
_logger = utils.get_logger()


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


class List(gtk.Table):

    def __init__(self, parent):
        gtk.Table.__init__(self, rows=10, homogeneous=True)

        self._rows = 0
        self._list = utils.get_store_list()
        self.download_list = DownloadList()

        self._parent = parent

        self.thread = None
        self.words = ''

        self.show_all()

    def _add_activity(self, widget):
        self.attach(widget, 0, 1, self._rows, self._rows + 1)
        self.attach(gtk.HSeparator(), 0, 1, self._rows + 1, self._rows + 2)
        self.show_all()
        self._rows += 2

    def _clear(self):
        self._rows = 0
        for child in self.get_children():
            self.remove(child)
            child = None

    def search(self, entry):

        try:
            self.thread.cancel()
        except:
            pass
        

        self.words = entry.get_text().lower()
        self._clear()

        self.thread = threading.Timer(0, self._search)
        self.thread.start()

    def _search(self):
        w = self.words
        id = -1
        for activity in self._list:
            id += 1
            name = activity[1].lower()
            description = activity[2].lower()
            if (w in name) or (w in description):
                activity_widget = ActivityWidget(id, self)
                self._add_activity(activity_widget)


class ActivityWidget(gtk.HBox):

    def __init__(self, id, parent):
        gtk.HBox.__init__(self, False, 0)

        self._id = id
        self._download_list = parent.download_list
        self._downloads_icon = parent._parent.downloads_icon

        self.name_label = self._label()
        self.icon = gtk.Image()
        self.install_button = gtk.Button(_("INSTALL"))
        self.install_button.connect("clicked", self._btn_clicked)
        self.install_button.modify_bg(gtk.STATE_NORMAL, BTN_COLOR)
        self.install_button.modify_bg(gtk.STATE_PRELIGHT, BTN_COLOR)
        self.install_button.modify_bg(gtk.STATE_ACTIVE, BTN_COLOR)
        self.install_button.set_size_request(gtk.gdk.screen_width() / 10, -1)

        self._activity_props = parent._list[id]

        self._left_box = gtk.VBox()
        self._right_box = gtk.VBox()
        self._icon_and_label = gtk.HBox()

        self._icon_and_label.pack_start(self.icon, False, True, 0)
        self._icon_and_label.pack_end(self.name_label, True, True, 0)
        self._left_box.pack_start(self._icon_and_label, False, True, 0)
        self._left_box.pack_end(self.install_button, False, True, 0)

        self.desc_label = self._label()
        self.vers_label = self._label()
        self.suga_label = self._label()
        self.upda_label = self._label()
        self.down_label = self._label()
        self.home_label = self._label()
    
        self._right_box.pack_start(self.desc_label, False, True, 0)
        self._right_box.pack_start(self.vers_label, False, True, 0)
        self._right_box.pack_start(self.suga_label, False, True, 0)
        self._right_box.pack_start(self.upda_label, False, True, 0)
        self._right_box.pack_start(self.down_label, False, True, 0)
        self._right_box.pack_start(self.home_label, False, True, 0)

        self.pack_start(self._left_box, False, True, 0)
        self.pack_start(gtk.VSeparator(), False, True, 20)
        self.pack_start(self._right_box, False, True, 0)


        self._setup()

        self.show_all()

    def _label(self):
        label = gtk.Label()
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_line_wrap(True)
        label.set_use_markup(True)

        return label

    def _setup(self):
        self.name_label.set_markup(self._activity_props[1])

        self.desc_label.set_markup(self._activity_props[2])
        self.vers_label.set_markup('Version: ' + self._activity_props[3])
        self.suga_label.set_markup('Works with: ' + self._activity_props[4] + ' - ' + self._activity_props[5])
        self.upda_label.set_markup('Updated: ' + self._activity_props[6])
        self.down_label.set_markup('Downloads: ' + self._activity_props[7])
        self.home_label.set_markup('Homepage: ' + self._activity_props[8])

        try:
            pixbuf_icon = utils.get_icon(self._id)
            self.icon.set_from_pixbuf(pixbuf_icon)
        except:
            pass

    def _btn_clicked(self, widget):
        _logger.info("Install button clicked (%s)")
        self._downloads_icon.animate()

        threading.Thread(target=utils.download_activity, args=(self._id,
                                self._progress_changed)).start()

        self._download_id = self._download_list.add_download(self._activity_props[1])

    def _progress_changed(self, progress):
        self._download_list.set_download_progress(self._download_id, progress)


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
        iter = self._model.append([name, _("Starting download..."), 0])
        return iter

    def set_download_progress(self, id, progress):
        if progress <= 100:
            self._model[id][2] = int(progress)

        if progress > 0:
            self._model[id][1] = _("Downloading...")

        if progress >= 150:
            self._model[id][1] = _("Installing...")

        if progress == 200:
            self._model[id][1] = _("Installed!")

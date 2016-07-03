#!/usr/bin/python
# (C) 2014 Ricardo Cruz <ricardo.pdm.cruz@gmail.com>
# distributed under the GPLv3

import os, time
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, GObject, GdkPixbuf

CONFIG = os.path.expanduser('~/.timetracker')

## Backend

store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, int, int)

def time2str(time):
	mins = time%60
	if mins < 10:
		mins = "0" + str(mins)
	return "%d:%s" % (time/60, str(mins))

def save():
	f = open(CONFIG, 'w')
	it = store.get_iter_first()
	while it != None:
		task, time = store.get(it, 1, 5)
		f.write("%s\n%d\n" % (task, time))
		it = store.iter_next(it)
	f.close()

def load():
    if os.path.exists(CONFIG):
	    f = open(CONFIG, 'r')
	    while True:
		    task = f.readline().strip()
		    time = f.readline().strip()
		    if time == "":
			    break
		    time = int(time)
		    store.append([None, task, time2str(0), time2str(time), 0, time])
	    f.close()

def add(task):
	stop()
	store.append([None, task, time2str(0), time2str(0), 0, 0])

def remove(item):
	stop()
	it = store.get_iter(Gtk.TreePath(item))
	store.remove(it)

play_source = -1
play_item = -1
play_time = 0
session_time = 0
total_time = 0

def play(item):
	global play_item, play_source, play_time, session_time, total_time
	stop()
	play_item = item
	if play_item >= 0:
		it = store.get_iter(Gtk.TreePath(item))
		store.set(it, 0, win.play_pixbuf)
		session_time = store.get(it, 4)[0]
		total_time = store.get(it, 5)[0]-session_time
		play_time = time.time()
		play_source = GObject.timeout_add(1000, win.play_timeout_cb)

def stop():
	global play_item, play_source, play_time, session_time, total_time
	if play_item >= 0:
		it = store.get_iter(Gtk.TreePath(play_item))
		store.set(it, 0, None)
		GObject.source_remove(play_source)
		play_item = -1

def update():
	global play_item, play_source, play_time, session_time, total_time
	if play_item >= 0:
		it = store.get_iter(Gtk.TreePath(play_item))
		t = int((time.time() - play_time)/60)
		store.set(it, 2, time2str(t+session_time), 3, time2str(t+session_time+total_time),
			4, t+session_time, 5, t+session_time+total_time)

## UI

class MyWindow(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self)
		self.set_title("Vanilla Time Tracker")
		self.play_pixbuf = self.render_icon_pixbuf(Gtk.STOCK_MEDIA_PLAY, 1)
		icon = self.render_icon_pixbuf(Gtk.STOCK_MEDIA_PLAY, 4)
		self.set_icon(icon)
		self.set_default_size(500, 200)

		toolbar = Gtk.Toolbar()
		button = Gtk.ToolButton(Gtk.STOCK_ADD)
		button.set_tooltip_text("Add Task...")
		button.connect("clicked", self.new_clicked_cb)
		toolbar.insert(button, -1)
		self.delete_button = Gtk.ToolButton(Gtk.STOCK_REMOVE)
		self.delete_button.set_sensitive(False)
		self.delete_button.set_tooltip_text("Remove Task")
		self.delete_button.connect("clicked", self.delete_clicked_cb)
		toolbar.insert(self.delete_button, -1)
		toolbar.insert(Gtk.SeparatorToolItem(), -1)
		self.play_button = Gtk.ToolButton(Gtk.STOCK_MEDIA_PLAY)
		self.play_button.set_sensitive(False)
		self.play_button.set_tooltip_text("Start Task")
		self.play_button.connect("clicked", self.play_clicked_cb)
		toolbar.insert(self.play_button, -1)
		self.pause_button = Gtk.ToolButton(Gtk.STOCK_MEDIA_PAUSE)
		self.pause_button.set_sensitive(False)
		self.pause_button.set_tooltip_text("Pause Task")
		self.pause_button.connect("clicked", self.pause_clicked_cb)
		toolbar.insert(self.pause_button, -1)
		toolbar.insert(Gtk.SeparatorToolItem(), -1)
		button = Gtk.ToolButton(Gtk.STOCK_ABOUT)
		button.connect("clicked", self.about_clicked_cb)
		button.set_tooltip_text("About")
		toolbar.insert(button, -1)

		self.view = Gtk.TreeView()
		self.view.set_model(store)
		renderer = Gtk.CellRendererPixbuf()
		column = Gtk.TreeViewColumn("", renderer, pixbuf=0)
		column.set_sizing(1)
		column.set_fixed_width(24)
		self.view.append_column(column)
		renderer = Gtk.CellRendererText()
		renderer.set_property('editable', True)
		renderer.connect('edited', self.renderer_edited_cb)
		column = Gtk.TreeViewColumn("Task", renderer, text=1)
		column.set_expand(True)
		self.view.append_column(column)
		column = Gtk.TreeViewColumn("Session Time", Gtk.CellRendererText(), text=2)
		self.view.append_column(column)
		column = Gtk.TreeViewColumn("Total Time", Gtk.CellRendererText(), text=3)
		self.view.append_column(column)
		selection = self.view.get_selection()
		selection.connect_after("changed", self.selection_changed_cb)
		self.view.connect_after("row-activated", self.row_activated_cb)
#		self.view.connect("button-press-event", self.view_button_press_cb)

		vbox = Gtk.VBox(False, 6)
		vbox.pack_start(toolbar, False, True, 0)
		vbox.pack_start(self.view, True, True, 0)
		vbox.show_all()
		self.add(vbox)
		self.view.grab_focus()

	# view

	def selection_changed_cb(self, selection):
		selected = (selection.count_selected_rows() > 0)
		self.delete_button.set_sensitive(selected)
		if selected:
			self.sync_sensitive_buttons()
		else:
			self.play_button.set_sensitive(False)
			self.pause_button.set_sensitive(False)

	def row_activated_cb(self, view, path, column):
		if play_item == self.get_selected():
			stop()
		else:
			play(self.get_selected())
		self.sync_sensitive_buttons()

	def play_timeout_cb(self):
		update()
		return True

	def get_selected(self):
		selection = self.view.get_selection()
		store, it = selection.get_selected()
		return store.get_path(it).get_indices()[0]

	def renderer_edited_cb(self, renderer, path, text):
		it = store.get_iter(path)
		store.set(it, 1, text)

#	def view_button_press_cb(self, view, event):
#		print "pressed"
#		if event.button.type == Gtk.GDK_2BUTTON_PRESS:
#			if view.get_selection().count_selected_rows() == 0:
#				print "no selected"
#				self.new_clicked_cb(None)

	# toolbar

	def sync_sensitive_buttons(self):
		playing = (play_item == self.get_selected())
		self.play_button.set_sensitive(not playing)
		self.pause_button.set_sensitive(playing)

	def play_clicked_cb(self, button):
		play(self.get_selected())
		self.sync_sensitive_buttons()

	def pause_clicked_cb(self, button):
		stop()
		self.sync_sensitive_buttons()

	def new_clicked_cb(self, button):
		dialog = Gtk.Dialog()
		dialog.set_title('')
		dialog.set_transient_for(self)
		dialog.add_buttons(Gtk.STOCK_CANCEL, 0, Gtk.STOCK_ADD, 1)
		dialog.set_default_response(1)
		entry = Gtk.Entry()
		entry.set_activates_default(True)
		entry.show()
		dialog.get_content_area().add(entry)
		if dialog.run() == 1:
			add(entry.get_text())
		dialog.destroy()

	def delete_clicked_cb(self, button):
		remove(self.get_selected())

	def about_clicked_cb(self, button):
		dialog = Gtk.AboutDialog()
		dialog.set_program_name("Vanilla Time Tracker")
		dialog.set_authors(["Ricardo Cruz <ricardo.pdm.cruz@gmail.com>"])
		dialog.run()
		dialog.destroy()

## Main

load()

def delete_event_cb(widget, event):
	save()
	return Gtk.main_quit()

win = MyWindow()
win.connect("delete-event", delete_event_cb)
win.show()
Gtk.main()


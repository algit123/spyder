# -*- coding: utf-8 -*-
#
# Copyright © 2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Project Explorer Plugin"""

from PyQt4.QtGui import QFontDialog
from PyQt4.QtCore import SIGNAL

import sys, cPickle, os.path as osp

# For debugging purpose:
STDOUT = sys.stdout

# Local imports
from spyderlib.config import get_conf_path, get_icon
from spyderlib.utils.qthelpers import create_action
from spyderlib.widgets.projectexplorer import ProjectExplorerWidget
from spyderlib.plugins import SpyderPluginMixin


class ProjectExplorer(ProjectExplorerWidget, SpyderPluginMixin):
    """Python source code analysis based on pylint"""
    ID = 'project_explorer'
    DATAPATH = get_conf_path('.projects')
    def __init__(self, parent=None):
        include = self.get_option('include', '.')
        exclude = self.get_option('exclude', r'\.pyc$|\.pyo$|\.orig$|^\.')
        show_all = self.get_option('show_all', False)
        ProjectExplorerWidget.__init__(self, parent=parent, include=include,
                                       exclude=exclude, show_all=show_all,
                                       valid_types=['.py', '.pyw'],
                                       default_project_path=get_conf_path())
        SpyderPluginMixin.__init__(self, parent)

        self.editor_valid_types = None

        self.set_font(self.get_plugin_font())
        
        if osp.isfile(self.DATAPATH):
            self.load_config()

        self.connect(self, SIGNAL("open_file(QString)"), self.open_file)
        
    #------ SpyderPluginWidget API ---------------------------------------------    
    def get_plugin_title(self):
        """Return widget title"""
        return self.tr("Project explorer")
    
    def get_focus_widget(self):
        """
        Return the widget to give focus to when
        this plugin's dockwidget is raised on top-level
        """
        return self.treewidget
    
    def get_plugin_actions(self):
        """Return a list of actions related to plugin"""
        new_project_act = create_action(self, text=self.tr('New project...'),
                                        icon=get_icon('project_expanded.png'),
                                        triggered=self.create_new_project)

        font_action = create_action(self, self.tr("&Font..."),
                                    None, 'font.png', self.tr("Set font style"),
                                    triggered=self.change_font)
        self.treewidget.common_actions += (None, font_action)
        
        self.main.file_menu_actions.insert(1, new_project_act)
        
        return []
        
    def refresh_plugin(self):
        """Refresh project explorer widget"""
        pass
        
    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed"""
        self.save_config()
        self.closing_widget()
        return True
        
    #------ Public API ---------------------------------------------------------
    def create_new_project(self):
        """Create new project"""
        if self.dockwidget.isHidden():
            self.dockwidget.show()
        self.dockwidget.raise_()
        if not self.treewidget.new_project():
            # Notify dockwidget to schedule a repaint
            self.dockwidget.update()
        
    def change_font(self):
        """Change font"""
        font, valid = QFontDialog.getFont(self.get_plugin_font(), self,
                                          self.tr("Select a new font"))
        if valid:
            self.set_font(font)
            self.set_plugin_font(font)
            
    def set_font(self, font):
        """Set project explorer widget font"""
        self.treewidget.setFont(font)
        
    def save_config(self):
        """Save configuration: opened projects & tree widget state"""
        data = self.get_project_config()
        cPickle.dump(data, file(self.DATAPATH, 'w'))
        self.set_option('expanded_state', self.treewidget.get_expanded_state())
        self.set_option('scrollbar_position',
                        self.treewidget.get_scrollbar_position())
        
    def load_config(self):
        """Load configuration: opened projects & tree widget state"""
        data = cPickle.load(file(self.DATAPATH))
        self.set_project_config(data)
        expanded_state = self.get_option('expanded_state', None)
        if expanded_state is not None:
            self.treewidget.set_expanded_state(expanded_state)
        
    def restore_scrollbar_position(self):
        """Restoring scrollbar position after main window is visible"""
        scrollbar_pos = self.get_option('scrollbar_position', None)
        if scrollbar_pos is not None:
            self.treewidget.set_scrollbar_position(scrollbar_pos)
        
    def set_editor_valid_types(self, valid_types):
        self.editor_valid_types = valid_types
        self.treewidget.valid_types += valid_types

    def open_file(self, fname):
        """
        Open filename with the appropriate application
        Redirect to the right widget (txt -> editor, spydata -> workspace, ...)
        """
        fname = unicode(fname)
        ext = osp.splitext(fname)[1]
        if ext in self.editor_valid_types:
            self.emit(SIGNAL("edit(QString)"), fname)
        elif ext in ('.spydata', '.npy', '.mat'):
            self.emit(SIGNAL("import_data(QString)"), fname)
        else:
            self.treewidget.startfile(fname)

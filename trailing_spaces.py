'''
Provides both a trailing spaces highlighter and a deletion command.

Config summary (see README.md for details):

    # key binding
    { "keys": ["ctrl+shift+t"], "command": "delete_trailing_spaces" }

    # file settings
    {
      "trailing_spaces_highlight_color": "invalid",
      "trailing_spaces_file_max_size": 1000
    }

@author: Jean-Denis Vauguet <jd@vauguet.fr>, Oktay Acikalin <ok@ryotic.de>
@license: MIT (http://www.opensource.org/licenses/mit-license.php)
@since: 2011-02-25
'''

import sublime
import sublime_plugin
import fnmatch
import os.path

DEFAULT_MAX_FILE_SIZE = 1048576
DEFAULT_COLOR_SCOPE_NAME = "invalid"
DEFAULT_IS_ENABLED = True

#Set whether the plugin is on or off
ts_settings = sublime.load_settings('trailing_spaces.sublime-settings')
trailing_spaces_enabled = bool(ts_settings.get('trailing_spaces_enabled',
                                               DEFAULT_IS_ENABLED))

# Determine if the view is a find results view
def is_find_results(view):
    return view.settings().get('syntax') and "Find Results" in view.settings().get('syntax')

# Return an array of regions matching trailing spaces.
def find_trailing_spaces(view):
    include_empty_lines = bool(ts_settings.get('trailing_spaces_include_empty_lines',
                                               DEFAULT_IS_ENABLED))
    return view.find_all('[ \t]+$' if include_empty_lines else '(?<=\S)[\t ]+$')


# Highlight trailing spaces
def highlight_trailing_spaces(view):
    max_size = ts_settings.get('trailing_spaces_file_max_size',
                               DEFAULT_MAX_FILE_SIZE)
    color_scope_name = ts_settings.get('trailing_spaces_highlight_color',
                                       DEFAULT_COLOR_SCOPE_NAME)
    if view.size() <= max_size and not is_find_results(view):
        regions = find_trailing_spaces(view)
        view.add_regions('TrailingSpacesHighlightListener',
                         regions, color_scope_name,
                         sublime.DRAW_EMPTY)


# Clear all trailing spaces
def clear_trailing_spaces_highlight(window):
    for view in window.views():
        view.erase_regions('TrailingSpacesHighlightListener')

# Delete all trailing spaces
def delete_trailing_spaces(view, edit):
    regions = find_trailing_spaces(view)
    if regions:
        # deleting a region changes the other regions positions, so we
        # handle this maintaining an offset
        offset = 0
        for region in regions:
            r = sublime.Region(region.a + offset, region.b + offset)
            view.erase(edit, sublime.Region(r.a, r.b))
            offset -= r.size()
        msg_parts = {"nbRegions": len(regions),
                     "plural":    's' if len(regions) > 1 else ''}
        msg = "Deleted %(nbRegions)s trailing spaces region%(plural)s" % msg_parts
    else:
        msg = "No trailing spaces to delete!"
    sublime.status_message(msg)


# Toggle the event listner on or off
class ToggleTrailingSpacesCommand(sublime_plugin.WindowCommand):
    def run(self):
        global trailing_spaces_enabled
        trailing_spaces_enabled = False if trailing_spaces_enabled else True

        # If toggling on, go ahead and perform a pass,
        # else clear the highlighting in all views
        if trailing_spaces_enabled:
            highlight_trailing_spaces(self.window.active_view())
        else:
            clear_trailing_spaces_highlight(self.window)


# Highlight matching regions.
class TrailingSpacesHighlightListener(sublime_plugin.EventListener):
    def on_modified(self, view):
        if trailing_spaces_enabled:
            highlight_trailing_spaces(view)

    def on_activated(self, view):
        if trailing_spaces_enabled:
            highlight_trailing_spaces(view)

    def on_load(self, view):
        if trailing_spaces_enabled:
            highlight_trailing_spaces(view)

    def on_pre_save(self, view):
        for ignore_pattern in view.settings().get('trailing_spaces_ignore_list',[]):
            base_name = os.path.basename(view.file_name())
            if fnmatch.fnmatch(base_name, ignore_pattern):
                return

        if trailing_spaces_enabled and bool(view.settings().get('trailing_spaces_on_save')):
            try:
                edit = view.begin_edit()
                delete_trailing_spaces(view, edit)
            finally:
                view.end_edit(edit)


# Allows to erase matching regions.
class DeleteTrailingSpacesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        delete_trailing_spaces(self.view, edit)

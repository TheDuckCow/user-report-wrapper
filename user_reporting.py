# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import json
import os
import platform
import re
import textwrap
import traceback
import urllib

import bpy

# Be sure to change this to your own addon name, to not conflict with others!
IDNAME = "error_reporter_demo"

# Update the ID from the webform, e.g. from this url
# https://docs.google.com/forms/d/1Ejf3Vg6TcXAwOmYKY3Nqw78gQGL_LlNl-aZpkRxeA5U/
FORM_ID = "1FAIpQLSdHTA6aOJCbNsTCpRoWDWheWuQjci1d6gxnxHb1FdAnXvRHdw"

# Update these IDs to match the prefilled form
FORM_FIELDS = {
    "version":"391369946",
    "blender":"1215866813",
    "platform":"286196237",
    "error":"1023948975"
}

# Global reference for user reporting singleton
Reporter = None

# Globals for managing size of strings submitted
SHORT_FIELD_MAX = 64
ERROR_STRING_LENGTH = 512 # grab only the last N characters of error


class UserReporter(object):
    """Singleton object used to report user encountered errors"""

    def __init__(self, version, form_id):
        """Setup the reporter with inputs and system information"""

        bversion = None
        try: # for compatibility to prior blender versions (2.75?)
            bversion = bpy.app.version
        except Exception as err:
            print("Failed to get blender version", str(err))

        # get platform OS info in a stable way
        os_platform = None
        try:
            res = platform.system()+":"+platform.release()
            if len(res) > SHORT_FIELD_MAX:
                res = res[:SHORT_FIELD_MAX-1] + "|"
            os_platform = str(res)
        except Exception as err:
            print("Error getting platform info: " + str(err))
            os_platform = "unknown:unknown"

        # Public
        self.verbose = True
        self.dev = False

        # Private
        self._addon = __package__.lower()
        self._addon_version = version
        self._blender_version = str(bversion)
        self._platform = os_platform
        self._handling_error = False # used to avoid recursion
        self._form_id = form_id

    def wrapper(self, function, oper, context):
        """Operator execute function wrapper.

        Operator calls always wrapped within try except so that
        """
        try:
            self._handling_error = False
            res = function(oper, context)
            self._handling_error = False
        except:
            err = traceback.format_exc()
            print(err) # always print raw traceback
            err = self._format_report_error(err)

            # Prevent recusrive popups, only show the inner-most errors
            if self._handling_error is False:
                self._handling_error = True
                atr = URW_OT_popup_report_error.bl_idname.split(".")

                # Call the operator, passing in the error report structure
                getattr(getattr(bpy.ops, atr[0]),atr[1])(
                    'INVOKE_DEFAULT', error_report=err)
            return {'CANCELLED'}

        return res

    @staticmethod
    def _remove_path_prefix(report):
        """Remove filepath prefix from report logs and shorten data sent"""
        report = report.replace(r'\\', '/').replace(r'\\\\\\', '/')
        try:
            return re.sub(
                # case insensitive match: File "C:/path/.." or File "/path/.."
                r'(?i)File "([a-z]:){0,1}[/\\]{1,2}.*[/\\]{1,2}',
                'File "<addon_path>/',
                str(report))
        except Exception as err:
            print("Error occured while removing info: {}".format(err))
            return "[pii] "+str(report)

    def _format_report_error(self, err):
        """Constructs a structured error report object"""

        error = self._remove_path_prefix(err)

        # cut off the first three lines of error, which is this wrapper
        # TODO: use better grabbing via function traceback
        nth_newline = 0
        for ind in range(len(err)):
            if err[ind] in ["\n", "\r"]:
                nth_newline += 1
            if nth_newline == 3:
                if len(err) > ind+1:
                    err = err[ind+1:]
                break
        return error

    def get_prefilled_form_url(self, report):
        """Returns a link to a prefilled form, to submit report a in browser"""

        ids = FORM_FIELDS
        vals = {
            "version": urllib.parse.quote(self._addon_version),
            "blender": urllib.parse.quote(self._blender_version),
            "platform": urllib.parse.quote(self._platform),
            "error": urllib.parse.quote(report),
        }

        param_entries = ["entry.{id}={val}".format(id=ids[key], val=vals[key])
            for key in list(ids)]
        params = "&".join(param_entries)

        if "docs.google.com/forms/d/" in self._form_id:
            if "forms/d/e/" not in self._form_id:
                # TODO: Likely the "edit" url, make smarter by extracting id
                raise Exception("Cannot send report, form configuration issue")
            base_url = self._form_id.split("forms/d/e/")[-1]
            base_id = base_url.split("/")[0]
        else:
            base_id = self._form_id
        url = "https://docs.google.com/forms/d/e/{base_id}/viewform?{params}".format(
            base_id=base_id, params=params)
        return url


def wrapper(function):
    """Decorator for the execute(self, context) function of operators."""

    def subwrapper(oper, context):
        """Operator execute function wrapper"""
        if not Reporter:
            print("No reporter available")
            return function(oper, context)
        return Reporter.wrapper(function, oper, context)

    return subwrapper


# -----------------------------------------------------------------------------
# Blender operator for error reporting
# -----------------------------------------------------------------------------


class URW_OT_popup_report_error(bpy.types.Operator):
    """Encountered an error? Press OK to submit in a webbrowser"""
    bl_idname = IDNAME+".user_report_popup"
    bl_label = "Report error"

    error_report = bpy.props.StringProperty(default="")

    def invoke(self, context, event):
        width = 500 * ui_scale()
        return context.window_manager.invoke_props_dialog(self, width=width)

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        box = col.box()
        boxcol = box.column()
        boxcol.scale_y = 0.7
        if self.error_report=="":
            box.label(text=" # no error code identified # ")
        else:
            width = 500
            report_lines = self.error_report.split("\n")[:-1]
            tot_ln = 0
            max_ln = 10
            for ln in report_lines:
                sub_lns = textwrap.fill(ln, width-30)
                spl = sub_lns.split("\n")
                for i,s in enumerate(spl):
                    boxcol.label(text=s)
                    tot_ln+=1
                    if tot_ln==max_ln: break
                if tot_ln==max_ln: break

        row = col.row(align=True)
        split = layout_split(layout, factor=0.6)
        spcol = split.row()
        spcol.label(text="Press OK to open and submit report in a browser")

    def execute(self, context):
        url = Reporter.get_prefilled_form_url(self.error_report)
        bpy.ops.wm.url_open(url=url)
        self.report({"INFO"},"Thanks for sharing the report")
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# General purpose utilities
# (recommended to abstract into a util file if one exists)
# -----------------------------------------------------------------------------


def get_preferences(context=None):
    """Function to easily get general user prefs in 2.7 and 2.8 friendly way"""
    if hasattr(context, "user_preferences"):
        return context.user_preferences
    elif hasattr(context, "preferences"):
        return context.preferences
    return None


def make_annotations(cls):
    """Add annotations to class fields to avoid Blender 2.8 warnings"""
    if not hasattr(bpy.app, "version") or bpy.app.version < (2, 80):
        return cls
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


def ui_scale():
    """Returns scale of UI, for width drawing. Compatible down to 2.72"""
    prefs = get_preferences()
    if not hasattr(prefs, "view"):
        return 1
    elif hasattr(prefs.view, "ui_scale") and hasattr(prefs.view, "pixel_size"):
        return prefs.view.ui_scale * prefs.system.pixel_size
    elif hasattr(prefs.system, "dpi"):
        return prefs.system.dpi/72
    else:
        return 1


def layout_split(layout, factor=0.0, align=False):
    """Intermediate method for pre and post blender 2.8 split UI function"""
    if bpy.app.version >= (2, 80):
        return layout.split(factor=factor, align=align)
    return layout.split(percentage=factor, align=align)


# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------


classes = (
    URW_OT_popup_report_error,
    )


def register(bl_info):
    """Setup the user logging singleton."""
    global Reporter

    try:
        Reporter = UserReporter(
            version=str(bl_info["version"]),
            form_id=FORM_ID
            )
    except Exception as err:
        print("Error setting up the user reporter: ")
        print(err)
        return

    for cls in classes:
        make_annotations(cls)
        bpy.utils.register_class(cls)


def unregister():
    """Unregister any operators"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

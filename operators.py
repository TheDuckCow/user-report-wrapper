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


import bpy

from . import user_reporting


class URW_OT_no_error(bpy.types.Operator):
    """An operator which has no errors"""
    bl_idname = "object.userreport_no_error"
    bl_label = "Demo No Error"
    bl_options = {'REGISTER', 'UNDO'}

    @user_reporting.wrapper
    def execute(self, context):
        print("Running fine here!")
        self.report({"INFO"}, "No issues here!")
        return {'FINISHED'}


class URW_OT_has_error(bpy.types.Operator):
    """An operator with an error"""
    bl_idname = "object.userreport_has_error"
    bl_label = "Demo With Error"
    bl_options = {'REGISTER', 'UNDO'}

    @user_reporting.wrapper
    def execute(self, context):
        self.report({"WARNING"}, "Oh no, an issue is about to occur!")
        raise Exception("This is a fake error!")
        return {'FINISHED'}


def menu_append(self, context):
    """Append operators to a draw function"""
    self.layout.separator()
    col = self.layout.column()
    col.operator("object.userreport_no_error")
    col.operator("object.userreport_has_error")
    ops = col.operator("error_reporter_demo.user_report_popup")
    ops.error_report = "" # will force user to fill out in form


classes = (
    URW_OT_no_error,
    URW_OT_has_error,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # append draw function to the Info Bar > Help dropdown
    bpy.types.TOPBAR_MT_help.append(menu_append)


def unregister():
    """Unregister the UI and operators"""
    bpy.types.TOPBAR_MT_help.remove(menu_append)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

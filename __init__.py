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

# <pep8-80 compliant>

bl_info = {
    "name": "Stanford PLY format for createcloth",
    "author": "Richard Fechner",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "File > Import/Export",
    "description": "Import-Export PLY mesh data for createcloth",
    #"doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/mesh_ply.html",
    #"support": 'OFFICIAL',
    "category": "Import-Export",
}

#if "bpy" in locals():
#    import importlib
#    if "export_ply" in locals():
#        importlib.reload(export_ply)
#    if "import_ply" in locals():
#        importlib.reload(import_ply)


import bpy
from bpy.props import (
    CollectionProperty,
    StringProperty,
    BoolProperty,
    FloatProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    axis_conversion,
    orientation_helper,
)
import logging
from . import plycontainer_to_blender
logger = logging.getLogger( __name__ )

class MyImportPLY(bpy.types.Operator, ImportHelper):
    """Load a PLY geometry file"""
    bl_idname = "import_mesh.ply_with_border"
    bl_label = "myImport PLY with border"
    bl_options = {'UNDO'}

    files: CollectionProperty(
        name="File Path",
        description="File path used for importing the PLY file",
        type=bpy.types.OperatorFileListElement,
    )

    ## Hide opertator properties, rest of this is managed in C. See WM_operator_properties_filesel().
    #hide_props_region: BoolProperty(
    #    name="Hide Operator Properties",
    #    description="Collapse the region displaying the operator settings",
    #    default=True,
    #)

    directory: StringProperty()

    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    def execute(self, context):
        import os
        #from . import import_ply
        from . import plycontainer_to_blender as import_ply

        context.window.cursor_set('WAIT')

        paths = [ os.path.join(self.directory, name.name) \
                                    for name in self.files ]
        import time

        for path in paths:
            t = time.time()
            import_ply.load_ply( path, context.collection, context.view_layer )
            logger.info("\nSuccessfully imported %r in %.3f sec" \
                                            % (path, time.time() - t))

        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}


@orientation_helper(axis_forward='Y', axis_up='Z')
class MyExportPLY(bpy.types.Operator, ExportHelper):
    bl_idname = "export_mesh.ply_with_border"
    bl_label = "myExport PLY"
    bl_description = "Export as a Stanford PLY"

    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    use_ascii: BoolProperty(
        name="ASCII",
        description="Export using ASCII file format, otherwise use binary",
        default=True,
    )
    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=True,
    )
    #use_mesh_modifiers: BoolProperty(
    #    name="Apply Modifiers",
    #    description="Apply Modifiers to the exported mesh",
    #    default=True,
    #)
    global_scale: FloatProperty(
        name="Scale",
        min=0.01,
        max=1000.0,
        default=1.0,
    )

    def execute(self, context):
        from mathutils import Matrix
        #from . import export_ply
        from . import blender_to_plycontainer as export_ply

        context.window.cursor_set('WAIT')

        needkeywords = ( "filepath", "use_ascii", "use_mesh_modifiers" )
                        #"use_normals", "use_uv_coords", "use_colors" )
        keywords = { a:b for a, b in self.as_keywords().items() \
                        if a in needkeywords }
        global_matrix = axis_conversion(
            to_forward=self.axis_forward,
            to_up=self.axis_up,
        ).to_4x4() @ Matrix.Scale(self.global_scale, 4)
        keywords["global_matrix"] = global_matrix

        if self.use_selection:
            keywords["objects"] = context.selected_objects
        else:
            keywords["objects"] = context.scene.objects

        import time
        t = time.time()
        export_ply.save( **keywords )
        logger.info("\nSuccessfully exported %r in %.3f sec" \
                                % (keywords["filepath"], time.time() - t))

        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(heading="Format")
        col.prop(operator, "use_ascii")



class PLY_PT_export_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "myTransform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_ply"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")
        layout.prop(operator, "global_scale")



def menu_func_import(self, context):
    self.layout.operator(MyImportPLY.bl_idname, text="Brubru Stanford with border(.ply)")


def menu_func_export(self, context):
    self.layout.operator(MyExportPLY.bl_idname, text="Brubru Stanford with border(.ply)")


classes = (
    MyImportPLY,
    MyExportPLY,
    PLY_PT_export_transform,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

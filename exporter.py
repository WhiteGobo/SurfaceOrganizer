import bpy.utils
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
    directory: StringProperty()
    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})
    def execute(self, context):
        import os
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
    filename_ext = ".ply" #needed for Blender ExportHelper

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

        keywords["object"] = list(context.selected_objects)[0]

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

    @classmethod
    def poll( self, context ):
        return len( context.selected_objects ) == 1
        conditions = ( \
                #context.space_data is not None, \
                len( context.selected_objects ) == 1, \
                )
        return all( conditions )


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

_classes = ( \
        MyImportPLY,
        MyExportPLY,
        )
def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
def unregister():
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except (ValueError, RuntimeError) as err:
            logger.debug( err )
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

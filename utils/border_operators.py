import bpy.types
import logging
from . import border_functions as bof
logger = logging.getLogger( __name__ )

class _add_new_border:
    bl_options = {'UNDO'}
    def execute( self, context ):
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index
        partsurf_info = allinfo.partial_surface_info[ index ]

        #newname = self.create_border_name( partsurf_info )
        #vgroup = targetobject.vertex_groups.new( name = newname )
        #self.set_border_name( partsurf_info, vgroup.name )
        #_add_vertices_to_vertexgroup( vgroup, targetobject )

        selverts = bof.get_thread_from_selected_edges( targetobject )
        #partsurf_info["up_border_indexlist"] = selverts
        partsurf_info[ self.vertices_index_border_name ] = selverts

        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        if context.active_object is None:
            return False
        is_in_edgeselectmode = lambda scene: ( False, True, False ) \
                                == tuple(scene.tool_settings.mesh_select_mode)
        if not is_in_edgeselectmode( context.scene ):
            return False
        targetobject = context.active_object
        if not bof.selected_edges_is_threadlike( targetobject ):
            return False
        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index
        if index < 0:
            return False
        partsurf_info = allinfo.partial_surface_info[ index ]
        return cls.get_border_name( partsurf_info ) == ""

class add_new_border_right( _add_new_border,bpy.types.Operator ):
    bl_idname = "mesh.add_border_right"
    bl_label = "Add border right"
    vertices_index_border_name = "right_border_indexlist"
    @classmethod
    def get_border_name( cls, partsurf_info ):
        return partsurf_info.right_border
    def set_border_name( self, partsurf_info, name ):
        partsurf_info.right_border = name
    def create_border_name( self, partsurf_info ):
        return "right_" + partsurf_info.name
class add_new_border_up( _add_new_border,bpy.types.Operator ):
    bl_idname = "mesh.add_border_up"
    bl_label = "Add border up"
    vertices_index_border_name = "up_border_indexlist"
    @classmethod
    def get_border_name( cls, partsurf_info ):
        return partsurf_info.up_border
    def set_border_name( self, partsurf_info, name ):
        partsurf_info.up_border = name
    def create_border_name( self, partsurf_info ):
        return "up_" + partsurf_info.name
class add_new_border_left( _add_new_border,bpy.types.Operator ):
    bl_idname = "mesh.add_border_left"
    bl_label = "Add border left"
    vertices_index_border_name = "left_border_indexlist"
    @classmethod
    def get_border_name( cls, partsurf_info ):
        return partsurf_info.left_border
    def set_border_name( self, partsurf_info, name ):
        partsurf_info.left_border = name
    def create_border_name( self, partsurf_info ):
        return "left_" + partsurf_info.name
class add_new_border_down( _add_new_border,bpy.types.Operator ):
    bl_idname = "mesh.add_border_down"
    bl_label = "Add border down"
    vertices_index_border_name = "down_border_indexlist"
    @classmethod
    def get_border_name( cls, partsurf_info ):
        return partsurf_info.down_border
    def set_border_name( self, partsurf_info, name ):
        partsurf_info.down_border = name
    def create_border_name( self, partsurf_info ):
        return "down_" + partsurf_info.name

class asdf( bpy.types.Operator ):
    bl_idname = "mesh.asdf"
    bl_label = "Add borderthingies"
    bl_options = {'UNDO'}
    def execute( self, context ):
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        targetobject = context.active_object
        if targetobject == None:
            return False
        allinfo = targetobject.partial_surface_information
        partsurf_info = allinfo.partial_surface_info[ index ]
        first, second = cls.get_cornerindices( partsurf_info )
        lenvertices = len( allinfo.partial_surface_info )
        if not all( first < 0, first > lenvertices,
                    second < 0, second > lenvertices):
            return False
        return True

def _add_vertices_to_vertexgroup( vgroup, targetobject ):
    #vertices should already be selected so no need to act here
    #select_vertices( targetobject, vertices )
    targetobject.vertex_groups.active_index = vgroup.index
    override = { "active_object": targetobject }
    bpy.ops.object.vertex_group_assign( override )


_classes = (\
        add_new_border_right, \
        add_new_border_up, \
        add_new_border_left, \
        add_new_border_down, \
        )
def register():
    for cls in _classes:
        bpy.utils.register_class( cls )

def unregister():
    for cls in reversed( _classes ):
        try:
            bpy.utils.unregister_class( cls )
        except (ValueError, RuntimeError) as err:
            logger.debug( err )

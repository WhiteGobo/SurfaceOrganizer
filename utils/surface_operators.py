import bpy.types
from . import surface_functions
import logging
logger= logging.getLogger( __name__ )

#find_possible_partialsurfaces_to_border( targetobject, partialsurfaceinfo )

class NewPartialSurface( bpy.types.Operator ):
    bl_idname = "mesh.autocomplete_bordered_partialsurface"
    bl_label = "Autocomplete partialsurface"
    bl_options = {'UNDO'}
    def execute( self, context ):
        context.window.cursor_set('WAIT')
        self.report( {'INFO'}, "This is a test" )
        targetobject = context.active_object
        #this is a hotfix for 'object.mode_set'
        context.view_layer.objects.active = targetobject

        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index 
        partsurf_info = allinfo.partial_surface_info[ index ]
        innersurfs = surface_functions.find_possible_partialsurfaces_to_border(\
                                                targetobject, partsurf_info )
        innersurfs = list( innersurfs )
        _onetime = True
        for surf in innersurfs:
            partsurf_name = "vertices_" + partsurf_info.name + "_auto"
            vgroup = targetobject.vertex_groups.new( name = partsurf_name )
            #_select_vertices( targetobject, surf )
            _add_vertices_to_vertexgroup( vgroup, targetobject, surf )
            if _onetime:
                _onetime = False
                partsurf_info.vertexgroup = vgroup.name
        context.window.cursor_set('DEFAULT')
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        for op in (bpy.ops.object.mode_set,):
            if not op.poll(): #context doesnt need to be given
                return False
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index 
        if index<0:
            return False
        partsurf_info = allinfo.partial_surface_info[ index ]
        corners = ( partsurf_info.rightup_corner, partsurf_info.leftup_corner, \
                partsurf_info.leftdown_corner, partsurf_info.rightdown_corner )
        for i in corners:
            if i < 0:
                logger.debug( f"{cls.bl_idname}.poll() failed because "\
                                +"needed all cornerpoints must be defined" )
                return False
        borders = ( partsurf_info.up_border, partsurf_info.left_border, \
                    partsurf_info.down_border, partsurf_info.right_border )
        for name in borders:
            if name == "":
                logger.debug( f"{cls.bl_idname}.poll() failed because "\
                                +"needed all border must be defined" )
                return False
        return True

def _select_vertices( targetobject, indexlist ):
    override = { "active_object": targetobject }
    mode = targetobject.mode
    bpy.ops.object.mode_set( override, mode='OBJECT' )
    for i, v in enumerate( targetobject.data.vertices ):
        v.select = (i in indexlist)
    bpy.ops.object.mode_set( override, mode=mode )

def _add_vertices_to_vertexgroup( vertexgroup, targetobject, vertice_indices ):
    mode = targetobject.mode
    bpy.ops.object.mode_set( mode='OBJECT' )
    assert targetobject.mode == 'OBJECT', "couldnt set objectmode, " \
                    "maybe c...active_object != c...view_layer.objects.active"
    weight, add_type = 1, "REPLACE"
    #vertexgroup = obj.vertex_groups.new( name=vertexgroupname )
    for i in vertice_indices:
        vertexgroup.add( [i], weight, add_type )
    #throws error if 0 in sequence as first place
    #vertexgroup.add( set(vertice_indices), weight, add_type )
    bpy.ops.object.mode_set( mode=mode )


_classes = ( \
        NewPartialSurface,
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

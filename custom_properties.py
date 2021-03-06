import bpy
import logging
from .exceptions import RegisterError, SurfaceNoActive
logger = logging.getLogger( __name__ )

def get_all_partialsurfaceinfo( targetobject ):
    from .surfacedivide import RIGHTUP_CORNER, LEFTUP_CORNER, \
                                LEFTDOWN_CORNER, RIGHTDOWN_CORNER
    for info in targetobject.partial_surface_information.partial_surface_info:

        output = { "Name": info.name, \
                RIGHTUP_CORNER: info.rightup_corner, \
                LEFTUP_CORNER: info.leftup_corner, \
                LEFTDOWN_CORNER: info.leftdown_corner, \
                RIGHTDOWN_CORNER: info.rightdown_corner, \
                }
        if info.vertexgroup != "":
            vertgroup = _get_vertices_of_vertexgroup( targetobject, \
                                                            info.vertexgroup )
            output["Vertexgroup"] = tuple(vertgroup)
        yield output


def get_corners( targetobject, surfacename=None ):
    """
    :raise: 'SurfaceNoActive'
    """
    if surfacename == None:
        index = allinfo.active_surface_index
        if index < 0:
            raise SurfaceNoActive( "no active partialsurface" )
    else:
        index = get_partialsurface_index( targetobject, surfacename )

    allinfo = targetobject.partial_surface_information
    surfaceinfo = allinfo.partial_surface_info[ index ]
    return (\
            surfaceinfo.rightup_corner, \
            surfaceinfo.leftup_corner, \
            surfaceinfo.leftdown_corner, \
            surfaceinfo.rightdown_corner, \
            )


def get_partialsurface_index( targetobject, surfacename ):
    """
    :raise: 'KeyError' if no surface with name 'surfacename'
    """
    for surf in allinfo.partial_surface_info:
        if surf.name == surfacename:
            return surf.index
    raise KeyError( f"No available surface with name {surfacename}" )


def test_get( self ):
    parentobject = self.id_data
    try:
        active_surface = parentobject.data[ "_subrectanglesurfaces" ][0]
    except (KeyError, IndexError):
        active_surface = ""
    return active_surface
    #return self.get( "active_surface", "" )
def test_write( self, value ):
    parentobject = self.id_data
    try:
        surfaces_list = parentobject.data[ "_subrectanglesurfaces" ]
    except KeyError:
        surfaces_list = list()
        parentobject.data[ "_subrectanglesurfaces" ] = surfaces_list
    try:
        surfaces_list.remove( value )
    except ValueError:
        pass
    surfaces_list.insert( 0, value )
    parentobject.data[ "_subrectanglesurfaces" ] = surfaces_list
    #self["active_surface"] = value

class ListItem( bpy.types.PropertyGroup ):
    """Group of properties representing an item in the list.
    """ 
    name: bpy.props.StringProperty( 
            name="Name", 
            description="A name for this item", 
            default="Untitled",
            #set=_customset,
            #get=_customget,
            ) 
    rightup_corner: bpy.props.IntProperty(
            name="rightup corner",
            default=-1 )
    leftup_corner: bpy.props.IntProperty(
            name="leftup corner",
            default=-1 )
    leftdown_corner: bpy.props.IntProperty(
            name="leftdown corner",
            default=-1 )
    rightdown_corner: bpy.props.IntProperty(
            name="rightdown corner",
            default=-1 )
    #up_border: bpy.props.StringProperty( name = "upborder Vertexgroup",
    #        description = "vertices assigned to upborder", default="" )
    #left_border: bpy.props.StringProperty( name = "leftborder Vertexgroup",
    #        description = "vertices assigned to leftborder", default="" )
    #down_border: bpy.props.StringProperty( name = "downborder Vertexgroup",
    #        description = "vertices assigned to downborder", default="" )
    #right_border: bpy.props.StringProperty( name = "rightborder Vertexgroup",
    #        description = "vertices assigned to rightborder", default="" )
    # Use private_data ['up_border_indexlist'] = [0,1,2] instead
    #up_border_indexlist: bpy.props.CollectionProperty( type=EdgeItem )
    #left_border_indexlist: bpy.props.CollectionProperty( type=EdgeItem )
    #right_border_indexlist: bpy.props.CollectionProperty( type=EdgeItem )
    #down_border_indexlist: bpy.props.CollectionProperty( type=EdgeItem )
    vertexgroup: bpy.props.StringProperty(
            name = "VertexGroup",
            description = "Vertex Group to partialsurface",
            default = "",
            )
    #included_vertices: bpy.props.CollectionProperty(type=bpy.types.IntProperty)

def _get_vertices_of_vertexgroup( object, groupname ):
    groupindex = object.vertex_groups[ groupname ].index
    for v in object.data.vertices:
        for g in v.groups:
            if g.group == groupindex:
                yield int( v.index )

class partialsurface_list( bpy.types.PropertyGroup ):
    active_surface_index: bpy.props.IntProperty( name = "surface index", \
                                                            default=-1 )
    partial_surface_info: bpy.props.CollectionProperty( type=ListItem )

_classes = ( \
        #EdgeItem, \
        ListItem, \
        partialsurface_list, \
        )

def register():
    for cls in _classes:
        try:
            bpy.utils.register_class( cls )
        except Exception as err:
            raise RegisterError( cls ) from err
    bpy.types.Object.partial_surface_information = \
                        bpy.props.PointerProperty( type=partialsurface_list )

def unregister():
    try:
        del( bpy.types.Object.partial_surface_information )
    except AttributeError:
        pass
    for cls in reversed( _classes ):
        try: # for testing purposes
            bpy.utils.unregister_class( cls )
        except (ValueError, RuntimeError) as err:
            logger.debug( err )

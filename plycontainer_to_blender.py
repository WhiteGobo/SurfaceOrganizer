#import bpy
import itertools
#from .plyhandler import ObjectSpec as PlyObject
import logging
from .exceptions import InvalidPlyDataForSurfaceobject
logger = logging.getLogger( __name__ )

# for documentation
from typings import Iterator
type_vertex = tuple[float,float,float]
type_faces = Iterator[int]
type_surfaceindices = tuple[ int,int,int,int ]
type_surfacenames = str
#

def load_ply( filepath, collection, view_layer ):
    """
    :param collection: context.collection from blenderoperator
    :param view_layer: context.view_layer from blenderoperator
    """
    import bpy
    #filename = "/home/hfechner/tmp.ply"
    #filename = "/home/hfechner/meshfortests.ply"
    ply_name = bpy.path.display_name_from_filepath( filepath )
    meshname = ply_name
    objectname = ply_name

    #vertexlist, faces, rightup, leftup, leftdown, rightdown \
    vertexlist, faces, borders, bordernames = load_meshdata_from_ply( filepath )

    generate_blender_object( meshname, objectname, vertexlist, faces, \
                                        borders, bordernames, \
                                        #rightup, leftup, leftdown, rightdown, \
                                        collection, view_layer )
    return {'FINISHED'}


def load_meshdata_from_ply( filepath:str ) -> tuple[ Iterator[type_vertex], \
                            Iterator[type_faces],Iterator[type_surfaceindices],\
                            Iterator[type_surfacenames]]:
    asdf = plysurfacehandler.plysurfacehandler.load_from_file( filepath )
    vertexpositions = asdf.get_vertexpositions()
    faceindices = asdf.get_faceindices()
    number_surfaces = asdf.get_numbersurfaces()
    get_corn = lambda x: tuple(( x.rightup, x.leftup, x.leftdown, x.rightdown ))
    surfaceindices = [ get_corn( asdf.get_surface(i) )\
                        for i in range( number_surfaces ) ]
    surfacenames = [ asdf.get_surface(i).surfacename \
                        for i in range( number_surfaces ) ]
    surface_vertexmask = [ asdf.get_surface(i).vertexlist \
                        for i in range( number_surfaces ) ]
    return vertexpositions, faceindices, surfaceindices, surfacenames


def extract_vertex_positions( blender_obj_info ):
    vertexpositions = blender_obj_info.vertex 
    vertexnumber = len( blender_obj_info.vertex )
    return vertexpositions, vertexnumber


def generate_blender_object( meshname, objectname, vertices_list, faces, \
                                        borders, bordernames, \
                                        #rightup, leftup, leftdown, rightdown, \
                                        collection, view_layer ):
    """
    :todo: setting view_layer.objects.active seems to have strange interactions
            with other parts of the program
    """
    import bpy
    mymesh = generate_mesh( vertices_list, faces, meshname )

    obj = bpy.data.objects.new( objectname, mymesh )

    collection.objects.link( obj )
    #The next line seems to interact strangely with context.active_object
    #i had problems using ops.mode_set if context.active_object differs from
    #context.view_layer.objects.active
    view_layer.objects.active = obj 
    from . import surfacedivide as surfdiv
    for border, bordername in itertools.zip_longest(borders, bordernames):
        surfdiv.add_new_partial_surface( obj, bordername )
        rightup, leftup, leftdown, rightdown = border
        surfdiv.assign_rightup_cornerpoint( obj, obj.data.vertices[rightup] )
        surfdiv.assign_leftup_cornerpoint( obj, obj.data.vertices[leftup])
        surfdiv.assign_leftdown_cornerpoint( obj, obj.data.vertices[leftdown])
        surfdiv.assign_rightdown_cornerpoint( obj, obj.data.vertices[rightdown])

    obj.select_set(True)
    return obj, mymesh


def generate_mesh( vertices_list, faces, meshname ):
    import bpy
    mesh = bpy.data.meshes.new( name=meshname )
    edgelist = [] # if faces are given no edges need to be provided
    mesh.from_pydata( vertices_list, edgelist, faces )
    #mesh.update()
    mesh.validate()

    return mesh


def create_vertexgroup_with_vertice( obj, vertexgroupname, vertice ):
    weight, add_type = 1, "REPLACE"
    obj.vertex_groups.new( name=vertexgroupname )
    obj.vertex_groups[ vertexgroupname ].add( [vertice], weight, add_type )


def _help_select_single_vertice( override, index ):
    obj = override["active_object"]
    mode = obj.mode
    bpy.ops.object.mode_set( override, mode='OBJECT' )
    for i, v in enumerate( obj.data.vertices ):
        v.select = (i==index)
    bpy.ops.object.mode_set( override, mode=mode )

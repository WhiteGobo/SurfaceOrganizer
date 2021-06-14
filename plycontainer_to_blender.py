import bpy
#import bpy.data
import itertools
import logging
from .exceptions import InvalidPlyDataForSurfaceobject
logger = logging.getLogger( __name__ )
from . import plysurfacehandler

# for documentation
from typing import Iterator
type_vertex = tuple[float,float,float]
type_faces = Iterator[int]
type_surfacedata = dict
#

def load_ply( filepath, collection, view_layer ):
    """
    :param collection: context.collection from blenderoperator
    :param view_layer: context.view_layer from blenderoperator
    """
    ply_name = bpy.path.display_name_from_filepath( filepath )
    meshname = ply_name
    objectname = ply_name

    vertexlist, faces, surfaceinfo_all = load_meshdata_from_ply( filepath )

    generate_blender_object( meshname, objectname, list( vertexlist), \
                                        list(faces), \
                                        surfaceinfo_all, \
                                        collection, view_layer )
    return {'FINISHED'}


def load_meshdata_from_ply( filepath:str ) -> tuple[ Iterator[type_vertex], \
                            Iterator[type_faces],\
                            Iterator[type_surfacedata]]:
    asdf = plysurfacehandler.plysurfacehandler.load_from_file( filepath )
    vertexpositions = asdf.get_vertexpositions()
    faceindices = asdf.get_faceindices()
    number_surfaces = asdf.get_number_surfaces()
    get_corn = lambda x: tuple(( x.rightup, x.leftup, x.leftdown, x.rightdown ))
    surfaceinfo = []
    for i in range( number_surfaces ):
        surf = asdf.get_surface(i)
        tmpinfo = {\
                "rightup": surf.rightup, \
                "leftup": surf.leftup, \
                "leftdown": surf.leftdown, \
                "rightdown": surf.rightdown, \
                "name": surf.surfacename, \
                "vertexmask": surf.vertexlist, \
                }
        surfaceinfo.append({ a:b for a,b in tmpinfo.items() if b is not None })

    return vertexpositions, faceindices, surfaceinfo


def extract_vertex_positions( blender_obj_info ):
    vertexpositions = blender_obj_info.vertex 
    vertexnumber = len( blender_obj_info.vertex )
    return vertexpositions, vertexnumber


def generate_blender_object( meshname, objectname, vertices_list, faces, \
                                        surfaceinfos, \
                                        collection, view_layer ):
    """
    :todo: setting view_layer.objects.active seems to have strange interactions
            with other parts of the program
    """
    mymesh = generate_mesh( vertices_list, faces, meshname )

    obj = bpy.data.objects.new( objectname, mymesh )

    collection.objects.link( obj )
    #The next line seems to interact strangely with context.active_object
    #i had problems using ops.mode_set if context.active_object differs from
    #context.view_layer.objects.active
    view_layer.objects.active = obj 
    from . import surfacedivide as surfdiv
    for surfaceinfo in surfaceinfos:
        rightup = surfaceinfo["rightup"]
        leftup = surfaceinfo["leftup"]
        leftdown = surfaceinfo["leftdown"]
        rightdown = surfaceinfo["rightdown"]
        bordername = surfaceinfo.get( "name", None )
        vertexmask = surfaceinfo.get( "vertexmask", None )
        surfdiv.add_new_partial_surface( obj, bordername )
        surfdiv.assign_rightup_cornerpoint( obj, obj.data.vertices[rightup] )
        surfdiv.assign_leftup_cornerpoint( obj, obj.data.vertices[leftup])
        surfdiv.assign_leftdown_cornerpoint( obj, obj.data.vertices[leftdown])
        surfdiv.assign_rightdown_cornerpoint( obj, obj.data.vertices[rightdown])

    obj.select_set(True)
    return obj, mymesh


def generate_mesh( vertices_list, faces, meshname ):
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

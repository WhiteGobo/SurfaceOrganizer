import bpy

import itertools
from .plyhandler import ObjectSpec as PlyObject
import logging
logger = logging.getLogger( __name__ )


def load_ply( filepath, collection, view_layer ):
    """
    :param collection: context.collection from blenderoperator
    :param view_layer: context.view_layer from blenderoperator
    """
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

class InvalidPlyDataForSurfaceobject( Exception ):
    pass

def load_meshdata_from_ply( filepath ):
    """
    :todo: use f cr is shitty
    """
    plyobj = PlyObject.load_from_file( filepath )
    try:
        vertexpositions = plyobj.get_filtered_data("vertex", ("x", "y", "z") )
        faceindices = plyobj.get_filtered_data( "face", ("vertex_indices",) )
        faceindices = [ f[0] for f in faceindices ]
        border = plyobj.get_filtered_data( "cornerrectangle",\
                                            ("rightup", "leftup", \
                                            "leftdown", "rightdown") )
    except KeyError as err:
        raise InvalidPlyDataForSurfaceobject( "couldnt find all needed "\
                        "elements and associated properties that are needed" )\
                        from err

    bordernames = (None,)
    try:
        bordernames = plyobj.get_filtered_data("cornerrectangle", ("surfacename",))
        bordernames = [ "".join(chr(i) for i in name[0]) \
                        for name in bordernames ]
    except KeyError:
        pass
    return vertexpositions, faceindices, border, bordernames


def extract_vertex_positions( blender_obj_info ):
    vertexpositions = blender_obj_info.vertex 
    vertexnumber = len( blender_obj_info.vertex )
    return vertexpositions, vertexnumber


def generate_blender_object( meshname, objectname, vertices_list, faces, \
                                        borders, bordernames, \
                                        #rightup, leftup, leftdown, rightdown, \
                                        collection, view_layer ):
    mymesh = generate_mesh( vertices_list, faces, meshname )

    obj = bpy.data.objects.new( objectname, mymesh )

    collection.objects.link( obj )
    view_layer.objects.active = obj
    for border, bordername in itertools.zip_longest(borders, bordernames):
        rightup, leftup, leftdown, rightdown = border
        if bordername is not None:
            strgen = lambda name: "_".join((bordername, name))
        else:
            strgen = lambda name: name
        name_leftup = strgen( "leftup" )
        name_rightup = strgen( "rightup" )
        name_leftdown = strgen( "leftdown" )
        name_rightdown = strgen( "rightdown" )

        create_vertexgroup_with_vertice( obj, name_leftup, leftup )
        create_vertexgroup_with_vertice( obj, name_rightup, rightup )
        create_vertexgroup_with_vertice( obj, name_rightdown, rightdown )
        create_vertexgroup_with_vertice( obj, name_leftdown, leftdown )

    if not (len(bordernames) == 1 and bordernames[0] is None):
        obj.data["_subrectanglesurfaces"] = list(bordernames)

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



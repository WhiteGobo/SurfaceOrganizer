import os
import importlib
_main_modulepath = os.path.join( str(os.environ["TESTMODULE"]), \
                                        "__init__.py")
_main_loader = importlib.machinery.SourceFileLoader("test_my_io_mesh_ply", \
                                        _main_modulepath )
try:
    _main_saveinblenderfile = (0 < int( os.environ["SAVEINBLENDER"] ) )
except Exception:
    _main_saveinblenderfile = False
main = _main_loader.load_module()
import sys
import unittest
import importlib.resources
import tempfile
import bpy
plyhandler = importlib.import_module( ".plysurfacehandler.plyhandler", "test_my_io_mesh_ply" )
PlyObject = plyhandler.ObjectSpec
testdirectory1 = importlib.import_module( ".test", "test_my_io_mesh_ply" )
testdirectory2 = importlib.import_module( ".tests", \
                                        "test_my_io_mesh_ply.plysurfacehandler.plyhandler" )
utils = importlib.import_module( ".utils", "test_my_io_mesh_ply" )
utils.border_operators = importlib.import_module( ".border_operators", \
                                        "test_my_io_mesh_ply.utils" )
utils.surface_operators = importlib.import_module( ".surface_operators", \
                                        "test_my_io_mesh_ply.utils" )

import logging
logger = logging.getLogger( __name__ )

class test_blender_plyimporter( unittest.TestCase ):
    def setUp( self ):
        #main.unregister()
        try:
            main.register()
        except Exception:
            pass
        #try:
        #    bpy.ops.mesh.autocomplete_bordered_partialsurface
        #except AttributeError:
        #    main.register()
        pass

    def test_border_operators( self ):
        scene = bpy.data.scenes[ "TestBorderOperators" ]
        newobj = bpy.data.objects[ "TestBorderOperators" ] 
        override = { "scene": scene, "active_object": newobj }
        borop = utils.border_operators
        bpy.ops.object.mode_set( override, mode='OBJECT' )
        for e in newobj.data.edges:
            e.select = (e.index in (0,4,5))

        allinfo = newobj.partial_surface_information
        index = allinfo.active_surface_index
        partsurf_info = allinfo.partial_surface_info[ index ]
        get_bordervertices = lambda: tuple(partsurf_info["up_border_indexlist"])
        self.assertRaises( KeyError, get_bordervertices )

        scene.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.mesh.add_border_up( override )
        scene.tool_settings.mesh_select_mode = (True, False, False)

        self.assertEqual( (0,5,4,2), get_bordervertices() )


    def test_surface_operators( self ):
        scene = bpy.data.scenes[ "TestSurfaceOperators" ]
        view_layer = scene.view_layers[0]
        #normaluse
        newobj = bpy.data.objects[ "TestSurfaceOperators" ] 
        #scene = newobj.users_scene[0]
        override = { \
                "scene":scene, \
                "active_object":newobj, \
                "view_layer":view_layer, \
                #"edit_object": newobj, \
                #"selected_objects":[newobj], \
                #"selected_active_objects":[ newobj ], \
                }


        bpy.ops.mesh.autocomplete_bordered_partialsurface( override )

        allinfo = newobj.partial_surface_information
        index = allinfo.active_surface_index 
        partsurf_info = allinfo.partial_surface_info[ index ]
        partsurf_name = partsurf_info.name
        vgroup = newobj.vertex_groups[ partsurf_info.vertexgroup ]
        for v in newobj.data.vertices:
            grouplist = set( g.group for g in v.groups )
            testrange = set( list(range(20,36))+[64,65] )
            if v.index in testrange:
                self.assertIn( vgroup.index, grouplist )
            else:
                self.assertEqual( grouplist, set() )

        newobj = bpy.data.objects[ "TestSurfaceOp_autocompleteStar" ] 
        override["active_object"] = newobj
        bpy.ops.mesh.autocomplete_bordered_partialsurface( override )

        newobj = bpy.data.objects[ "TestSurfaceOp_autocomplete4points" ] 
        override["active_object"] = newobj
        bpy.ops.mesh.autocomplete_bordered_partialsurface( override )


    def test_load_ascii( self ):
        scene = bpy.data.scenes["TestLoadSurface"]
        #scene = bpy.data.scenes[ "TestSurfaceOperators" ]
        override = { "scene": scene }
        with importlib.resources.path( testdirectory2, "tmp.ply" ) as filepath:
            bpy.ops.import_mesh.ply_with_border( override, files=[{"name":str(filepath)}])

        objname = "tmp"
        newobj = bpy.data.objects[ -1 ] #last created object
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            override = { "selected_objects":[newobj] }
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )

    def test_save_ascii( self ):
        newobj = bpy.data.objects[ "PreparedWithBorderCube" ] 
        scene = bpy.data.scenes[ "Scene" ]
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            override = { "scene":scene, "selected_objects":[newobj] }
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )

    def test_save_ascii_multiplesurfaces( self ):
        newobj = bpy.data.objects["PreparedWithMultipleSurfaces"] 
        scene = bpy.data.scenes["test_save_ascii_multiplesurfaces"]
        override = { "selected_objects":[newobj] }
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )
            override = { "scene": scene }
            #bpy.ops.import_mesh.ply_with_border( override, \
            #                            files=[{"name":filepath} ] )

            plyobj = PlyObject.load_from_file( filepath )

            asd = plyobj.get_filtered_data( "cornerrectangle", \
                            ("rightup", "leftup", "leftdown", "rightdown"))
            self.assertEqual( tuple( asd ), ((2, 0, 15, 7), (13, 9, 1,3)))

            asd = plyobj.get_dataarray( "cornerrectangle", "surfacename" )
            mysurfnames = [ str( bytes(single), encoding="utf8" ) \
                            for single in asd ]
            self.assertEqual( tuple(mysurfnames), ("surf1", "surf2") )


    def test_load_ascii_multiplesurfaces( self ):
        scene = bpy.data.scenes["test_load_ascii_multiplesurfaces"]
        override = { "scene": scene }
        with importlib.resources.path( testdirectory1, "multiplesurface.ply" ) \
                                                                    as filepath:
            bpy.ops.import_mesh.ply_with_border( override, \
                                                files=[{"name":str(filepath)}])

        get_all_partialsurfaceinfo = main.custom_properties.get_all_partialsurfaceinfo

        obj = bpy.data.objects["multiplesurface"]
        m = main.surfacedivide
        rightup, leftup = m.RIGHTUP_CORNER, m.LEFTUP_CORNER
        leftdown, rightdown = m.LEFTDOWN_CORNER, m.RIGHTDOWN_CORNER
        test = tuple(info for info in get_all_partialsurfaceinfo( obj ))
        textA = ({'Name': 'surf1', 
                rightup: 2, leftup: 0, leftdown: 15, rightdown: 7}, 
                {'Name': 'surf2', 
                rightup: 13, leftup: 9, leftdown: 1, rightdown: 3})
        self.assertEqual( test, textA )

    
    def test_assignborder( self ):
        obj = bpy.data.objects["planeforadding"] 
        scene = bpy.data.scenes["borderadding"]
        override = {"scene":scene, "selected_objects":[obj], \
                    "active_object":obj, "selected_active_objects":[obj]}
        mode = obj.mode
        toolmode = scene.tool_settings.mesh_select_mode
        bpy.ops.object.mode_set( override, mode='EDIT' )
        scene.tool_settings.mesh_select_mode = (True, False, False)#verticemode
        _help_select_single_vertice( override, 2 )
        bpy.ops.mesh.assign_rightupcorner( override )
        _help_select_single_vertice( override, 0 )
        bpy.ops.mesh.assign_leftupcorner( override )
        _help_select_single_vertice( override, 1 )
        bpy.ops.mesh.assign_leftdowncorner( override )
        _help_select_single_vertice( override, 3 )
        bpy.ops.mesh.assign_rightdowncorner( override )
        scene.tool_settings.mesh_select_mode = (False, True, False) #edgemode
        _help_select_edgelist( override, [3, 16, 17, 18, 19] ) #2-3
        bpy.ops.mesh.add_border_right( override )
        _help_select_edgelist( override, [2, 12, 13, 14, 15] ) #1-3
        bpy.ops.mesh.add_border_down( override )
        _help_select_edgelist( override, [1, 8, 9, 10, 11] ) #1-0
        bpy.ops.mesh.add_border_left( override )
        _help_select_edgelist( override, [0, 4, 5, 6, 7] ) #0-2
        bpy.ops.mesh.add_border_up( override )
        scene.tool_settings.mesh_select_mode = toolmode
        bpy.ops.object.mode_set( override, mode=mode )
        bpy.ops.mesh.autocomplete_bordered_partialsurface( override )
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )
            plyobj = PlyObject.load_from_file( filepath )
            asd = plyobj.get_filtered_data( "cornerrectangle", \
                            ("rightup", "leftup", "leftdown", "rightdown"))
            self.assertEqual( tuple( asd ), ((2,0,1,3),))

            asd = plyobj.get_dataarray( "cornerrectangle", "surfacename" )
            mysurfnames = [ str( bytes(single), encoding="utf8" ) \
                            for single in asd ]
            self.assertEqual( tuple(mysurfnames), ("Untitled",))


    def tearDown( self ):
        #main.unregister()
        if _main_saveinblenderfile:
            bpy.ops.wm.save_as_mainfile( filepath="test/new.blend" )

def _help_select_single_vertice( override, index ):
    obj = override["active_object"]
    mode = obj.mode
    bpy.ops.object.mode_set( override, mode='OBJECT' )
    for i, v in enumerate( obj.data.vertices ):
        v.select = (i==index)
    bpy.ops.object.mode_set( override, mode=mode )

def _help_select_edgelist( override, edgeindexlist ):
    obj = override["active_object"]
    mode = obj.mode
    bpy.ops.object.mode_set( override, mode='OBJECT' )
    for e in obj.data.edges:
        e.select = (e.index in edgeindexlist)
    bpy.ops.object.mode_set( override, mode=mode )



if __name__=="__main__":
    #main.unregister()
    #main.register()
    logging.basicConfig( level=logging.CRITICAL )
    sys.argv = [__file__] \
            + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()

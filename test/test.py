import os
import importlib
_main_modulepath = os.path.join( str(os.environ["TESTMODULE"]), \
                                        "__init__.py")
_main_loader = importlib.machinery.SourceFileLoader("test_my_io_mesh_ply", \
                                        _main_modulepath )
main = _main_loader.load_module()
import sys
import unittest
import importlib.resources
import tempfile
import bpy
plyhandler = importlib.import_module( ".plyhandler", "test_my_io_mesh_ply" )
PlyObject = plyhandler.ObjectSpec
testdirectory1 = importlib.import_module( ".test", "test_my_io_mesh_ply" )
testdirectory2 = importlib.import_module( ".tests", \
                                        "test_my_io_mesh_ply.plyhandler" )
utils = importlib.import_module( ".utils", "test_my_io_mesh_ply" )
utils.border_operators = importlib.import_module( ".border_operators", \
                                        "test_my_io_mesh_ply.utils" )
utils.surface_operators = importlib.import_module( ".surface_operators", \
                                        "test_my_io_mesh_ply.utils" )

import logging
logger = logging.getLogger( __name__ )

class test_blender_plyimporter( unittest.TestCase ):
    def setUp( self ):
        #logging.basicConfig( level=logging.DEBUG )
        logging.basicConfig( level=logging.CRITICAL )
        main.unregister()
        #print( bpy.ops.mesh.assign_rightdowncorner)
        #raise Exception()
        main.register()


    def test_border_operators( self ):
        utils.border_operators
        pass

    def test_surface_operators( self ):
        utils.surface_operators
        pass

    def test_load_ascii( self ):
        override = {}
        with importlib.resources.path( testdirectory2, "tmp.ply" ) as filepath:
            bpy.ops.import_mesh.ply_with_border( files=[{"name":str(filepath)}])

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
            self.assertEqual( tuple( asd ), ((2, 0, 15, 7), (13, 9, 3, 1)))

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
                rightup: 7, leftup: 0, leftdown: 2, rightdown: 15}, 
                {'Name': 'surf2', 
                rightup: 9, leftup: 13, leftdown: 3, rightdown: 1})
        self.assertEqual( test, textA )

    
    def test_assignborder( self ):
        obj = bpy.data.objects["planeforadding"] 
        scene = bpy.data.scenes["borderadding"]
        override = {"scene":scene, "selected_objects":[obj], \
                    "active_object":obj, "selected_active_objects":[obj]}
        mode = obj.mode
        bpy.ops.object.mode_set( override, mode='EDIT' )
        _help_select_single_vertice( override, 0 )
        bpy.ops.mesh.assign_rightupcorner( override )
        _help_select_single_vertice( override, 1 )
        bpy.ops.mesh.assign_leftupcorner( override )
        _help_select_single_vertice( override, 2 )
        bpy.ops.mesh.assign_leftdowncorner( override )
        _help_select_single_vertice( override, 3 )
        bpy.ops.mesh.assign_rightdowncorner( override )
        bpy.ops.object.mode_set( override, mode=mode )
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )
            plyobj = PlyObject.load_from_file( filepath )
            asd = plyobj.get_filtered_data( "cornerrectangle", \
                            ("rightup", "leftup", "leftdown", "rightdown"))
            self.assertEqual( tuple( asd ), ((0,1,2,3),))

            asd = plyobj.get_dataarray( "cornerrectangle", "surfacename" )
            mysurfnames = [ str( bytes(single), encoding="utf8" ) \
                            for single in asd ]
            self.assertEqual( tuple(mysurfnames), ("Untitled",))


    def tearDown( self ):
        #bpy.ops.wm.save_as_mainfile( filepath="test/new.blend" )
        main.unregister()

def _help_select_single_vertice( override, index ):
    obj = override["active_object"]
    mode = obj.mode
    bpy.ops.object.mode_set( override, mode='OBJECT' )
    for i, v in enumerate( obj.data.vertices ):
        v.select = (i==index)
    bpy.ops.object.mode_set( override, mode=mode )


if __name__=="__main__":
    sys.argv = [__file__] \
            + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()


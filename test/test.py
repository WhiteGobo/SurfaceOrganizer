import os
import sys
if "TESTSCRIPTS" in os.environ.keys():
    sys.path.insert( 0, os.environ["TESTSCRIPTS"] )
else:
    sys.path.insert( 0, os.getcwd() )
import unittest
import importlib.resources
import bpy

class test_blender_plyimporter( unittest.TestCase ):
    def test_load_and_save_ascii( self ):
        #with importlib.resources.path()
        pass


if __name__=="__main__":
    sys.argv = [__file__] \
            + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()


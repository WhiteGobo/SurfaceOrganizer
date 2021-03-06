ZIP = zip
ZIP_ARGS = 
BLENDER = blender
#BLENDERARGS = --debug-value 3 --verbose 3
BLENDERARGS = 
blenderpackagefiles = \
	./blender_to_plycontainer.py \
	./__init__.py \
	./plycontainer_to_blender.py \
	./editmodeoperators.py \
	./surfacedivide.py \
	./graphic.py \
	./plysurfacehandler/__init__.py \
	./plysurfacehandler/constants.py \
	./plysurfacehandler/dataclass.py \
	./plysurfacehandler/exceptions.py \
	./plysurfacehandler/plyhandler/datacontainer.py \
	./plysurfacehandler/plyhandler/__init__.py \
	./plysurfacehandler/plyhandler/myexport_ply.py \
	./plysurfacehandler/plyhandler/myimport_ply.py \
	./utils/border_operators.py \
	./utils/surface_operators.py \
	./utils/__init__.py


default: my_io_mesh_ply.zip

my_io_mesh_ply.zip: $(blenderpackagefiles)
	-rm $@
	cd ..; $(ZIP) $(ZIP_ARGS) $(addprefix my_io_mesh_ply/, $@) $(addprefix my_io_mesh_ply/, $^)

.PHONY: test
test: test/test.py test/test.blend
	env TESTSCRIPTS=$(abspath test/) TESTMODULE=$(abspath ./) SAVEINBLENDER=0\
		$(BLENDER) $(BLENDERARGS) -b $(word 2, $^) --python $(word 1, $^)

test_with_save: test/test.py test/test.blend
	env TESTSCRIPTS=$(abspath test/) TESTMODULE=$(abspath ./) SAVEINBLENDER=1\
		$(BLENDER) $(BLENDERARGS) -b $(word 2, $^) --python $(word 1, $^)

.PHONY: clean
clean:
	-rm my_io_mesh_ply.zip
	-rm -r __pycache__

ZIP = zip
ZIP_ARGS = 
blenderpackagefiles = \
	./blender_to_plycontainer.py \
	./__init__.py \
	./plycontainer_to_blender.py \
	./editmodeoperators.py \
	./plyhandler/datacontainer.py \
	./plyhandler/__init__.py \
	./plyhandler/myexport_ply.py \
	./plyhandler/myimport_ply.py \

default: my_io_mesh_ply.zip

my_io_mesh_ply.zip: $(blenderpackagefiles)
	-rm $@
	cd ..; $(ZIP) $(ZIP_ARGS) $(addprefix my_io_mesh_ply/, $@) $(addprefix my_io_mesh_ply/, $^)

.PHONY: test
test: test/test.py test/test.blend
	env TESTSCRIPTS=$(abspath test/) TESTMODULE=$(abspath ../) \
		blender -b $(word 2, $^) --python $(word 1, $^)

.PHONY: clean
clean:
	-rm my_io_mesh_ply.zip
	-rm -r __pycache__

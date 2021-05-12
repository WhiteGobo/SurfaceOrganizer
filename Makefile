
.PHONY: test
test: test/test.py
	env TESTSCRIPTS=$(abspath test/) blender -b --python $(word 1, $^)

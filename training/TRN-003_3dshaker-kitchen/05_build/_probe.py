import bpy, sys, os, math
sys.argv = sys.argv[:sys.argv.index("--")] + ["--"] if "--" in sys.argv else sys.argv
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath or "."))

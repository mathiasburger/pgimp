from pgimp.documentation.GimpDocumentationGenerator import GimpDocumentationGenerator
from pgimp.documentation.output.OutputPythonSkeleton import OutputPythonSkeleton

generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton('../../gimp'))
generate_python_skeleton()

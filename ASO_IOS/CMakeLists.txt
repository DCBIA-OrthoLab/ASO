#-----------------------------------------------------------------------------
set(MODULE_NAME ASO_IOS)

set(MODULE_PYTHON_SCRIPTS 
  ${MODULE_NAME}.py
  utils/utils.py)

SlicerMacroBuildScriptedCLI(
  NAME ${MODULE_NAME}
  RESOURCES ${MODULE_PYTHON_SCRIPTS}
  
  )
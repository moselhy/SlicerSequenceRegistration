import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# SequenceRegistration
#

class SequenceRegistration(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Sequence Registration" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Sequences"]
    self.parent.dependencies = []
    self.parent.contributors = ["Mohamed Moselhy (Western University), Andras Lasso (PerkLab, Queen's University)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    TODO
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
    TODO
""" # replace with organization, grant and thanks.

#
# SequenceRegistrationWidget
#

class SequenceRegistrationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    self.registrationInProgress = False
    self.logic = SequenceRegistrationLogic()
    self.logic.logCallback = self.addLog

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLSequenceNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    label = qt.QLabel("Input volume sequence:")
    label.setToolTip( "Pick the multivolume sequence as input." )
    self.inputSelector.setToolTip( "Pick the multivolume sequence as input." )
    parametersFormLayout.addRow(label, self.inputSelector)

    #
    # output volume selector
    #
    self.outputVolumesSelector = slicer.qMRMLNodeComboBox()
    self.outputVolumesSelector.nodeTypes = ["vtkMRMLSequenceNode"]
    self.outputVolumesSelector.baseName = "OutputVolumes"
    self.outputVolumesSelector.selectNodeUponCreation = True
    self.outputVolumesSelector.addEnabled = True
    self.outputVolumesSelector.removeEnabled = True
    self.outputVolumesSelector.renameEnabled = True
    self.outputVolumesSelector.noneEnabled = True
    self.outputVolumesSelector.showHidden = False
    self.outputVolumesSelector.showChildNodeTypes = False
    self.outputVolumesSelector.setMRMLScene( slicer.mrmlScene )
    label = qt.QLabel("Output volume sequence:")
    label.setToolTip( "Pick or create a multivolume sequence as output." )
    self.outputVolumesSelector.setToolTip( "Pick or create a multivolume sequence as output." )
    parametersFormLayout.addRow(label, self.outputVolumesSelector)

    #
    # output transform selector
    #
    self.outputTransformSelector = slicer.qMRMLNodeComboBox()
    self.outputTransformSelector.nodeTypes = ["vtkMRMLSequenceNode"]
    self.outputTransformSelector.baseName = "OutputTransforms"
    self.outputTransformSelector.selectNodeUponCreation = True
    self.outputTransformSelector.addEnabled = True
    self.outputTransformSelector.removeEnabled = True
    self.outputTransformSelector.renameEnabled = True
    self.outputTransformSelector.noneEnabled = True
    self.outputTransformSelector.showHidden = False
    self.outputTransformSelector.showChildNodeTypes = False
    self.outputTransformSelector.setMRMLScene( slicer.mrmlScene )
    label = qt.QLabel("Output transform sequence:")
    label.setToolTip( "(optional) Computed displacement field that transform nodes from moving volume space to fixed volume space. NOTE: You must set at least one output sequence (transform and/or volume)." )
    self.outputTransformSelector.setToolTip( "(optional) Computed displacement field that transform nodes from moving volume space to fixed volume space. NOTE: You must set at least one output sequence (transform and/or volume)." )
    parametersFormLayout.addRow(label, self.outputTransformSelector)

    self.outputTransformBrowser = None


    #
    # Preset selector
    #
    import Elastix
    label = qt.QLabel("Preset:")
    self.registrationPresetSelector = qt.QComboBox()
    label.setToolTip("Pick preset to register with.")
    self.registrationPresetSelector.setToolTip("Pick preset to register with.")
    for preset in self.logic.elastixLogic.getRegistrationPresets():
      self.registrationPresetSelector.addItem("{0} ({1})".format(preset[Elastix.RegistrationPresets_Modality], preset[Elastix.RegistrationPresets_Content]))
    parametersFormLayout.addRow(label, self.registrationPresetSelector)


    #
    # Advanced Area
    #
    advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    advancedCollapsibleButton.text = "Advanced"
    advancedCollapsibleButton.collapsed = 1
    self.layout.addWidget(advancedCollapsibleButton)

    # Layout within the dummy collapsible button
    advancedFormLayout = qt.QFormLayout(advancedCollapsibleButton)


    #
    # fixed frame number value
    #
    self.initialFixedFrame = ctk.ctkSliderWidget()
    self.initialFixedFrame.singleStep = 1
    self.initialFixedFrame.minimum = 0
    self.initialFixedFrame.value = 0
    label = qt.QLabel("Fixed frame at timepoint:")
    label.setToolTip("Set the frame of the input sequence to use as the fixed volume.")
    self.initialFixedFrame.setToolTip("Set the frame of the input sequence to use as the fixed volume.")
    advancedFormLayout.addRow(label, self.initialFixedFrame)

    #
    # Option to show detailed log
    #

    self.showDetailedLogDuringExecutionCheckBox = qt.QCheckBox(" ")
    self.showDetailedLogDuringExecutionCheckBox.checked = False
    label = qt.QLabel("Show detailed log during registration:")
    label.setToolTip("Show detailed log during registration.")
    self.showDetailedLogDuringExecutionCheckBox.setToolTip("Show detailed log during registration.")
    advancedFormLayout.addRow(label, self.showDetailedLogDuringExecutionCheckBox)

    #
    # Option to keep temporary files after registration
    #

    self.keepTemporaryFilesCheckBox = qt.QCheckBox(" ")
    self.keepTemporaryFilesCheckBox.checked = False
    label = qt.QLabel("Keep temporary files:")
    label.setToolTip("Keep temporary files (inputs, computed outputs, logs) after the registration is completed.")
    self.keepTemporaryFilesCheckBox.setToolTip("Keep temporary files (inputs, computed outputs, logs) after the registration is completed.")

    #
    # Button to open the folder in which temporary files are stored
    #

    self.showTemporaryFilesFolderButton = qt.QPushButton("Show temp folder")
    self.showTemporaryFilesFolderButton.toolTip = "Open the folder where temporary files are stored."
    self.showTemporaryFilesFolderButton.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Preferred)

    hbox = qt.QHBoxLayout()
    hbox.addWidget(self.keepTemporaryFilesCheckBox)
    hbox.addWidget(self.showTemporaryFilesFolderButton)
    advancedFormLayout.addRow(label, hbox)


    self.showRegistrationParametersDatabaseFolderButton = qt.QPushButton("Show database folder")
    self.showRegistrationParametersDatabaseFolderButton.toolTip = "Open the folder where temporary files are stored."
    self.showRegistrationParametersDatabaseFolderButton.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Preferred)
    advancedFormLayout.addRow("Registration presets:", self.showRegistrationParametersDatabaseFolderButton)

    customElastixBinDir = self.logic.elastixLogic.getCustomElastixBinDir()
    self.customElastixBinDirSelector = ctk.ctkPathLineEdit()
    self.customElastixBinDirSelector.filters = ctk.ctkPathLineEdit.Dirs
    self.customElastixBinDirSelector.setCurrentPath(customElastixBinDir)
    self.customElastixBinDirSelector.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Preferred)
    self.customElastixBinDirSelector.setToolTip("Set bin directory of an Elastix installation (where elastix executable is located). "
      "If value is empty then default elastix (bundled with SlicerElastix extension) will be used.")
    advancedFormLayout.addRow("Custom Elastix toolbox location:", self.customElastixBinDirSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Register")
    self.applyButton.toolTip = "Start registration."
    self.applyButton.enabled = False
    self.layout.addWidget(self.applyButton)


    self.statusLabel = qt.QPlainTextEdit()
    self.statusLabel.setTextInteractionFlags(qt.Qt.TextSelectableByMouse)
    self.statusLabel.setCenterOnScroll(True)
    self.layout.addWidget(self.statusLabel)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputVolumesSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.showTemporaryFilesFolderButton.connect('clicked(bool)', self.onShowTemporaryFilesFolder)
    self.showRegistrationParametersDatabaseFolderButton.connect('clicked(bool)', self.onShowRegistrationParametersDatabaseFolder)
    # Immediately update deleteTemporaryFiles and show detailed logs in the logic to make it possible to decide to
    # update these variables while the registration is running
    self.keepTemporaryFilesCheckBox.connect("toggled(bool)", self.onKeepTemporaryFilesToggled)
    self.showDetailedLogDuringExecutionCheckBox.connect("toggled(bool)", self.onShowLogToggled)


    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    if not self.inputSelector.currentNode():
      numberOfDataNodes = 0
    else:
      numberOfDataNodes = self.inputSelector.currentNode().GetNumberOfDataNodes()

    if numberOfDataNodes < 1:
      self.initialFixedFrame.maximum = 0
    else:
      self.initialFixedFrame.maximum = numberOfDataNodes-1

    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputVolumesSelector.currentNode()

    if not self.registrationInProgress:
      self.applyButton.text = "Register"
      return
    self.updateBrowsers()

  def onApplyButton(self):

    if self.registrationInProgress:
      self.registrationInProgress = False
      self.logic.setAbortRequested(True)
      self.applyButton.text = "Cancelling..."
      self.applyButton.enabled = False
      return

    self.registrationInProgress = True
    self.applyButton.text = "Cancel"
    self.statusLabel.plainText = ''
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    try:
      self.logic.elastixLogic.setCustomElastixBinDir(self.customElastixBinDirSelector.currentPath)
      self.logic.logStandardOutput = self.showDetailedLogDuringExecutionCheckBox.checked
      self.logic.registerVolumeSequence(self.inputSelector.currentNode(),
        self.outputVolumesSelector.currentNode(), self.outputTransformSelector.currentNode(),
        int(self.initialFixedFrame.value), self.registrationPresetSelector.currentIndex)
    except Exception as e:
      print e
      self.addLog("Error: {0}".format(e.message))
      import traceback
      traceback.print_exc()
    finally:
      slicer.app.restoreOverrideCursor()
      self.registrationInProgress = False
      self.onSelect() # restores default Apply button state

  def addLog(self, text):
    """Append text to log window
    """
    self.statusLabel.appendPlainText(text)
    slicer.app.processEvents()  # force update

  def onShowTemporaryFilesFolder(self):
    qt.QDesktopServices().openUrl(qt.QUrl("file:///" + self.logic.elastixLogic.getTempDirectoryBase(), qt.QUrl.TolerantMode));

  def onKeepTemporaryFilesToggled(self, toggle):
    self.logic.elastixLogic.deleteTemporaryFiles = toggle

  def onShowRegistrationParametersDatabaseFolder(self):
    qt.QDesktopServices().openUrl(qt.QUrl("file:///" + self.logic.elastixLogic.registrationParameterFilesDir, qt.QUrl.TolerantMode));

  def onShowLogToggled(self, toggle):
    self.logic.elastixLogic.logStandardOutput = toggle

#
# SequenceRegistrationLogic
#

class SequenceRegistrationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.logStandardOutput = False
    self.logCallback = None

    import Elastix
    self.elastixLogic = Elastix.ElastixLogic()

  def setAbortRequested(self, abortRequested):
    self.elastixLogic.abortRequested = abortRequested

  def findBrowserForSequence(self, sequenceNode):
    browserNodes = slicer.util.getNodesByClass("vtkMRMLSequenceBrowserNode")
    for browserNode in browserNodes:
      if browserNode.IsSynchronizedSequenceNode(sequenceNode, True):
        return browserNode
    return None

  def registerVolumeSequence(self, inputVolSeq, outputVolSeq, outputTransformSeq, fixedVolumeItemNumber, presetIndex):
    self.elastixLogic.logStandardOutput = self.logStandardOutput
    self.elastixLogic.logCallback = self.logCallback
    self.abortRequested = False

    import Elastix
    parameterFilenames = self.elastixLogic.getRegistrationPresets()[presetIndex][Elastix.RegistrationPresets_ParameterFilenames]

    fixedSeqBrowser = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
    fixedSeqBrowser.SetAndObserveMasterSequenceNodeID(inputVolSeq.GetID())
    fixedSeqBrowser.SetSelectedItemNumber(fixedVolumeItemNumber)
    slicer.modules.sequencebrowser.logic().UpdateAllProxyNodes()
    slicer.app.processEvents()
    fixedVolume = fixedSeqBrowser.GetProxyNode(inputVolSeq)

    movingSeqBrowser = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
    movingSeqBrowser.SetAndObserveMasterSequenceNodeID(inputVolSeq.GetID())

    # Initialize output sequences
    for seq in [outputVolSeq, outputTransformSeq]:
      if seq:
        seq.RemoveAllDataNodes()
        seq.SetIndexType(inputVolSeq.GetIndexType())
        seq.SetIndexName(inputVolSeq.GetIndexName())
        seq.SetIndexUnit(inputVolSeq.GetIndexUnit())

    outputVol = slicer.mrmlScene.AddNewNodeByClass(fixedVolume.GetClassName())

    # Only request output transform if it is needed, to save some time on computing it
    if outputTransformSeq:
      outputTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode")
    else:
      outputTransform = None

    try:

      numberOfDataNodes = inputVolSeq.GetNumberOfDataNodes()
      for movingVolumeItemNumber in range(numberOfDataNodes):
        if movingVolumeItemNumber>0:
          self.elastixLogic.addLog("---------------------")
        self.elastixLogic.addLog("Registering item {0}/{1}".format(movingVolumeItemNumber+1, numberOfDataNodes))
        movingSeqBrowser.SetSelectedItemNumber(movingVolumeItemNumber)
        slicer.modules.sequencebrowser.logic().UpdateProxyNodesFromSequences(movingSeqBrowser)
        movingVolume = movingSeqBrowser.GetProxyNode(inputVolSeq)

        if movingVolumeItemNumber != fixedVolumeItemNumber:
          self.elastixLogic.registerVolumes(
            fixedVolume, movingVolume,
            outputVolumeNode = outputVol,
            parameterFilenames = parameterFilenames,
            outputTransformNode = outputTransform
            )

          if outputVolSeq:
            outputVolSeq.SetDataNodeAtValue(outputVol, inputVolSeq.GetNthIndexValue(movingVolumeItemNumber))
          if outputTransformSeq:
            outputTransformSeq.SetDataNodeAtValue(outputTransform, inputVolSeq.GetNthIndexValue(movingVolumeItemNumber))
        else:
          self.elastixLogic.addLog("Same as fixed volume.")
          if outputVolSeq:
            outputVolSeq.SetDataNodeAtValue(fixedVolume, inputVolSeq.GetNthIndexValue(movingVolumeItemNumber))
          if outputTransformSeq:
            # Set identity as transform (vtkTransform is initialized to identity transform by default)
            outputTransform.SetAndObserveTransformToParent(vtk.vtkTransform())
            outputTransformSeq.SetDataNodeAtValue(outputTransform, inputVolSeq.GetNthIndexValue(movingVolumeItemNumber))

      # Uniformly match scalar type of the fixed volume in the output sequence to match the others
      outputFixedVol = outputVolSeq.GetDataNodeAtValue(inputVolSeq.GetNthIndexValue(fixedVolumeItemNumber))
      imageCast = vtk.vtkImageCast()
      ijkToRasMatrix = vtk.vtkMatrix4x4()
      imageCast.SetInputData(outputFixedVol.GetImageData())
      imageCast.SetOutputScalarTypeToShort()
      imageCast.Update()
      outputFixedVol.SetAndObserveImageData(imageCast.GetOutput())
      movingVolIndices = range(numberOfDataNodes)
      movingVolIndices.remove(fixedVolumeItemNumber)
      if len(movingVolIndices) >= 1:
        matchedVolumeIndex = movingVolIndices[0]
        matchedVolume = outputVolSeq.GetDataNodeAtValue(outputVolSeq.GetNthIndexValue(matchedVolumeIndex))
        outputFixedVol.SetOrigin(matchedVolume.GetOrigin())
        outputFixedVol.SetSpacing(matchedVolume.GetSpacing())

    finally:

      # Temporary result nodes
      slicer.mrmlScene.RemoveNode(outputVol)
      if outputTransformSeq:
        slicer.mrmlScene.RemoveNode(outputTransform)
      # Temporary input browser nodes
      slicer.mrmlScene.RemoveNode(fixedSeqBrowser)
      slicer.mrmlScene.RemoveNode(movingSeqBrowser)
      # Temporary input volume proxy nodes
      slicer.mrmlScene.RemoveNode(fixedVolume)
      slicer.mrmlScene.RemoveNode(movingVolume)

      # Move output sequences in the same browser node as the input volume sequence
      outputBrowserNode = self.findBrowserForSequence(inputVolSeq)
      if outputBrowserNode:
        if outputVolSeq and not self.findBrowserForSequence(outputVolSeq):
          outputBrowserNode.AddSynchronizedSequenceNodeID(outputVolSeq.GetID())
        if outputTransformSeq and not self.findBrowserForSequence(outputTransformSeq):
          outputBrowserNode.AddSynchronizedSequenceNodeID(outputTransformSeq.GetID())

class SequenceRegistrationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SequenceRegistration()

  def test_SequenceRegistration(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    #
    # first, get some data
    #

    import SampleData
    sampleDataLogic = SampleData.SampleDataLogic()
    inputVolSeqBrowser = sampleDataLogic.downloadSample("CTPCardio")[0]
    inputVolSeq = inputVolSeqBrowser.GetMasterSequenceNode()

    outputVolSeq = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode", "OutVolSeq")
    outputTransformSeq = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode", "OutTransformSeq")

    for i in range(inputVolSeq.GetNumberOfDataNodes())[3:]:
      inputVolSeq.RemoveDataNodeAtValue(str(i))

    self.delayDisplay('Starting registration...')

    import Elastix
    logic = SequenceRegistrationLogic()
    logic.registerVolumeSequence(inputVolSeq, outputVolSeq, outputTransformSeq, 1, 0)

    slicer.app.restoreOverrideCursor()
    self.delayDisplay('Test passed!')

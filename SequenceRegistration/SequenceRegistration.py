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
    self.parent.title = "Sequence Registration"
    self.parent.categories = ["Sequences"]
    self.parent.dependencies = []
    self.parent.contributors = ["Mohamed Moselhy (Western University), Andras Lasso (PerkLab, Queen's University), and Feng Su (Western University)"]
    self.parent.helpText = """For up-to-date user guides, go to <a href="https://github.com/moselhy/SlicerSequenceRegistration">the official GitHub page</a>
"""
    self.parent.acknowledgementText = """
"""

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
    self.inputSelector.setToolTip("Pick input volume sequence. Each time point will be registered to the fixed frame.")
    parametersFormLayout.addRow("Input volume sequence:", self.inputSelector)

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
    self.outputVolumesSelector.setMRMLScene(slicer.mrmlScene)
    self.outputVolumesSelector.setToolTip("Select a node for storing computed motion-compensated volume sequence.")
    parametersFormLayout.addRow("Output volume sequence:", self.outputVolumesSelector)

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
    self.outputTransformSelector.setMRMLScene(slicer.mrmlScene)
    self.outputTransformSelector.setToolTip("Computed displacement field that transform nodes from moving volume space to fixed volume space. NOTE: You must set at least one output sequence (transform and/or volume).")
    parametersFormLayout.addRow("Output transform sequence:", self.outputTransformSelector)

    #
    # Output transform mode
    #
    import Elastix
    self.registrationPresetSelector = qt.QComboBox()
    self.registrationPresetSelector.setToolTip("Pick preset to register with.")
    for preset in self.logic.elastixLogic.getRegistrationPresets():
      self.registrationPresetSelector.addItem("{0} ({1})".format(preset[Elastix.RegistrationPresets_Modality], preset[Elastix.RegistrationPresets_Content]))
    self.registrationPresetSelector.addItem("*NEW*")
    self.newPresetIndex = self.registrationPresetSelector.count - 1
    parametersFormLayout.addRow("Preset:", self.registrationPresetSelector)

    #
    # Advanced Area
    #
    advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    advancedCollapsibleButton.text = "Advanced"
    advancedCollapsibleButton.collapsed = 1
    self.layout.addWidget(advancedCollapsibleButton)

    # Layout within the dummy collapsible button
    advancedFormLayout = qt.QFormLayout(advancedCollapsibleButton)

    # Fixed frame index
    self.sequenceFixedItemIndexWidget = ctk.ctkSliderWidget()
    self.sequenceFixedItemIndexWidget.decimals = 0
    self.sequenceFixedItemIndexWidget.singleStep = 1
    self.sequenceFixedItemIndexWidget.minimum = 0
    self.sequenceFixedItemIndexWidget.value = 0
    self.sequenceFixedItemIndexWidget.setToolTip("Set the frame of the input sequence to use as the fixed volume (that all other volumes will be registered to.")
    advancedFormLayout.addRow("Fixed frame index:", self.sequenceFixedItemIndexWidget)

    # Sequence start index
    self.sequenceStartItemIndexWidget = ctk.ctkSliderWidget()
    self.sequenceStartItemIndexWidget.minimum = 0
    self.sequenceStartItemIndexWidget.decimals = 0
    self.sequenceStartItemIndexWidget.setToolTip("First item in the sequence to register.")
    advancedFormLayout.addRow("Start frame index:", self.sequenceStartItemIndexWidget)

    # Sequence end index
    self.sequenceEndItemIndexWidget = ctk.ctkSliderWidget()
    self.sequenceEndItemIndexWidget.minimum = 0
    self.sequenceEndItemIndexWidget.decimals = 0
    self.sequenceEndItemIndexWidget.setToolTip("Last item in the sequence to register.")
    advancedFormLayout.addRow("End frame index:", self.sequenceEndItemIndexWidget)

    #
    # Transform direction
    #
    self.transformDirectionSelector = qt.QComboBox()
    self.transformDirectionSelector.setToolTip("Moving to fixed: computes stabilizing transform. Fixed to moving: computes morphing transform, which deforms structures defined on the fixed frame to all moving frames.")
    self.transformDirectionSelector.addItem("moving frames to fixed frame")
    self.transformDirectionSelector.addItem("fixed frame to moving frames")
    advancedFormLayout.addRow("Transform direction:", self.transformDirectionSelector)

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
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputSelect)
    self.outputVolumesSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.sequenceFixedItemIndexWidget.connect('valueChanged(double)', self.setSequenceItemIndex)
    self.sequenceStartItemIndexWidget.connect('valueChanged(double)', self.setSequenceItemIndex)
    self.sequenceEndItemIndexWidget.connect('valueChanged(double)', self.setSequenceItemIndex)
    self.showTemporaryFilesFolderButton.connect('clicked(bool)', self.onShowTemporaryFilesFolder)
    self.showRegistrationParametersDatabaseFolderButton.connect('clicked(bool)', self.onShowRegistrationParametersDatabaseFolder)
    # Immediately update deleteTemporaryFiles and show detailed logs in the logic to make it possible to decide to
    # update these variables while the registration is running
    self.keepTemporaryFilesCheckBox.connect("toggled(bool)", self.onKeepTemporaryFilesToggled)
    self.showDetailedLogDuringExecutionCheckBox.connect("toggled(bool)", self.onShowLogToggled)
    # Check if user selects to create a new preset
    self.registrationPresetSelector.connect("activated(int)", self.onCreatePresetPressed)


    # Add vertical spacer
    self.layout.addStretch(1)

    # Variable initializations
    self.newParameterButtons = []

    # Refresh Apply button state
    self.onInputSelect()

  def setSequenceItemIndex(self, index):
    sequenceBrowserNode = self.logic.findBrowserForSequence(self.inputSelector.currentNode())
    sequenceBrowserNode.SetSelectedItemNumber(int(index))

  def onCreatePresetPressed(self):
    if self.registrationPresetSelector.currentIndex != self.newPresetIndex:
      return

    self.newPresetBox = qt.QDialog()
    self.customPresetLayout = qt.QVBoxLayout()

    self.addParameterFile()

    addPresetButton = qt.QPushButton("Add more presets...")
    addPresetButton.connect("clicked(bool)", self.addParameterFile)
    self.customPresetLayout.addWidget(addPresetButton)
    self.newPresetBox.setLayout(self.customPresetLayout)


    # Add fields to specify descriptions, etc... for that preset (to be included in the XML file)

    groupBox = qt.QGroupBox()
    formLayout = qt.QFormLayout()

    self.contentBox = qt.QLineEdit()
    formLayout.addRow("Content: ", self.contentBox)
    self.descriptionBox = qt.QLineEdit()
    formLayout.addRow("Description: ", self.descriptionBox)
    self.idBox = qt.QLineEdit()
    formLayout.addRow("Id: ", self.idBox)
    self.modalityBox = qt.QLineEdit()
    formLayout.addRow("Modality: ", self.modalityBox)
    self.publicationsBox = qt.QPlainTextEdit()
    formLayout.addRow("Publications: ", self.publicationsBox)

    groupBox.setLayout(formLayout)
    self.customPresetLayout.addWidget(groupBox)

    # Add Ok/Cancel buttons and connect them to the main dialog
    buttonBox = qt.QDialogButtonBox()
    buttonBox.setStandardButtons(qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel)
    buttonBox.setCenterButtons(True)
    buttonBox.connect("accepted()", self.newPresetBox.accept)
    buttonBox.connect("rejected()", self.newPresetBox.reject)

    self.customPresetLayout.addWidget(buttonBox)

    response = self.newPresetBox.exec_()

    if response:
      self.createPreset()

  def createPreset(self):
    filenames = []
    # Get all the filenames that the user included
    for includeButton in self.newPresetBox.findChildren(qt.QPushButton):
      if includeButton.isChecked():
        row = self.newParameterButtons[self.getRowNumber(includeButton)]
        filepath = os.path.realpath(row[0].text)
        if os.path.exists(filepath):
          filenames.append(filepath)
        else:
          logging.error("File \"%s\" was not included, it was not found in %s" % (os.path.basename(filepath), os.path.dirname(filepath)))

    if len(filenames) > 0:
      from shutil import copyfile
      import xml.etree.ElementTree as ET
      databaseDir = self.logic.elastixLogic.registrationParameterFilesDir
      presetDatabase = os.path.join(databaseDir, 'ElastixParameterSetDatabase.xml')
      xml = ET.parse(presetDatabase)
      root = xml.getroot()
      attributes = {}
      attributes['content'] = self.contentBox.text
      attributes['description'] = self.descriptionBox.text
      attributes['id'] = self.idBox.text
      attributes['modality'] = self.modalityBox.text
      attributes['publications'] = self.publicationsBox.plainText

      presetElement = ET.SubElement(root, "ParameterSet", attributes)
      parFilesElement = ET.SubElement(presetElement, "ParameterFiles")

      # Copy parameter files to database directory
      for file in filenames:
        filename = os.path.basename(file)
        newFilePath = os.path.join(databaseDir, filename)
        if os.path.exists(newFilePath) and not self.overwriteParFile(filename):
          continue
        copyfile(file, newFilePath)
        ET.SubElement(parFilesElement, "File", {"Name" : filename})

      xml.write(presetDatabase)

    # Destroy old dialog box
    self.newPresetBox.delete()
    self.newParameterButtons = []

    # Refresh list and select new preset
    self.selectNewPreset()

  def selectNewPreset(self):
    import Elastix
    self.logic = SequenceRegistrationLogic()
    allPresets = self.logic.elastixLogic.getRegistrationPresets()
    preset = allPresets[len(allPresets) - 1]
    self.registrationPresetSelector.insertItem(self.newPresetIndex, "{0} ({1})".format(preset[Elastix.RegistrationPresets_Modality], preset[Elastix.RegistrationPresets_Content]))
    self.registrationPresetSelector.currentIndex = self.newPresetIndex
    self.newPresetIndex += 1

  def overwriteParFile(self, filename):
    d = qt.QDialog()
    resp = qt.QMessageBox.warning(d, "Overwrite File?", "File \"%s\" already exists, do you want to overwrite it? (Clicking Discard would exclude the file from the preset)" % filename, qt.QMessageBox.Save | qt.QMessageBox.Discard, qt.QMessageBox.Save)
    return resp == qt.QMessageBox.Save

  def addParameterFile(self):
    lastSelectorIndex = self.customPresetLayout.count() - 3
    parameterFilePathButton = qt.QPushButton("Select a file")
    parameterFileToggleButton = qt.QPushButton("Include")
    parameterFileToggleButton.setCheckable(True)

    rowLayout = qt.QHBoxLayout()
    rowLayout.addWidget(parameterFilePathButton)
    rowLayout.addWidget(parameterFileToggleButton)

    self.newParameterButtons.append((parameterFilePathButton, parameterFileToggleButton))
    self.customPresetLayout.insertLayout(lastSelectorIndex, rowLayout)

    parameterFilePathButton.connect("clicked(bool)", lambda: self.selectParameterFile(parameterFilePathButton))

  def selectParameterFile(self, sender):
    sender.setText(qt.QFileDialog.getOpenFileName())
    row = self.newParameterButtons[self.getRowNumber(sender)]
    row[1].setChecked(True)

  def getRowNumber(self, sender):
    for row in self.newParameterButtons:
      if sender in row:
        return self.newParameterButtons.index(row)

  def cleanup(self):
  	pass

  def onInputSelect(self):
    if not self.inputSelector.currentNode():
      numberOfDataNodes = 0
    else:
      numberOfDataNodes = self.inputSelector.currentNode().GetNumberOfDataNodes()

    for sequenceItemSelectorWidget in [self.sequenceFixedItemIndexWidget, self.sequenceStartItemIndexWidget, self.sequenceEndItemIndexWidget]:
      if numberOfDataNodes < 1:
        sequenceItemSelectorWidget.maximum = 0
        sequenceItemSelectorWidget.enabled = False
      else:
        sequenceItemSelectorWidget.maximum = numberOfDataNodes-1
        sequenceItemSelectorWidget.enabled = True

    self.sequenceFixedItemIndexWidget.value =  int(self.sequenceStartItemIndexWidget.maximum / 2)
    self.sequenceStartItemIndexWidget.value =  0
    self.sequenceEndItemIndexWidget.value = self.sequenceEndItemIndexWidget.maximum

    self.onSelect()

  def onSelect(self):

    self.applyButton.enabled = self.inputSelector.currentNode() and (self.outputVolumesSelector.currentNode() or self.outputTransformSelector.currentNode())

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
      computeMovingToFixedTransform = (self.transformDirectionSelector.currentIndex == 0)
      fixedFrameIndex = int(self.sequenceFixedItemIndexWidget.value)
      startFrameIndex = int(self.sequenceStartItemIndexWidget.value)
      endFrameIndex = int(self.sequenceEndItemIndexWidget.value)
      self.logic.elastixLogic.setCustomElastixBinDir(self.customElastixBinDirSelector.currentPath)
      self.logic.logStandardOutput = self.showDetailedLogDuringExecutionCheckBox.checked
      self.logic.registerVolumeSequence(self.inputSelector.currentNode(),
        self.outputVolumesSelector.currentNode(), self.outputTransformSelector.currentNode(),
        fixedFrameIndex, self.registrationPresetSelector.currentIndex, computeMovingToFixedTransform,
        startFrameIndex, endFrameIndex)
    except Exception as e:
      print(e)
      self.addLog("Error: {0}".format(str(e)))
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
    self.logic.elastixLogic.deleteTemporaryFiles = not toggle

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

  def registerVolumeSequence(self, inputVolSeq, outputVolSeq, outputTransformSeq, fixedVolumeItemNumber, presetIndex, computeMovingToFixedTransform = True,
    startFrameIndex=None, endFrameIndex=None):
    """
    computeMovingToFixedTransform: if True then moving->fixed else fixed->moving transforms are computed
    """
    self.elastixLogic.logStandardOutput = self.logStandardOutput
    self.elastixLogic.logCallback = self.logCallback
    self.abortRequested = False

    import Elastix
    parameterFilenames = self.elastixLogic.getRegistrationPresets()[presetIndex][Elastix.RegistrationPresets_ParameterFilenames]

    fixedSeqBrowser = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
    fixedSeqBrowser.SetAndObserveMasterSequenceNodeID(inputVolSeq.GetID())
    fixedSeqBrowser.SetSelectedItemNumber(fixedVolumeItemNumber)
    if slicer.app.majorVersion*100+slicer.app.minorVersion < 411:
      sequencesModule = slicer.modules.sequencebrowser
    else:
      sequencesModule = slicer.modules.sequences
    sequencesModule.logic().UpdateAllProxyNodes()
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
      if startFrameIndex is None:
        startFrameIndex = 0
      if endFrameIndex is None:
        endFrameIndex = numberOfDataNodes-1
      movingVolIndices = list(range(startFrameIndex, endFrameIndex+1))
      for movingVolumeItemNumber in movingVolIndices:
        if movingVolumeItemNumber>movingVolIndices[0]:
          self.elastixLogic.addLog("---------------------")
        self.elastixLogic.addLog("Registering item {0} of {1}".format(movingVolumeItemNumber-movingVolIndices[0]+1, len(movingVolIndices)))
        movingSeqBrowser.SetSelectedItemNumber(movingVolumeItemNumber)
        sequencesModule.logic().UpdateProxyNodesFromSequences(movingSeqBrowser)
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
            if not computeMovingToFixedTransform:
              outputTransform.Inverse()
            outputTransformSeq.SetDataNodeAtValue(outputTransform, inputVolSeq.GetNthIndexValue(movingVolumeItemNumber))
        else:
          self.elastixLogic.addLog("Same as fixed volume.")
          if outputVolSeq:
            outputVolSeq.SetDataNodeAtValue(fixedVolume, inputVolSeq.GetNthIndexValue(movingVolumeItemNumber))
            outputVolSeq.GetDataNodeAtValue(inputVolSeq.GetNthIndexValue(movingVolumeItemNumber)).SetName(slicer.mrmlScene.GetUniqueNameByString("Volume"))

          if outputTransformSeq:
            # Set identity as transform (vtkTransform is initialized to identity transform by default)
            outputTransform.SetAndObserveTransformToParent(vtk.vtkTransform())
            outputTransformSeq.SetDataNodeAtValue(outputTransform, inputVolSeq.GetNthIndexValue(movingVolumeItemNumber))

      if outputVolSeq:
        # Make scalar type of the fixed volume in the output sequence to the other volumes
        outputFixedVol = outputVolSeq.GetDataNodeAtValue(inputVolSeq.GetNthIndexValue(fixedVolumeItemNumber))
        imageCast = vtk.vtkImageCast()
        ijkToRasMatrix = vtk.vtkMatrix4x4()
        imageCast.SetInputData(outputFixedVol.GetImageData())
        imageCast.SetOutputScalarTypeToShort()
        imageCast.Update()
        outputFixedVol.SetAndObserveImageData(imageCast.GetOutput())
        # Make origin and spacing match exactly other volumes
        movingVolIndices.remove(fixedVolumeItemNumber)
        if len(movingVolIndices) >= 1:
          matchedVolumeIndex = movingVolIndices[0]
          matchedVolume = outputVolSeq.GetDataNodeAtValue(inputVolSeq.GetNthIndexValue(matchedVolumeIndex))
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

      # Move output sequences in the same browser node as the input volume sequence and rename their proxy nodes
      outputBrowserNode = self.findBrowserForSequence(inputVolSeq)

      if outputBrowserNode:
        if outputVolSeq and not self.findBrowserForSequence(outputVolSeq):
          outputBrowserNode.AddSynchronizedSequenceNodeID(outputVolSeq.GetID())
          outputBrowserNode.SetOverwriteProxyName(outputVolSeq, True)
        if outputTransformSeq and not self.findBrowserForSequence(outputTransformSeq):
          outputBrowserNode.AddSynchronizedSequenceNodeID(outputTransformSeq.GetID())
          outputBrowserNode.SetOverwriteProxyName(outputTransformSeq, True)

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
    inputVolSeqBrowser = sampleDataLogic.downloadSample("CTPCardio")
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

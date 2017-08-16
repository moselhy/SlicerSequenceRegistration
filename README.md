# SequenceRegistration
## Uses [SlicerElastix](https://github.com/lassoan/SlicerElastix) module logic to register 4D multivolumes

### Screenshot:


![Alt text](screenshot.png?raw=true "Screenshot")

### Usage:

## All the input that is needed is a multivolume sequence.
###### Currently developing an input for masks as well

### How to make a sequence:

#### From DICOMs:
1. Load up the `DICOM Browser` in Slicer
![Alt text](screenshots/loadDcm.png?raw=true "Load DICOM")

2. Make sure the `Advanced` checkbox is checked, and the `MultiVolumeImporterPlugin` is also checked
![Alt text](screenshots/multivolume.png?raw=true "Load DICOMs as a multivolume")

3. Import your dataset
![Alt text](screenshots/import.png?raw=true "Import DICOMs")

4. Select your dataset and click `Examine`
![Alt text](screenshots/examine.png?raw=true "Examine DICOMs")

5. Select the one with the reader `MultiVolume` and click `Load`
![Alt text](screenshots/load.png?raw=true "Load MultiVolume")

6. Click the `Save` button in the top pane of Slicer
![Alt text](screenshots/save.png?raw=true "Save MultiVolume")

7. Check the MultiVolume that was chosen in step 5 and choose a folder to save it in
![Alt text](screenshots/nrrd.png?raw=true "Save MultiVolume as Nrrd")

8. Edit the file name to add `.seq` before `.nrrd` and click `Save`
![Alt text](screenshots/seqnrrd.png?raw=true "Save MultiVolume as Nrrd Sequence")

9. Close the Scene by clicking `File -> Close Scene`
![Alt text](screenshots/closescene.png?raw=true "Close Scene")

10. Click the `Data` button at the top of Slicer
![Alt text](screenshots/data.png?raw=true "Add Data")

11. Choose the file you saved in step 8 and click `Open`, then click `Ok` to load the MultiVolume Sequence
![Alt text](screenshots/open.png?raw=true "Load MultiVolume Sequence")

12. Now you can choose the sequence as input in the Sequence Registration Module
![Alt text](screenshots/choose.png?raw=true "Use MultiVolume Sequence in Sequence Registration")

#### From a MultiVolume NRRD:
- Perform steps 8-12 above

#### From many scalar volumes:
1. Open the Sequences module
![Alt text](screenshots/choose.png?raw=true "Open the Sequences module")

2. Create a new Sequence
![Alt text](screenshots/createseq.png?raw=true "Create a new Sequence")

3. Add scalar volumes by selecting them and clicking the green left arrow
![Alt text](screenshots/addvoltoseq.png?raw=true "Append Sequence with Scalar Volumes")

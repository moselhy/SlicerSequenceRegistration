# Volume sequence registration for 3D Slicer

This extension registers a sequence of volumes (3D+t a.k.a. 4D image data) to a selected volume. Processing results is a transform sequence (3D displacement field changing in time) and motion-compensated volume sequence. The transform sequence can be used for deforming point targets or structures.

Applications include motion-compensation for volume comparison and analysis of organ motion.

The module uses [Elastix](http://elastix.isi.uu.nl/) registration toolkit through [SlicerElastix extension](https://github.com/lassoan/SlicerElastix).

![Alt text](screenshot01.png?raw=true "Screenshot")

See full result here (animated gif): http://wiki.imaging.robarts.ca/images/e/eb/14.gif

## Usage:

### Simple example

1. Load sample 4D cardiac sequence by opening SampleData module and clicking on `CTPCardio` data set. The sequence browser toolbar will appear that can be used to play/pause/browse the volume sequence.

2. Perform registration

* Switch to Sequence registration module (in Sequences category in the module list)
* Input volume sequence: CTP-cardio
* Output volume sequence: Create new
* Output transform sequence: Create new
* Advanced section / Fixed frame at timepoint: 7 (the first frame does not contain contrast agent, so registering all the contrasted frames to it would not provide optimal results)
* Click Register -- and wait about 10 minutes

3. Review results

* After the registration is completed, the motion-compensated output volume sequence is shown in slice viewers.
* Use the sequence browser toolbar to replay the sequence.
* Transform can be visualized by switching to Transforms module, selecting the output transform, and adjusting options in Display section.

### How to register your own data

All the required input is a volume sequence node in Slicer. In the future, the module will support specifying masks for specifying a region of interest for registration.

#### Create volume sequence from 4D DICOM image:

1. Load up the `DICOM Browser` in Slicer

![Alt text](img/loadDcm.png?raw=true "Load DICOM")

2. Make sure the `Advanced` checkbox is checked, and the `MultiVolumeImporterPlugin` is also checked

![Alt text](img/multivolume.png?raw=true "Load DICOMs as a multivolume")

3. Import your dataset

![Alt text](img/import.png?raw=true "Import DICOMs")

4. Select your dataset and click `Examine`

![Alt text](img/examine.png?raw=true "Examine DICOMs")

5. Select the one with the reader `MultiVolume` and click `Load`

![Alt text](img/load.png?raw=true "Load MultiVolume")

6. Click the `Save` button in the top pane of Slicer

![Alt text](img/save.png?raw=true "Save MultiVolume")

7. Check the MultiVolume that was chosen in step 5 and choose a folder to save it in

![Alt text](img/nrrd.png?raw=true "Save MultiVolume as Nrrd")

8. Edit the file name by double-clicking on it, and append `.seq` to the end of the filename (when you load this image into Slicer later, this .seq.nrrd file extension gives a hint to Slicer that the file should be interpreted as a volume sequence)

8. Click `Save`

![Alt text](img/seqnrrd.png?raw=true "Save MultiVolume as Nrrd Sequence")

9. Close the Scene by clicking `File -> Close Scene`

![Alt text](img/closescene.png?raw=true "Close Scene")

10. Click the `Data` button at the top of Slicer

![Alt text](img/data.png?raw=true "Add Data")

11. Choose the file you saved in step 8 and click `Open`, then click `Ok` to load the MultiVolume Sequence

![Alt text](img/open.png?raw=true "Load MultiVolume Sequence")

12. Now you can choose the sequence as input in the Sequence Registration Module

![Alt text](img/choose.png?raw=true "Use MultiVolume Sequence in Sequence Registration")

#### Create volume sequence from 4D NRRD image:

- Perform steps 8-13 [above](#from-dicoms)

#### Create volume sequence from many scalar volumes

1. Open the Sequences module

![Alt text](img/choose.png?raw=true "Open the Sequences module")

2. Create a new Sequence

![Alt text](img/createseq.png?raw=true "Create a new Sequence")

3. Add scalar volumes by selecting them and clicking the green left arrow

![Alt text](img/addvoltoseq.png?raw=true "Append Sequence with Scalar Volumes")


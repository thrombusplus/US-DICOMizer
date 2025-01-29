# US-DICOMizer
US-DICOMizer is an advanced application designed to automate and streamline the preparation of ultrasound diagnostic DICOM files for AI-based workflows. The application incorporates three key functionalities: 

1. **anonymisation** to remove sensitive patient information while preserving essential metadata for AI tasks, 
2. **cropping** to extract relevant regions from images or videos, and 
3. **tagging** to annotate files with critical metadata, such as anatomical position, imaging purpose, and other contextual information. 

These functionalities aim to address the unique requirements of ultrasound imaging data preparation while ensuring compliance with data privacy regulations and clinical standards.

![US-DICOMizer main view](images/US-dicomizer_app_main_window_01.jpg)

## Changelog
### Changes in version 4.14  

### Changes in version 4.13  
If in [settings] section at settings.ini file  
user_can_change_compression_level = no  
then at settings window the jpeg quality text entry is disabled  

Added the free text area at the footer  
Minor updates at footer section  
### Changes in version 4.12  
Smaller font size in treeviews  
Separation of attributes into metadata and dataset  
Added ability to copy values ​​from treeview with attribute tags by right-click  
Added options (title) to filedialog  
Removed simpleTK and scikit-image modules as they are no longer used  

## Citation

If you use US-DICOMizer in a scientific publication, we would appreciate using the following citation:

* *Pechlivanis, D., Didaskalou, S., Kaldoudi, E. and Drosatos, G. (2025). Preparing Ultrasound Imaging Data for Artificial Intelligence Tasks: Anonymisation, Cropping, and Tagging. In Proceedings of the 18th International Joint Conference on Biomedical Engineering Systems and Technologies (BIOSTEC 2025) - Volume 5: HEALTHINF, ISBN 978-989-758-xxx-x, ISSN 2184-4305, pages xxx-xxx. DOI: 10.5220/001xxxxxxxxxxxxx*

and as BibTeX:
```
@incollection{Pechlivanis_US-DICOMizer_2025,
    author       = {Pechlivanis, Dimitrios and Didaskalou, Stylianos and Kaldoudi, Eleni and Drosatos, George},
    title        = {Preparing Ultrasound Imaging Data for Artificial Intelligence Tasks: Anonymisation, Cropping, and Tagging},
    keywords     = {Ultrasound Imaging;DICOM;Anonymisation;Cropping;Tagging;Artificial Intelligence (AI)},
    booktitle    = {Proceedings of the 18th International Joint Conference on Biomedical Engineering Systems and Technologies (BIOSTEC 2025) - Volume 5: HEALTHINF},
    volume       = {5},
    year         = {2025},
    pages        = {xxx-xxx},
    publisher    = {SciTePress},
    organization = {INSTICC},
    doi          = {10.5220/001xxxxxxxxxxxxx},
    isbn         = {978-989-758-xxx-x},
    issn         = {2184-4305}
}
```

---
title: 'PyGMI - a python package for geoscience modelling and interpretation'
tags:
  - Python
  - geoscience
  - geophysics
  - remote sensing
authors:
  - name: Patrick Cole
    orcid: 0000-0002-3563-8704
    affiliation: 1
affiliations:
 - name: Council for Geoscience, South Africa
   index: 1
date: 11 March 2024
bibliography: paper.bib
---

# Summary

Python Geoscience Modelling and Interpretation (PyGMI) is an open-source software development project, working with a GUI, programmed in Python. The main aim of PyGMI is to provide a free geoscientific tool for processing, interpretation and modelling of geoscience data, including magnetic, gravity and remote sensing data. It also allows for research into better ways to process, analyse and model data and as such is continually updated to implement these advances.

Although is was originally intended to create voxel based three dimensional potential field models, it expanded to include tools for the processing and visualisation of raster data, import and visualisation of vector data (normally collected in surveys along lines), unsupervised and supervised cluster analysis, gravity processing, remote sensing processing and quality control tools for earthquake seismology. It is therefore a toolbox of numerous techniques to accomplish this. Examples of use include modelling of this Bushveld Igneous Complex [@COLE2021106219] and remote sensing in the Namaqualand region, South Africa [@Musekiwa2023].

# Statement of Need
Geophysical data provide geoscientists with the ability to create a picture of the subsurface prior to more expensive endeavours such a drilling or for further research using complementary data sets. The best way to present such a picture is through 3D models. The primary need for the PyGMI project was to provide open source modelling and image processing capabilities through a GUI. Geophysically, its strength is GUI based forward modelling, with limited inversion. It makes use of scientific libraries, such as SimPEG, [@cockett2015simpeg] and scikit-learn, [@Pedregosa2012] and is curently a GUI based alternative to libraries such as GemPy [@de_la_Varga_GemPy_1_0_open-source_2019], PyGimli [@Ruecker2017], and Harmonica [@fatiando_a_terra_project_2024_13308312].

# PyGMI Functionality
The original concept of PyGMI was a desire to have an effective 3D forward modelling package for magnetic and gravity data. There are a number of basic strategies to do this. One conventional approach follows the modelling of individual profiles, which are then “joined” up into 3D sections. Another is to form bodies from arbitrary polygonal shapes. However, using such methods, the time it takes to construct a 3D model can be prohibitive. Conventional polygonal based 3D modelling programs (3DS Max, Maya, Blender) are akin to CAD packages and require a steep learning curve, which is not always possible or tolerated by many scientists. PyGMI follows a voxel based approach (which is also used commonly in geophysical inversion), allowing the model to be ‘drawn’ in on model slices or layers, much like using an art program. Each voxel is assigned to a lithology from a user defined list, with its associate geophysical definitions.

There are many techniques which can be considered here [@Bhattacharyya1964; @Guptasarma1999; @Singh2001a; @Singh2001b; @Holstein2003]. In this case the technique by @Bhattacharyya1964 was used, being most applicable for voxel modelling (\autoref{fig:model}). The simplicity of the technique makes it well suited to rectangular prism calculations. It is described and developed into a Fortran routine, named ‘mbox’ by @Blakely1995 (pp. 200-201).
 
![(a) An example of a model created with PyGMI. (b) Top view of the model, the horizontal line is the profile being modelled. (c) The side view of the profile being modelled. The lines above the model represent the observed and calculated data. \label{fig:model}](img/figure1.jpg)

The PyGMI interface has been designed in a flow chart manner. This enables the user to see each step of the processing flow, useful in both debugging a process or teaching to new users. It also allows greater flexibility between modules.

Standard raster functions such as equations (making use of the NumExpr library, https://github.com/pydata/numexpr/), smoothing, normalisation, merging of datasets and reprojections [courtesy of @gdal2020; @gillies_2019] are included. Functions unique to potential fields such as tilt angle [@Cooper2006], visibility [@Cooper2005], reduction to the pole, sun shading [@Horn1981], IGRF calculations [@igrf2015, based on code by written by A. Zunde, USGS, S.R.C. Malin & D.R. Barraclough, Institute of Geological Sciences, United Kingdom and maintained by Stefan Maus, NOAA] have all been translated into or developed in python. The sun shading tool in particular allows for sunshade detail and light reflectance to be changed (\autoref{fig:sun}). These two parameters are not normally present in other software packages which usually only allow for the changing of sun dip and azimuth. Vector data, such as magnetic line data or geochemical data, can be imported courtesy of the GeoPandas library [@kelsey_jordahl_2020_3946761].

![Sunshading being displayed on the raster interpretation module. \label{fig:sun}](img/rasterinterp.png)

Gravity data processing has been developed according to the North American gravity database standards, as described by @Hinze2005. It allows for data to be imported from Scintrex CG-5 gravimeters and basic processing to Bouguer anomaly to be performed.

Earthquake seismology QC tools for the open source SEISAN platform [@Havskov2020] have been implemented. These include various plotting functions including RMS of time residuals, histograms of events vs time, b-values and error ellipses (\autoref{fig:seis}). Filtering of events can be performed via a filtering tool. A fault plane solution tool is also implemented, translated from MATLAB code written by Andy Michael, Chen Ji and Oliver Boyd and is capable of exporting results to the shapefile format.

![Error ellipses of seismic events shown on the QC tool. \label{fig:seis}](img/seisplots.png)

Crisp and fuzzy cluster analysis routines developed by @Paasche2009 in a joint project with the Council for Geoscience are provided, as well as supervised and unsupervised routines developed via the Sklearn library [@Pedregosa2012]. A graphical tool to see class representations via a scatterplot allows for relationships between scatterplots and the data to be examined interactively. Image segmentation following the method by @Baatz2000 has also been implemented.
 
Remote sensing tools are one of the major new focuses of PyGMI. Numerous major satellite formats can be read through the GDAL library via the  rasterio library [@gdal2020; @gillies_2019], including Sentinel-2, ASTER and Landsat, to name a few. PyGMI’s focus is to enable convenient calculation of a variety of measures, including predefined band ratios, condition indices, PCA (principal component analysis) and MNF [minimum noise fraction, @Green1988]. Change detection indices are also implemented as well as a viewer for change data visualisation. Finally, hyperspectral data analysis through feature detection is also possible [@Haest2012].

The PyGMI project therefore aims to continue to grow and support research and development in geosciences by providing easy to use tools with a GUI frontend.

# PyGMI Resources
Various resources including documentation and wiki are available:

- PyGMI Repository - https://github.com/Patrick-Cole/pygmi/
- PyGMI Documentation - https://patrick-cole.github.io/pygmi/
- PyGMI Installation Instructions - https://patrick-cole.github.io/pygmi/install.html/

# Acknowledgements

The author would like to acknowledge the Council for Geoscience for providing resources to allow for the continued development of PyGMI. In addition the author would like to thank all users for reporting bugs and suggesting useful features for PyGMI.

# References


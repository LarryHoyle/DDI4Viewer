# DDI4Viewer
A python (networkx)  application allowing views of the DDI4 model as an interactive network diagram

   Larry Hoyle, Institute for Policy and Social Research, University of Kansas

This application
  reads the current DDI4 Platform Independent Model (PIM) from the DDI4 Drupal site,
  parses that xmi file, 
  builds a networkx model of nodes and edges, 
  then calls networkx_viewer to allow browsing the model.

Nodes and edges have assigned attributes that can be seen in the browser as they are selected.

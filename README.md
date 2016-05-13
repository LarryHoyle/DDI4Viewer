# DDI4Viewer
A python (networkx)  application allowing views of the DDI4 model as an interactive network diagram

   Larry Hoyle, Institute for Policy and Social Research, University of Kansas

This application:
<ul>
  <li>reads the current DDI4 Platform Independent Model (PIM) from the DDI4 Drupal site,</li>
  <li>parses that xmi file, </li>
  <li>builds a networkx model of nodes and edges, </li>
  <li>then calls networkx_viewer to allow browsing the model.</li>
</ul>
Nodes and edges have assigned attributes that can be seen in the browser as they are selected.

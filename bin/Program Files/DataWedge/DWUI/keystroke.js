
c_keystroke_plugin=function()
{this.id=null;this.name=null;this.version=null;this.plugdom=null;this.m_xmldom=null;this.m_cfgdom=null;this.m_dfndom=null;this.m_xpathStack=new c_stack_obj();this.changed=0;this.mapId=0;};c_keystroke_plugin.prototype=new c_base_plugin();c_keystroke_plugin.prototype.constructor=c_keystroke_plugin;c_keystroke_plugin.prototype.parent=c_base_plugin.prototype;c_keystroke_plugin.prototype.updateKeymapList=function()
{var cfgmaps=selectNodes(this.m_cfgdom,"./Keymap/Mapping");var cfglen=cfgmaps.length;if(cfglen==0){return;}
var i,j,val,txt,kids,map,mapchld,klen;var keymap=selectNodes(this.m_xmldom,"./Keymap");mapchld=keymap[0].firstChild;while(mapchld!=null){mapchld.parentNode.removeChild(mapchld);mapchld=keymap[0].firstChild;}
i=0;while(i<cfglen)
{cfgmaps[i].setAttribute("id",i);kids=cfgmaps[i].childNodes;klen=kids.length;j=0;if(klen>0){map=this.m_xmldom.ownerDocument.createElement("Mapping");map.setAttribute("id",i);while(j<klen){mapchld=this.m_xmldom.ownerDocument.createElement(kids[j].nodeName);mapchld.setAttribute("type","integer");mapchld.setAttribute("min","0");switch(kids[j].nodeName){case"Char":mapchld.setAttribute("max","255");mapchld.setAttribute("name","Character code");break;case"Key":mapchld.setAttribute("max","65535");mapchld.setAttribute("name","Key code");break;}
val=kids[j].firstChild.nodeValue;txt=this.m_xmldom.ownerDocument.createTextNode(val);mapchld.appendChild(txt);map.appendChild(mapchld);j++;}
mapchld=this.m_xmldom.ownerDocument.createElement("Delete");mapchld.setAttribute("type","delete");map.appendChild(mapchld);keymap[0].appendChild(map);}
i++;}
this.mapId=i;map=this.m_xmldom.ownerDocument.createElement("Mapping");map.setAttribute("name","Add new");map.setAttribute("type","add");keymap[0].appendChild(map);};c_keystroke_plugin.prototype.handleUnknownNodeName=function(node,idx)
{var nname=node.nodeName;var nid=node.getAttribute("id");switch(nname)
{case"Keymap":this.updateKeymapList();break;}
return false;};c_keystroke_plugin.prototype.handleAddNew=function(node,idx)
{var xpth=this.m_xpathStack.getLastValue();var chrnode=this.m_xmldom.ownerDocument.createElement("Char");chrnode.setAttribute("name","Character code");chrnode.setAttribute("type","integer");chrnode.setAttribute("min","0");chrnode.setAttribute("max","255");var txt=this.m_xmldom.ownerDocument.createTextNode("0");chrnode.appendChild(txt);var keynode=this.m_xmldom.ownerDocument.createElement("Key");keynode.setAttribute("name","Key code");keynode.setAttribute("type","integer");keynode.setAttribute("min","0");keynode.setAttribute("max","65535");txt=this.m_xmldom.ownerDocument.createTextNode("0");keynode.appendChild(txt);var map=this.m_xmldom.ownerDocument.createElement("Mapping");map.setAttribute("id",this.mapId);map.appendChild(chrnode);map.appendChild(keynode);var delnode=this.m_xmldom.ownerDocument.createElement("Delete");delnode.setAttribute("type","delete");map.appendChild(delnode);node.parentNode.insertBefore(map,node.parentNode.lastChild);this.m_xpathStack.pop();xpth=this.m_xpathStack.getLastValue();var cfgnode=selectNodes(this.m_cfgdom,xpth);chrnode=this.m_cfgdom.ownerDocument.createElement("Char");txt=this.m_cfgdom.ownerDocument.createTextNode("0");chrnode.appendChild(txt);keynode=this.m_cfgdom.ownerDocument.createElement("Key");txt=this.m_cfgdom.ownerDocument.createTextNode("0");keynode.appendChild(txt);map=this.m_cfgdom.ownerDocument.createElement("Mapping");map.setAttribute("id",this.mapId);map.appendChild(chrnode);map.appendChild(keynode);cfgnode[0].appendChild(map);this.mapId++;this.changed++;this.refresh();return true;};c_keystroke_plugin.prototype.handleDelete=function(node,idx)
{this.m_xpathStack.pop();locationbar.pop();var xpth=this.m_xpathStack.getLastValue();var mid=node.parentNode.getAttribute("id");node.parentNode.parentNode.removeChild(node.parentNode);this.m_xpathStack.pop();xpth=xpth+"[@id='"+mid+"']";var cfgnode=selectNodes(this.m_cfgdom,xpth);cfgnode[0].parentNode.removeChild(cfgnode[0]);this.changed++;this.refresh();return true;};c_keystroke_plugin.prototype.checkInteger=function(value,id)
{var minval=this.nodeSelected.getAttribute("min");if(minval!=null){minval=parseInt(minval,10);}
var maxval=this.nodeSelected.getAttribute("max");if(maxval!=null){maxval=parseInt(maxval,10);}
if(value.validInteger())
{value=parseInt(value,10);if(value!=NaN)
{if(value>1E+15){alert("Value is too big.");return false;}
var minok=false;var maxok=false;if(minval==null){minok=true;}
else{if(value>=minval){minok=true;}}
if(maxval==null){maxok=true;}
else{if(value<=maxval){maxok=true;}}
if(minok&&maxok){if(this.nodeSelected.nodeName=="Char"){var cfgnode=selectNodes(this.m_cfgdom,".//Mapping[Char="+value+"]");if(cfgnode!=null){if(cfgnode.length>0){alert("The character code entered already has a mapping.");return false;}}}
this.setTextNodeValue(value);return true;}}}
if(maxval==null){alert("Value must be greater than "+minval);}
else if(minval==null){alert("Value must be less than "+maxval);}
else{alert("Value must be between "+minval+" and "+maxval);}
return false;};
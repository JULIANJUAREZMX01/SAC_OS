
c_adfplugin_plugin=function()
{this.id=null;this.name=null;this.version=null;this.actiondom=null;this.masterdom=null;this.plugdom=null;this.m_xmldom=null;this.m_cfgdom=null;this.m_dfndom=null;this.m_xpathStack=new c_stack_obj();this.changed=0;};c_adfplugin_plugin.prototype=new c_base_plugin();c_adfplugin_plugin.prototype.constructor=c_adfplugin_plugin;c_adfplugin_plugin.prototype.parent=c_base_plugin.prototype;c_adfplugin_plugin.default_Enabled=0;c_adfplugin_plugin.prototype.createBasePath=function(node,id)
{var rule=this.m_cfgdom.ownerDocument.createElement("Rule");rule.setAttribute("id",id);rule.setAttribute("name",id);var el=this.m_cfgdom.ownerDocument.createElement("Enabled");el.setAttribute("type","bool");var txt=this.m_cfgdom.ownerDocument.createTextNode("1");el.appendChild(txt);rule.appendChild(el);el=this.m_cfgdom.ownerDocument.createElement("Criteria");rule.appendChild(el);el=this.m_cfgdom.ownerDocument.createElement("Actions");var act=this.m_cfgdom.ownerDocument.createElement("Action");act.setAttribute("id","SEND");el.appendChild(act);rule.appendChild(el);node.appendChild(rule);};c_adfplugin_plugin.prototype.checkRule0=function(id)
{var rsnode=selectNodes(this.m_cfgdom,"./RuleSet");var existsRuleSet=false;if(rsnode!=null){if(rsnode.length>0){existsRuleSet=true;}}
if(!existsRuleSet){var root=selectNodes(this.m_cfgdom,".");rsnode=this.m_cfgdom.ownerDocument.createElement("RuleSet");root[0].appendChild(rsnode);}
rnode=selectNodes(this.m_cfgdom,"./RuleSet/Rule");var existsRule=false;if(rnode!=null){if(rnode.length>0){existsRule=true;}}
if(!existsRule&&!existsRuleSet){rsnode=selectNodes(this.m_cfgdom,"./RuleSet");this.createBasePath(rsnode[0],"Rule0");}};c_adfplugin_plugin.prototype.subload=function(id)
{this.checkRule0();this.masterdom=this.plugdom.documentElement.cloneNode(true);var url=htmlroot+"adf_actions.xml";var xml=geturl(url);if(xml!=null){if(xml.match("<?xml"))
{this.actiondom=loadXMLString(xml);return;}}
alert("Error loading action list.");};c_adfplugin_plugin.prototype.updateRulesList=function(node,idx)
{var xpth=this.m_xpathStack.getLastValue();var cfgrules=selectNodes(this.m_cfgdom,xpth.removePid().removeUid()+"/*");var cfglen=cfgrules.length;var xmlrules=selectNodes(this.m_xmldom,xpth);var chld=xmlrules[0].firstChild;while(chld!=null){chld.parentNode.removeChild(chld);chld=xmlrules[0].firstChild;}
if(cfglen>0){var i=0;var pid,pname,rule,enabled,txt,node;while(i<cfglen)
{pid=cfgrules[i].getAttribute("id");pname=cfgrules[i].getAttribute("name");if(pid==null){pid=this.getNewRuleName(0);pname=pid;cfgrules[i].setAttribute("id",pid);cfgrules[i].setAttribute("name",pname);this.changed++;}
if(pname==null){pname=pid;cfgrules[i].setAttribute("name",pname);this.changed++;}
rule=this.m_xmldom.ownerDocument.createElement("Rule");rule.setAttribute("id",pid);rule.setAttribute("name",pname);enabled=1;if(cfgrules[i].childNodes.length>0){enabled=cfgrules[i].firstChild.firstChild.nodeValue;if(enabled==null){enabled=1;}}
txt=this.m_xmldom.ownerDocument.createTextNode(enabled);node=this.m_xmldom.ownerDocument.createElement("Enabled");node.appendChild(txt);rule.setAttribute("enabled",enabled);rule.appendChild(node);xmlrules[0].appendChild(rule);i++;}}
rule=this.m_xmldom.ownerDocument.createElement("Rule");rule.setAttribute("type","add");rule.setAttribute("name","Add new");xmlrules[0].appendChild(rule);};c_adfplugin_plugin.prototype.createNewRule=function(name)
{rule=null;displayMessage("Loading rule, please wait...");rule=new c_rule_obj();var cfgNode=selectNodes(this.m_cfgdom,"./RuleSet");this.createBasePath(cfgNode[0],name);cfgNode=selectNodes(this.m_cfgdom,"./RuleSet/Rule[@id='"+name+"']");rule.setCfgBase(cfgNode[0]);var dfnNode=dwconfigdfn.m_xmldom.documentElement;rule.setDfnBase(dfnNode);rule.id=name;rule.name=name;rule.actiondom=this.actiondom;rule.changed++;rule.setGuvnor(this);classStack.push("rule");setTimeout("rule.load();",20);};c_adfplugin_plugin.prototype.existingRuleName=function(name)
{var node=selectNodes(this.m_cfgdom,"./RuleSet/Rule[@id='"+name+"']");if(node.length>0){return true;}
node=selectNodes(this.m_cfgdom,"./RuleSet/Rule[@name='"+name+"']");if(node.length>0){return true;}
return false;};c_adfplugin_plugin.prototype.checkUnknown=function(value,id)
{switch(id)
{case"Rule":name=value.trim();if(name.length==0)
alert("Invalid entry.  Please try adding some characters.");else{var ret=name.validString();if(!ret){alert(name+" contains invalid characters!");}
else{ret=!this.existingRuleName(name);if(!ret){alert(name+" is already taken!");}}
if(ret){redact=false;this.createNewRule(name);}}
break;}
return false;};c_adfplugin_plugin.prototype.getNewRuleName=function()
{var i=1,j;if(arguments.length>0){i=arguments[0];}
var pname,sname,pfname;var pnode=selectNodes(this.m_cfgdom,"./RuleSet/Rule");while(1)
{sname="Rule"+i;for(j=0;j<pnode.length;j++)
{pname=pnode[j].getAttribute("name");if(pname!=null){if(pname.toLowerCase()==sname.toLowerCase()){break;}}
pfname=pnode[j].getAttribute("id");if(pfname!=null){if(pfname.toLowerCase()==sname.toLowerCase()){break;}}}
if(j==pnode.length){break;}
i++;}
return sname;}
c_adfplugin_plugin.prototype.handleAddNew=function(node,idx)
{switch(node.nodeName)
{case"Rule":this.editBox(null,"New rule name:",this.getNewRuleName(),"plugin",node.nodeName);break;}
return true;};c_adfplugin_plugin.prototype.handleUnknownNodeName=function(node,idx)
{switch(node.nodeName)
{case"RuleSet":this.updateRulesList();break;case"Rule":var id=node.getAttribute("id");var name=node.getAttribute("name");if(id==null){return true;}
if(name==null){name=id;}
rule=new c_rule_obj();var dfnNode=selectNodes(this.m_dfndom,"./RuleSet/Rule");rule.setDfnBase(dfnNode[0]);var cfgNode=selectNodes(this.m_cfgdom,"./RuleSet/Rule[@id='"+id+"']");rule.setCfgBase(cfgNode[0]);rule.id=id;rule.name=name;rule.actiondom=this.actiondom;rule.setGuvnor(this);classStack.push("rule");displayMessage("Loading rule, please wait...");setTimeout("rule.load();",10);return true;break;}
return false;};c_adfplugin_plugin.prototype.removeRule=function(id)
{var cfgnode=selectNodes(this.m_cfgdom,"./RuleSet/Rule[@id='"+id+"']");cfgnode[0].parentNode.removeChild(cfgnode[0]);var xmlnode=selectNodes(this.m_xmldom,"./RuleSet/Rule[@id='"+id+"']");if(xmlnode.length>0){xmlnode[0].parentNode.removeChild(xmlnode[0]);}
this.changed++;};c_adfplugin_plugin.prototype.refresh=function()
{var xpath,nodeList;xpath=this.m_xpathStack.getLastValue();if(xpath=="./RuleSet"){this.updateRulesList();}
nodeList=selectNodes(this.m_xmldom,xpath+"/*");locationbar.refresh();this.updateMenu(nodeList);keytrap=true;};c_rule_obj=function()
{this.id=null;this.name=null;this.version=null;this.ruledom=null;this.actiondom=null;this.m_xmldom=null;this.m_cfgdom=null;this.m_dfndom=null;this.m_xpathStack=new c_stack_obj();this.changed=0;};c_rule_obj.prototype=new c_base_obj();c_rule_obj.prototype.constructor=c_rule_obj;c_rule_obj.prototype.parent=c_base_obj.prototype;c_rule_obj.prototype.addDevicesToCriteria=function()
{var crit=selectNodes(this.m_xmldom,".//Devices");var chld=crit[0].firstChild;while(chld!=null){chld.parentNode.removeChild(chld);chld=crit[0].firstChild;}
var inputPid=this.m_guvnor.m_guvnor.getInputPid();var deviceList=dwconfigdfn.getInputDeviceListByPluginId(inputPid);var devlen=deviceList.length;var i=0;var dev,devdfn,dcodrdfn,dcodrcfg,txt,declen,cfglen,node,dcodr,all,enode,decen;var txt,c,d,e,did,val,noen,nocfg;while(i<devlen)
{dev=this.m_xmldom.ownerDocument.createElement("Device");dev.setAttribute("id",deviceList[i].id);dev.setAttribute("desc",deviceList[i].desc);dev.setAttribute("name",deviceList[i].name);dev.setAttribute("devicetype",deviceList[i].devicetype);devdfn=selectNodes(dwconfigdfn.m_xmldom,"//PlugIns/Input/PlugIn/Device[@desc='"+deviceList[i].desc+"']");dcodrdfn=selectNodes(devdfn[0],"Decoders/Decoder");devcfg=selectNodes(this.m_cfgdom,"Criteria/Devices/Device[@desc='"+deviceList[i].desc+"']");dcodrcfg=null;nocfg=true;if(devcfg!=null){if(devcfg.length>0){dcodrcfg=selectNodes(devcfg[0],"Decoders/Decoder");nocfg=false;}}
cfglen=0;if(dcodrcfg!=null){cfglen=dcodrcfg.length;}
if(nocfg){devcfg=selectNodes(this.m_cfgdom,"Criteria/Devices");node=this.m_cfgdom.ownerDocument.createElement("Device");node.setAttribute("id",deviceList[i].id);node.setAttribute("desc",deviceList[i].desc);node.setAttribute("devicetype",deviceList[i].devicetype);devcfg[0].appendChild(node);devcfg=selectNodes(this.m_cfgdom,"Criteria/Devices/Device[@desc='"+deviceList[i].desc+"']");}
if(dcodrdfn!=null){if((declen=dcodrdfn.length)>0){node=this.m_xmldom.ownerDocument.createElement("Enabled");node.setAttribute("name","Included");node.setAttribute("type","bool");val=1;if(devcfg!=null){if(devcfg.length>0){noen=true;dcodr=selectNodes(devcfg[0],"Enabled");if(dcodr!=null){if(dcodr.length>0){if(dcodr[0].firstChild!=null){val=dcodr[0].firstChild.nodeValue;}
noen=false;}}
if(noen){noen=this.m_cfgdom.ownerDocument.createElement("Enabled");txt=this.m_cfgdom.ownerDocument.createTextNode(val);noen.appendChild(txt);devcfg[0].appendChild(noen);}}}
node.setAttribute("enabled",val);txt=this.m_xmldom.ownerDocument.createTextNode(val);node.appendChild(txt);dev.appendChild(node);node=this.m_xmldom.ownerDocument.createElement("Decoders");all=this.m_xmldom.ownerDocument.createElement("EnableAll");all.setAttribute("name","ALL");all.setAttribute("type","bool");dcodr=selectNodes(devcfg[0],"Decoders/EnableAll");val=1;if(dcodr!=null){if(dcodr.length>0){if(dcodr[0].firstChild!=null){val=dcodr[0].firstChild.nodeValue;}}}
txt=this.m_xmldom.ownerDocument.createTextNode(val);all.appendChild(txt);node.appendChild(all);d=0;while(d<declen)
{dcodr=this.m_xmldom.ownerDocument.createElement("Decoder");did=dcodrdfn[d].getAttribute("id");dcodr.setAttribute("id",did);dcodr.setAttribute("name",DECODER[did]);dcodr.setAttribute("type","bool");val=0;if(cfglen>0){c=0;while(c<cfglen){if(dcodrcfg[c].getAttribute("id")==did){if(dcodrcfg[c].firstChild!=null){val=dcodrcfg[c].firstChild.nodeValue;}
else{txt=this.m_cfgdom.ownerDocument.createTextNode(val);dcodrcfg[c].appendChild(txt);}
break;}
c++;}}
txt=this.m_xmldom.ownerDocument.createTextNode(val);dcodr.appendChild(txt);node.appendChild(dcodr);d++;}
dev.appendChild(node);}}
if(dev.childNodes.length==0){node=this.m_xmldom.ownerDocument.createElement("Enabled");node.setAttribute("name","Included");node.setAttribute("type","bool");val=1;if(devcfg!=null){if(devcfg.length>0){dcodr=selectNodes(devcfg[0],"Enabled");if(dcodr!=null){if(dcodr.length>0){if(dcodr[0].firstChild!=null){val=dcodr[0].firstChild.nodeValue;}}}}}
node.setAttribute("enabled",val);txt=this.m_xmldom.ownerDocument.createTextNode(val);node.appendChild(txt);dev.appendChild(node);}
crit[0].appendChild(dev);i++;}};c_rule_obj.prototype.updateActionList=function()
{var actxml=selectNodes(this.m_xmldom,"Actions");var chld=actxml[0].firstChild;while(chld!=null){chld.parentNode.removeChild(chld);chld=actxml[0].firstChild;}
var node,nchld,nid,act,aid,txt,cprms,cprms1,cprms1_txt,aprms,aprms1,aprms1_txt,match;var i=0,j,a,plen;var actcfg=selectNodes(this.m_cfgdom,"./Actions/Action");if(actcfg!=null){var actlen=actcfg.length;if(actlen>0){while(i<actlen)
{aid=actcfg[i].getAttribute("id");cprms=selectNodes(actcfg[i],"Param");cprms1=selectNodes(actcfg[i],"Param[@id='1']");cprms1_txt=null;if(cprms1!=null){if(cprms1.length>0){if(cprms1[0].firstChild!=null){cprms1_txt=cprms1[0].firstChild.nodeValue;}}}
act=selectNodes(this.actiondom,"//Action[@id='"+aid+"']");if(act!=null){a=0;while(a<act.length){aprms=selectNodes(act[a],"Param");if(aprms.length==cprms.length){match=true;if(aid=="PADLEFT"){aprms1=selectNodes(act[a],"Param[@id='1']");aprms1_txt=null;if(aprms1!=null){if(aprms1.length>0){if(aprms1[0].firstChild!=null){aprms1_txt=aprms1[0].firstChild.nodeValue;}}}
if(aprms1_txt!=cprms1_txt){match=false;}}
if(match){node=act[a].cloneNode(true);node.removeAttribute("type");node.setAttribute("uid",i);j=0;chld=actcfg[i].firstChild;while(chld!=null){if(chld.nodeName=="Param"){if(chld.childNodes.length>0){aid=chld.getAttribute("id");nchld=node.firstChild;while(nchld!=null){nid=nchld.getAttribute("id");if(aid==nid){if(nchld.childNodes.length>0){nchld.firstChild.nodeValue=chld.firstChild.nodeValue;}
else{txt=this.m_xmldom.ownerDocument.createTextNode(chld.firstChild.nodeValue);nchld.appendChild(txt);}}
nchld=nchld.nextSibling;}}}
chld=chld.nextSibling;}
actxml[0].appendChild(node);break;}}
a++;}}
i++;}}}
node=this.m_xmldom.ownerDocument.createElement("Action");node.setAttribute("id","add");node.setAttribute("name","Add new");node.setAttribute("type","add");actxml[0].appendChild(node);};c_rule_obj.prototype.load=function()
{var url=htmlroot+"adf_rule.xml";var xml=geturl(url);if(xml!=null){if(xml.match("<?xml"))
{this.ruledom=loadXMLString(xml);this.m_xmldom=selectNodes(this.ruledom,"/Rule")[0];this.show();return;}}
alert("Error loading rule template.");this.onSelect(666);};c_rule_obj.prototype.addAvailableActions=function(node)
{var act=selectNodes(this.actiondom,"/Actions/Action");var chld;for(i=0;i<act.length;i++){chld=act[i].cloneNode(false);node.appendChild(chld);}};c_rule_obj.prototype.handleAddNew=function(node,idx)
{switch(node.nodeName)
{case"Action":var type=node.getAttribute("type");if(type=="add"){var pn=node.parentNode;if(pn.nodeName=="Action"){if(pn.getAttribute("type")==node.getAttribute("type")){var aid=node.getAttribute("id");this.m_xpathStack.pop();this.m_xpathStack.pop();locationbar.pop();var xpth=this.m_xpathStack.getLastValue();var cfgnode=selectNodes(this.m_cfgdom,xpth.removePid().removeUid());var act=this.m_cfgdom.ownerDocument.createElement("Action");act.setAttribute("id",aid);var action=selectNodes(this.actiondom,"/Actions/Action["+(idx+1)+"]");var prm=selectNodes(action[0],"Param");var i=0,p,txt,val;while(i<prm.length){p=this.m_cfgdom.ownerDocument.createElement("Param");p.setAttribute("id",prm[i].getAttribute("id"));if(prm[i].firstChild!=null){val=prm[i].firstChild.nodeValue;txt=this.m_cfgdom.ownerDocument.createTextNode(val);p.appendChild(txt);}
act.appendChild(p);i++;}
cfgnode[0].appendChild(act);this.changed++;this.updateActionList();this.updateActionUids();this.menupage=0;this.refresh();}}
else{if(node.childNodes.length==0){this.addAvailableActions(node);}
return false;}}
break;}
return true;};c_rule_obj.prototype.handleUnknownNodeName=function(node,idx)
{switch(node.nodeName)
{case"Criteria":this.addDevicesToCriteria();break;case"Actions":this.updateActionList();break;}
return false;};c_rule_obj.prototype.updateActionUids=function()
{var xmlnode=selectNodes(this.m_xmldom,"./Actions/Action");var len=xmlnode.length;var i=0;while(i<len){xmlnode[i].setAttribute("uid",i);i++;}};c_rule_obj.prototype.removeAction=function(node,idx)
{var xpth=this.m_xpathStack.get2ndToLastValue();var pn=node.parentNode;var uid=pn.getAttribute("uid");if(uid==null)alert("uid is null");var cfgacts=selectNodes(this.m_cfgdom,xpth.removePid().removeUid());var cfgact=cfgacts[0].getElementsByTagName("Action");var len=cfgact.length;if(len>uid){cfgact[uid].parentNode.removeChild(cfgact[uid]);pn.parentNode.removeChild(pn);this.changed++;this.updateActionUids();}
else alert("uid["+uid+"] >= actions["+cfgact.length+"]");};c_rule_obj.prototype.handleDelete=function(node,idx)
{this.m_xpathStack.pop();switch(node.parentNode.nodeName)
{case"Rule":this.m_guvnor.removeRule(this.id);keytrap=true;setTimeout("onSelect(666);",20);break;case"Action":this.removeAction(node,idx);keytrap=true;setTimeout("onSelect(666);",20);break;default:alert(node.parentNode.nodeName);}
return true;};c_rule_obj.prototype.checkRename=function(value,id)
{var name=value.trim();if(name.length==0)
{alert("Invalid entry.  Please try adding some characters.");return false;}
var chk=false,dup=true;var errmsg=" contains invalid characters!";chk=name.validString();if(chk){dup=this.m_guvnor.existingRuleName(name);}
if(!chk){alert(name+errmsg);}
else{if(dup){alert(name+" is already taken!");return false;}
locationbar.setLastValue(name);var node=selectNodes(this.m_cfgdom,".");node[0].setAttribute("id",name);node[0].setAttribute("name",name);this.changed++;return true;}
return false;};c_rule_obj.prototype.updateNodeListValues=function(xpath,nodeList)
{var xpth=xpath;var i=0;var len=nodeList.length;var xmlNode,dfnNode,cfgNode,nname,node,xid,xdesc,xdevicetype,xp,dxp,val,pid,txt;for(i=0;i<len;i++)
{xmlNode=nodeList[i];if(xmlNode.nodeType==3){continue;}
if(xmlNode.getAttribute("type")=="add"){continue;}
xdesc=null;if(xmlNode.nodeName!="PlugIn"){xdesc=xmlNode.getAttribute("desc");}
xid=xmlNode.getAttribute("id");dxp=xpth.removePid().convertUid();xp=dxp+"/"+xmlNode.nodeName;if(xmlNode.nodeName=="Param"){if(xmlNode.parentNode.nodeName=="Action"){pid=xmlNode.parentNode.getAttribute("id");dxp=xpth.removeUid()+"[@id='"+pid+"']";}}
dxp=dxp+"/"+xmlNode.nodeName;if(xid!=null){xp+="[@id='"+xid+"']";dxp+="[@id='"+xid+"']";}
if(xdesc!=null){xp+="[@desc='"+xdesc+"']";}
dfnNode=selectNodes(this.m_dfndom,dxp);cfgNode=selectNodes(this.m_cfgdom,xp);if(dfnNode==null){;}
else if(dfnNode.length==0){if(this.removeNode(xmlNode)){nodeList=selectNodes(this.m_xmldom,xpath+"/*");len=nodeList.length;;i--;continue;}}
var crnew=false;if(cfgNode==null){crnew=true;}
else if(cfgNode.length==0){crnew=true;}
if(crnew){nname=xmlNode.nodeName;if(this.skipConfigNode(xmlNode)){return;}
cfgNode=selectNodes(this.m_cfgdom,xpth.removePid().convertUid());if(cfgNode==null){}
if(cfgNode.length==0){xp=xpth.removePid().removeUid();var fs=0,lp=0;while(fs>=0){lp=fs;fs=xp.indexOf("/",fs+1);}
if(lp>0){cfgNode=selectNodes(this.m_cfgdom,xp.substr(0,lp));var ndname=xp.substr(lp+1);node=this.m_cfgdom.ownerDocument.createElement(ndname);cfgNode[0].appendChild(node);cfgNode=selectNodes(this.m_cfgdom,xp);}}
node=cfgNode[0].ownerDocument.createElement(nname);if(xid!=null){node.setAttribute("id",xid);}
xdesc=xmlNode.getAttribute("desc");if(xdesc!=null){node.setAttribute("desc",xdesc);}
xdevicetype=xmlNode.getAttribute("devicetype");if(xdevicetype!=null){node.setAttribute("devicetype",xdevicetype);}
if(xmlNode.getAttribute("type")=="fixed"){val=xmlNode.getAttribute("value");node.setAttribute("value",val);}
if(nname=="Decoder"){txt=cfgNode[0].ownerDocument.createTextNode("0");node.appendChild(txt);}
cfgNode[0].appendChild(node);xp=xpth.removePid().convertUid()+"/"+xmlNode.nodeName;if(xid!=null){xp+="[@id='"+xid+"']";}
if(xdesc!=null){xp+="[@desc='"+xdesc+"']";}
cfgNode=selectNodes(this.m_cfgdom,xp);}
if(dfnNode==null){this.updateNodeValues(xmlNode,cfgNode[0],null);}
else{this.updateNodeValues(xmlNode,cfgNode[0],dfnNode[0]);}}};c_rule_obj.prototype.handleAction=function(node,idx)
{if(node.parentNode.parentNode.nodeName=="Action"){locationbar.pop();}
return this.parent.handleAction.call(this,node,idx);return true;};
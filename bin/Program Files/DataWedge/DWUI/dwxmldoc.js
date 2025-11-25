function removeWhitespace(str){
    var re=/[>]([ \t\r\n]*)[<]/g;
    return str.replace(re, "><");
}

String.prototype.removeWhitespace = function()
{
    var re=/[>]([ \t\r\n]*)[<]/g;
    return this.replace(re, "><");
}

function newXMLDoc()
{
	try
	{ // Internet Explorer
		xmlDoc = new ActiveXObject("MSXML2.DOMDocument");
		return(xmlDoc);
	}
	catch(e)
	{
		try
		{ // Firefox, Mozilla, Opera, etc
			xmlDoc = document.implementation.createDocument("","",null);
			return(xmlDoc);
		}
		catch(e)
		{
			alert(e.message);
		}
	}
	return(null);
}

function loadXMLDoc(dname)
{
	try
	{ // Internet Explorer
		xmlDoc = new ActiveXObject("MSXML2.DOMDocument");
	}
	catch(e)
	{
		try
		{ // Firefox, Mozilla, Opera, etc
			xmlDoc = document.implementation.createDocument("","",null);
		}
		catch(e)
		{
			alert(e.message);
		}
	}
	
	try
	{
		xmlDoc.async = false;
		xmlDoc.validateOnParse = false;
		xmlDoc.resolveExternals = false;
		xmlDoc.preserveWhiteSpace = false;
		xmlDoc.load(dname);
		return(xmlDoc);
	}
	catch(e)
	{
		alert(e.message);
	}
	return(null);
}

function loadXMLString(txt)
{
	var xmlDoc;
	try
	{ // Internet Explorer
		xmlDoc = new ActiveXObject("MSXML2.DOMDocument");
		xmlDoc.async = false;
		xmlDoc.validateOnParse = false;
		xmlDoc.resolveExternals = false;
		xmlDoc.preserveWhiteSpace = false;
		xmlDoc.loadXML(txt);
		return(xmlDoc);
	}
	catch(e)
	{
		try
		{ // Firefox, Mozilla, Opera, etc
			txt = removeWhitespace(txt);
			parser = new DOMParser();
			xmlDoc = parser.parseFromString(txt,"text/xml");
			return(xmlDoc);
		}
		catch(e)
		{
			alert(e.message);
		}
	}
	return(null);
}

function writeMenu()
{
	var kt = keytrap;
	keytrapajax = false;
	var n = menu[0].length;
	var xml = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n<DWUI>\r\n";
	for (var i=0; i<n; i++)
	{
		//xml += menu[0][i].xml;
		xml += xml2str(menu[0][i]);
	}
	xml += "\r\n</DWUI>"
	var ret = puturl("/config/dwui_menu.xml", xml);
	if (ret == null) alert("Error writing menu. DataWedge may not be running.");
	keytrap = kt;
}

function reloadMenu()
{
	var resp = geturl("/config/dwui_menu.xml");
	if (resp.length == 0) return;
	if (resp.match("<?xml") == null) return;
		
	var xml = loadXMLString(resp);
	menu[0] = xml.documentElement.childNodes;
	//menu[1] = menu[0][0].childNodes;
	if (dwuiView == viewType.basic) 
		//onSelect(1);
		menu[1] = menu[0][1].childNodes;
	else {
		menu[1] = menu[0][0].childNodes;
		menu[2] = menu[1][0].childNodes;
		//onSelect(0);
	}
}

var profileXml;
function createProfileString(name, xmlroot)
{
	//profileXml = new ActiveXObject("MSXML2.DOMDocument");
	profileXml = newXMLDoc();
	profileXml.async = false;
	profileXml.preserveWhiteSpace = true;	//false;
	var newel = xmldocblank.createElement("DWProfileConfig");
	profileXml.appendChild(newel);
	var newatt = profileXml.createAttribute("name");
	newatt.nodeValue = name;
	var px = selectNodes(profileXml, "/DWProfileConfig")[0];
	px.setAttributeNode(newatt);
	newel = xmldocblank.createElement("PlugIns");
	px.appendChild(newel);
	newel = xmldocblank.createElement("DataPaths");
	px.appendChild(newel);
	newel = xmldocblank.createElement("Input");
	px = selectNodes(profileXml, "/DWProfileConfig/PlugIns")[0];
	px.appendChild(newel);
	newel = xmldocblank.createElement("Output");
	px.appendChild(newel);
	newel = xmldocblank.createElement("Process");
	px.appendChild(newel);
	var ppin = selectNodes(dwconfigdfn, "/DWConfigDfn/PlugIns/Process/PlugIn");
	var i;
	px = selectNodes(profileXml, "/DWProfileConfig/PlugIns/Process")[0];
	for (i=0; i<ppin.length; i++)
	{
		newel = xmldocblank.createElement("PlugIn");
		newel.setAttribute("id", ppin[i].getAttribute("id"));
		px.appendChild(newel);
	}
	var plugsrc, plugdest;
	plugsrc = selectNodes(xmlroot, "//Profile[@name='"+name+"']/Input/PlugIn");
	plugdest = selectNodes(profileXml, "/DWProfileConfig/PlugIns/Input");
	walkXmlTree(plugsrc, plugdest, 0);
	plugsrc = selectNodes(xmlroot, "//Profile[@name='"+name+"']/Output/PlugIn");
	plugdest = selectNodes(profileXml, "/DWProfileConfig/PlugIns/Output");
	walkXmlTree(plugsrc, plugdest, 0);
	plugsrc = selectNodes(xmlroot, "//Profile[@name='"+name+"']/DataPaths/Path");
	plugdest = selectNodes(profileXml, "/DWProfileConfig/DataPaths");
	walkXmlTree(plugsrc, plugdest, 0);
	//return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n" + profileXml.xml;
	return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n" + xml2str(profileXml);
}

function walkXmlTree(srcnode, destnode, index)
{
	var n, nlen, nchildren;
	var el, tn, attr, ptype, tval;
	var nname;

	nlen = srcnode.length;
	if (nlen > 0)
	{
		for (n=0; n<nlen; n++)
		{
			if (srcnode[n].nodeType != nodeType.Element)
			{
				if (srcnode[n].nodeType == nodeType.Text)
				{
					len = destnode.length;
					//tn = profileXml.createTextNode(srcnode[n].nodeValue);
					tn = xmldocblank.createTextNode(srcnode[n].nodeValue);
					if (index < len) {
						destnode[index].appendChild(tn);
					}
					else
						destnode[len-1].appendChild(tn);
				}
				return false;
			}
			nname = srcnode[n].nodeName;
			if (nname == "Move") continue;
			if (nname == "Rename") continue;
			if (nname == "Decoder")
				if (srcnode[n].childNodes[0].nodeType == nodeType.Text)
					if (srcnode[n].childNodes[0].nodeValue == "0") continue;
			el = xmldocblank.createElement(nname);
			attr = selectNodes(srcnode[n], "@id");
			if (attr.length > 0)
			{
				ptype = srcnode[n].parentNode.getAttribute("type");
				if (ptype == "add") continue;
				if (ptype == "delete") continue;
				if (ptype == "hidden") continue;
				if (ptype == "fixed")
				{
					tval = srcnode[n].parentNode.getAttribute("value");
					if (attr[0].nodeValue != tval) continue;
				}
				el.setAttribute("id", attr[0].nodeValue);
				attr = selectNodes(srcnode[n], "@value");
				if (attr.length > 0)
				{
					//tn = profileXml.createTextNode(attr[0].nodeValue);
					tn = xmldocblank.createTextNode(attr[0].nodeValue);
					el.appendChild(tn);
					destnode[destnode.length-1].appendChild(el);
					continue;
				}
				attr = selectNodes(srcnode[n], "@desc");
				if (attr.length > 0)
					el.setAttribute("desc", attr[0].nodeValue);
			}
			else
			{
				ptype = srcnode[n].getAttribute("type");
				switch(ptype)
				{
				case "add":
				case "action":
				case "delete":
				case "hidden":
					continue;
					break;
				case "fixed":
					el.setAttribute("value", srcnode[n].getAttribute("value"));
					break;
				case "select":
					attr = selectNodes(srcnode[n], "@value");
					if (attr.length > 0)
					{
						if (srcnode[n].nodeName == "Plugin")
						{
							el.setAttribute("id", srcnode[n].getAttribute("value"));
							destnode[destnode.length-1].appendChild(el);
							continue;
						}
						//tn = profileXml.createTextNode(attr[0].nodeValue);
						tn = xmldocblank.createTextNode(attr[0].nodeValue);
						el.appendChild(tn);
						destnode[destnode.length-1].appendChild(el);
						continue;
					}
					break;
				}
			}
			destnode[destnode.length-1].appendChild(el);
			nchildren = srcnode[n].childNodes.length;
			if (nchildren > 0)
			{
				walkXmlTree(srcnode[n].childNodes, destnode[destnode.length-1].childNodes, n);
			}
		}
	}
	return true;
}

function selectNodes(xmlDoc, xpath)
{
	try
	{
		return xmlDoc.selectNodes(xpath);
	}
	catch(e)
	{
		try
		{
			var oEvaluator = new XPathEvaluator();
			var oResult = oEvaluator.evaluate(xpath, xmlDoc, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
			var aNodes = new Array();
			if (oResult != null) {
				var oElement = oResult.iterateNext();
				while(oElement) {
					aNodes.push(oElement);
					oElement = oResult.iterateNext();
				}
			}
			return aNodes;

			//var nsResolver = xmlDoc.createNSResolver( xmlDoc.ownerDocument == null ? xmlDoc.documentElement : xmlDoc.ownerDocument.documentElement);
			//var res = xmlDoc.evaluate(xpath, xmlDoc, nsResolver, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
			//return res;
		}
		catch(e)
		{
			//alert("selectNodes() failed.");
			return null;
		}
	}
	return null;
}

function xml2str(xmlNode) {
	try {
		// Gecko-based browsers, Safari, Opera.
		var izer = new XMLSerializer();
		return izer.serializeToString(xmlNode);
	}
	catch (e) {
		try {
			// Internet Explorer.
			return xmlNode.xml;
		}
		catch (e) {  
			//Other browsers without XML Serializer
			alert('Xmlserializer not supported');
		}
	}
	return false;
}

function writeDWConfig()
{
	var kt = keytrap;
	keytrap = false;
	rebuildActiveProfileList();
	var profile = new Array();
	profile = menu[0][0].getElementsByTagName("Profile");
	var _dwprfl = new Array();
	dwprfl = dwconfig.getElementsByTagName("Profile");
	var ap = menu[0][0].getElementsByTagName("ActiveProfile")[0];
	var i,j,k;
	var apps, app, papp, val, tn, name;
	var dwpname, dwpfname, pname, pfname;
	var apset = false;
	for (i=0; i<dwprfl.length; i++)
	{
		dwpname = dwprfl[i].getAttribute("name");
		dwpfname = dwprfl[i].getAttribute("filename");
		for (j=0; j<profile.length; j++)
		{
			pname = profile[j].getAttribute("name");
			pfname = profile[j].getAttribute("filename");
			if (dwpfname == pfname)
			{
				dwprfl[i].setAttribute("name", pname);
				dwprfl[i].setAttribute("enabled", profile[j].childNodes[0].childNodes[0].nodeValue);
				if (ap.getAttribute("value") == dwpfname)
				{
					dwprfl[i].setAttribute("active", 1);
					apset = true;
				}
				else 
					dwprfl[i].setAttribute("active", 0);
				if (dwpfname == "Default") continue;
				if (dwpfname == "Profile0") continue;
				apps = dwprfl[i].getElementsByTagName("Applications");
				if (apps.length > 0) apps[0].parentNode.removeChild(apps[0]);
				apps = xmldocblank.createElement("Applications");
				papp = profile[j].getElementsByTagName("Application");
				for (k=0; k<papp.length; k++)
				{
					if (papp[k].attributes.length == 0) continue;
					val = papp[k].getAttribute("value");
					name = papp[k].getAttribute("name");
					if (val == null) continue;
					app = xmldocblank.createElement("Application");
					tn = xmldocblank.createTextNode(name);
					//app.text = val;
					app.appendChild(tn);
					apps.appendChild(app);
				}
				dwprfl[i].appendChild(apps);
				break;
			}
		}
	}
	if (!apset)
		if (profile.length > 0)
			dwprfl[0].setAttribute("active", 1);
	
	var aps = menu[0][0].getElementsByTagName("AutoProfileSwitching")[0];
	var dwaps = dwconfig.getElementsByTagName("AutoProfileSwitching")[0];
	//dwaps.childNodes[0].nodeValue = aps.childNodes[0].nodeValue;
	dwaps.childNodes[0].nodeValue = aps.getAttribute("value");
			
	updateDWConfigLogSettings();
	//var ret = puturl("/config/DWConfig.xml", dwconfig.xml);
	var ret = puturl("/config/DWConfig.xml", xml2str(dwconfig));
	keytrap = kt;
	if (ret == null) alert("Error writing configuration.  DataWedge may not be running.");
}

function updateDWConfigLogSettings()
{
	var newnode, newtext, val;
	var log = selectNodes(dwconfig.documentElement, "//Log")[0];
	var logdest = selectNodes(dwconfig.documentElement, "//LogSize")[0];
	var logsrc = selectNodes(menu[0][0], "//LogSize")[0];
	val = logsrc.getAttribute("value");
	if (logdest == null)
	{
		newnode = xmldocblank.createElement("LogSize");
		newtext = xmldocblank.createTextNode(val);
		newnode.appendChild(newtext);
		log.appendChild(newnode);
	}
	else
		logdest.childNodes[0].nodeValue = val;
	logdest = selectNodes(dwconfig.documentElement, "//LogPath")[0];
	logsrc = selectNodes(menu[0][0], "//LogPath")[0];
	val = logsrc.childNodes[0].nodeValue;
	if (logdest == null)
	{
		newnode = xmldocblank.createElement("LogPath");
		newtext = xmldocblank.createTextNode(val);
		newnode.appendChild(newtext);
		log.appendChild(newnode);
	}
	else
		logdest.childNodes[0].nodeValue = val;
	logdest = selectNodes(dwconfig.documentElement, "//TempPath")[0];
	logsrc = selectNodes(menu[0][0], "//TempPath")[0];
	val = logsrc.childNodes[0].nodeValue;
	if (logdest == null)
	{
		newnode = xmldocblank.createElement("TempPath");
		newtext = xmldocblank.createTextNode(val);
		newnode.appendChild(newtext);
		log.appendChild(newnode);
	}
	else
		logdest.childNodes[0].nodeValue = val;
	logdest = selectNodes(dwconfig.documentElement, "//LogLevel")[0];
	logsrc = selectNodes(menu[0][0], "//LogLevel")[0];
	val = logsrc.getAttribute("value");
	if (logdest == null)
	{
		newnode = xmldocblank.createElement("LogLevel");
		newtext = xmldocblank.createTextNode(val);
		newnode.appendChild(newtext);
		log.appendChild(newnode);
	}
	else
		logdest.childNodes[0].nodeValue = val;
}

function moveNode(node, dir)
{
	var numnodes = node.parentNode.childNodes.length;
	if (numnodes < 2) return;
	var n1 = node.parentNode;
	var n2, n3, ntype;
	if (dir.toLowerCase() == "up")
	{
		n2 = n1.previousSibling;
		if (n2 == null) return;
		n1.parentNode.insertBefore(n1, n2);
	}
	if (dir.toLowerCase() == "down")
	{
		n2 = n1.nextSibling;
		if (n2 == null) return;
		ntype = n2.getAttribute("type");
		if (ntype != null)
			if (ntype == "add") return;
		n2.parentNode.insertBefore(n2, n1);
	}
}

function rebuildActiveProfileList()
{
	var ap = menu[0][0].getElementsByTagName("ActiveProfile")[0];
	var newap = xmldocblank.createElement("ActiveProfile");
	newap.setAttribute("name", ap.getAttribute("name"));
	newap.setAttribute("type", ap.getAttribute("type"));
	newap.setAttribute("oid", 0);
	newap.setAttribute("value", ap.getAttribute("value"));
	var prfl = menu[0][0].getElementsByTagName("Profile");
	var oidset = false;
	for (var i=0; i<prfl.length; i++)
	{
		if (prfl[i].getAttribute("type") != null) continue;
		var newopt = xmldocblank.createElement("option");
		var name = prfl[i].getAttribute("name");
		var filename = prfl[i].getAttribute("filename");
		newopt.setAttribute("id", i);
		newopt.setAttribute("name", name);
		newopt.setAttribute("value", filename);
		if (ap.getAttribute("value") == filename) {
			newap.setAttribute("oid", i);
			oidset = true;
		}
		newap.appendChild(newopt);
	}
	if (!oidset) newap.setAttribute("value", prfl[0].getAttribute("filename"));
	ap.parentNode.replaceChild(newap, ap);
}

function enableAllDecoders(idx)
{
	menu[menulevel][idx].firstChild.nodeValue = 1;
	menu[menulevel][idx].parentNode.getElementsByTagName("DisableAll")[0].firstChild.nodeValue = 0;
	var e = selectNodes(menu[menulevel][idx].parentNode, "Decoder/Enabled");
	for (var i=0; i<e.length; i++)
	{
		e[i].firstChild.nodeValue = 1;
	}
	updateMenu();
}

function disableAllDecoders(idx)
{
	menu[menulevel][idx].firstChild.nodeValue = 1;
	menu[menulevel][idx].parentNode.getElementsByTagName("EnableAll")[0].firstChild.nodeValue = 0;
	var e = selectNodes(menu[menulevel][idx].parentNode, "Decoder/Enabled");
	for (var i=0; i<e.length; i++)
	{
		e[i].firstChild.nodeValue = 0;
	}
	updateMenu();
}


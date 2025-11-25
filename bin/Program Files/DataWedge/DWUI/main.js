// main

var viewType = {
	basic: 0,
	advanced: 1
}

var MAX_PATH = 260;
var MAX_PROFILENAME = 32;
var xmldocblank;
var dwconfig;
var dwconfigdfn;
var rootmenu;
var uiProfileTemplate;
var uiDatapathTemplate;
var profile = new Array();
var profileConfig = new Array();
var plugin = new Array();
var uiPlugin = new Array();
var uiFeedback;	// = new Array();
var adfrule;
var adfaction;
var numProfiles = 0;
var idxProfile = 0;
var numPlugins = 0;
var idxPlugin = 0;
var numFeedback = 0;
var menuLoaded = false;
var setTimeouts = 0;
var dwuiView = viewType.advanced;

function statusBar(txt)
{
	document.getElementById("bottompanel").innerHTML = txt;
}

function main(){
	document.getElementById("toppanel").innerHTML = "Initialising, please wait.";
	if (location.href.indexOf("?mode=basic") > 0) dwuiView = viewType.basic;
	else if (location.href.indexOf("?mode=advanced") > 0) dwuiView = viewType.advanced;
	xmldocblank = newXMLDoc();
	//if (isIEMobile())
	//	SimpleAJAXCall(urlex("/dwui/dwui.xml?pie=fullscreen"), cbMain, "", "dwui");
	//else
		SimpleAJAXCall(urlex("/dwui/dwui.xml"), cbMain, "", "dwui");
	SimpleAJAXCall(urlex("/dwui/dwui_profile.xml"), cbMain, "", "dwui_profile");
	SimpleAJAXCall(urlex("/dwui/dwui_datapath.xml"), cbMain, "", "dwui_datapath");
	SimpleAJAXCall(urlex("/dwui/dwui_ngdwfeedbak.xml"), cbMain, "", "dwui_ngdwfeedbak");
	SimpleAJAXCall(urlex("/config/DWConfig.xml"), cbMain, "", "dwconfig");
	SimpleAJAXCall(urlex("/config/DWConfigDfn.xml"), cbMain, "", "dwconfigdfn");
	SimpleAJAXCall(urlex("/config/dwui_menu.xml"), cbMain, "", "dwui_menu");
	progressBarCreate(12);
	statusBar("Getting dwui, dwui_profile, DWConfig, DWConfigDfn");
}

function cbMain(xml, param)
{
	//if (xml == null) return;
	//var node = xml.documentElement.nodeName;
	//var s = xml.indexOf("<",5) + 1;
	//var e = xml.indexOf(" ", s);
	//var e2 = xml.indexOf(">", s);
	//if (e2 < e) e = e2;
	//var node = xml.substring(s, e);
	progressBarStepIt2();
	switch(param)
	{
	case "dwui":
		if (xml == null) return;
		if (xml.length == 0) return;
		rootmenu = loadXMLString(xml);
		statusBar("Got "+param);
		break;
	case "dwui_profile":
		if (xml == null) return;
		if (xml.length == 0) return;
		uiProfileTemplate = loadXMLString(xml);
		statusBar("Got "+param);
		break;
	case "dwui_datapath":
		if (xml == null) return;
		if (xml.length == 0) return;
		uiDatapathTemplate = loadXMLString(xml);
		statusBar("Got "+param);
		break;
	case "dwui_ngdwfeedbak":
		if (xml == null) return;
		if (xml.length == 0) return;
		uiFeedback = loadXMLString(xml);
		statusBar("Got "+param);
		break;
	case "dwconfig":
		if (xml == null) return;
		if (xml.length == 0) return;
		dwconfig = loadXMLString(xml);
		statusBar("Got "+param);
		//setTimeout("getProfiles();", 10);
		setTimeout("setActiveProfileSwitching();", 50);
		break;
	case "dwconfigdfn":
		if (xml == null) return;
		if (xml.length == 0) return;
		dwconfigdfn = loadXMLString(xml);
		statusBar("Got "+param);
		//setTimeout("getPlugins();", 10);
		setTimeout("addPluginVersionInfo();", 10);
		//setTimeout("setDeviceInfo();", 10);
		setTimeout("setLogValues();", 10);
		break;
	case "dwui_menu":
		if (xml != null)
			if (xml.length > 0)
			{
				rootmenu = loadXMLString(xml);
				statusBar("Got "+param);
				menuLoaded = true;
				//loadRootMenu(rootmenu.documentElement.childNodes);
				setTimeout("wait4setTimeouts();", 500);
				//return;
			}
		setTimeouts = 3;
		setTimeout("getProfiles();", 10);
		setTimeout("getPlugins();", 200);
		setTimeout("setFeedbackDefaults(uiFeedback);", 250);
		break;
	default:
		alert(node);
	}
}

function wait4setTimeouts()
{
	if (setTimeouts > 0)
	{
		setTimeout("wait4setTimeouts();", 500);
	}
	else
	{
		loadRootMenu(rootmenu.documentElement.childNodes);
	}
}

function add2Settings(prfl)
{
	var ap = rootmenu.getElementsByTagName("ActiveProfile")[0];
	for (i=0; i<numProfiles; i++)
	{
		var opt = xmldocblank.createElement("option");
		opt.setAttribute("id", i);
		opt.setAttribute("name", prfl[i].getAttribute("name"));
		opt.setAttribute("value", prfl[i].getAttribute("name"));
		ap.appendChild(opt);
		if (prfl[i].getAttribute("active") == 1)
		{
			ap.setAttribute("oid", i);
			ap.setAttribute("value", prfl[i].getAttribute("name"));
		}
	}
}

function getProfiles()
{
	if (menuLoaded) {
		setTimeouts--;
		return;
	}
	profile = dwconfig.getElementsByTagName("Profile");
	numProfiles = profile.length;
	add2Settings(profile);
	var url;
	for (i=0; i<numProfiles; i++)
	{
		url = "/config/profiles/" + profile[i].getAttribute("filename") + ".xml";
		SimpleAJAXCall(urlex(url), cbProfile, "", i);
	}
	statusBar("Getting profiles...");
}

function cbProfile(xml, param)
{
	profileConfig[param] = loadXMLString(xml);
	progressBarStepIt2();
	statusBar("Got profile "+param);
	if ((param+1) == numProfiles)
		setTimeout("addProfiles();", 10);
}

// now the profiles have loaded
// let's add the profile template for each profile
function addProfiles()
{
	var profiles = new Array();
	profiles = dwconfig.getElementsByTagName("Profile");
	var pfls = rootmenu.getElementsByTagName("Profiles")[0];
	var profile;
	var p, pfc1, pfc2, pfname;
	for (i=0; i<numProfiles; i++)
	{
		p = profileConfig[i];
		if (typeof(p) != "undefined")
		{
			profile = uiProfileTemplate.documentElement.cloneNode(true);
			profile.setAttribute("name", profiles[i].getAttribute("name"));
			profile.setAttribute("filename", profiles[i].getAttribute("filename"));
			//profile.setAttribute("enabled", profiles[i].getAttribute("active"));
			//profile.firstChild.firstChild.nodeValue = 1;	//profiles[i].getAttribute("active");
			pfc1 = profile.firstChild;
			pfc2 = pfc1.firstChild;
			pfc2.nodeValue = 1;
			pfname = profile.getAttribute("filename");
			if ((pfname != "Default") && (pfname != "Profile0"))
			{
				//  <Applications><Application name="Add new" type="add"></Application></Applications>
				//var apps = xmldocblank.createElement("Applications");
				//var app = xmldocblank.createElement("Application");
				//app.setAttribute("type", "add");
				//app.setAttribute("name", "Add new");
				//apps.appendChild(app);
				//profile.insertBefore(apps, profile.childNodes[1]);
				var apps = profiles[i].getElementsByTagName("Application");
				for (j = 0; j < apps.length; j++)
				{
					var app = xmldocblank.createElement("Application");
					var name = apps[j].firstChild.nodeValue;	//.text
					app.setAttribute("value", name);
					app.setAttribute("name", name);
					var ed = xmldocblank.createElement("Edit");
					ed.setAttribute("type", "edit");
					app.appendChild(ed);
					var del = xmldocblank.createElement("Delete");
					del.setAttribute("type", "delete");
					app.appendChild(del);
					var ib = profile.childNodes[1].childNodes.length-1;
					var t = profile.childNodes[1].childNodes[ib];
					profile.childNodes[1].insertBefore(app, t);
				}

				var ren = xmldocblank.createElement("Rename");
				profile.appendChild(ren);
				var del = xmldocblank.createElement("Delete");
				del.setAttribute("type", "delete");
				profile.appendChild(del);
			}
			else
			{
				var apps = profile.getElementsByTagName("Applications")[0];
				apps.parentNode.removeChild(apps);
			}
			//if (profiles[i].childNodes[0])
			//	profile.insertBefore(profiles[i].childNodes[0], profile.childNodes[1]);
			pfls.appendChild(profile);
		}
	}
	var newel = xmldocblank.createElement("Profile");
	newel.setAttribute("name", "Add new");
	newel.setAttribute("type", "add");	//"profile");
	pfls.appendChild(newel);
}

function getPlugins()
{
	var plugin = dwconfigdfn.getElementsByTagName("PlugIn");
	numPlugins = plugin.length;
	var url, js, pid;
	var IEMobile = isIEMobile();
	for (var i=0; i<numPlugins; i++)
	{
		pid = plugin[i].getAttribute("id").toLowerCase();
		url = "/dwui/dwui_" + pid + ".xml";
		SimpleAJAXCall(urlex(url), cbPlugin, "", i);
		//if (IEMobile) {
		//	js = "<script type='text/javascript' src='dwui_" + pid + ".js'/>";
		//	document.getElementById("js" + i).innerHTML = js;
		//}
	}
	//if (menuLoaded) return;
	statusBar("Getting plugins...");
}

function getFeedback()
{
	var url;
	var feedback = dwconfigdfn.getElementsByTagName("Feedback");
	var lenFeedback = feedback.length;
	for (var i=0; i<lenFeedback; i++)
	{
		url = feedback[i].getAttribute("id");
		if (url)
		{
			url = "/dwui/dwui_" + url.toLowerCase() + ".xml";
			SimpleAJAXCall(urlex(url), cbFeedback, "", i);
			numFeedback++;
		}
	}
	statusBar("Getting feedback...");
}

function cbPlugin(xml, param)
{
	uiPlugin[param] = loadXMLString(xml);
	progressBarStepIt2();
	statusBar("Defaulting plugin "+param);
	addFeedback2Plugin(uiPlugin[param]);
	setPluginDefaults(uiPlugin[param]);
	if ((param+1) == numPlugins)
	{
		if (menuLoaded) {
			setTimeouts--;
			statusBar("");
			return;
		}
		setTimeout("addPlugins();", 100);
	}
}

function cbFeedback(xml, param)
{
	uiFeedback[param] = loadXMLString(xml);
	progressBarStepIt2();
	statusBar("Defaulting feedback "+param);
	setFeedbackDefaults(uiFeedback[param]);
	if ((param+1) == numFeedback)
		setTimeout("addFeedback();", 100);
}

function addFeedback2Plugin(plug)
{
	var fdbk = selectNodes(plug, "//*[@type='feedback']");
	var len = fdbk.length;
	for (var i=0; i< len; i++)
	{
		var nfn = uiFeedback.documentElement.childNodes.length;
		for (var j=0; j<nfn; j++)
		{
			var fbn = uiFeedback.documentElement.childNodes[j].cloneNode(true);
			fdbk[i].appendChild(fbn);
		}
		//var fbn = uiFeedback.documentElement.cloneNode(true);
	}
}

// now add the plugins into the menu tree
function addPlugins()
{
	if (menuLoaded) return;
	var i, j, k, p=0;
	var profile, pfl;
	var plugin = new Array();
	var pid;
	var input, output, process;
	var datapaths, path;
	for (i=0; i<numProfiles; i++)
	{
		profile = profileConfig[i];
		if (profile != null)
		{
			//plugin = profile.getElementsByTagName("PlugIn");
			plugin = dwconfigdfn.getElementsByTagName("PlugIn");
			for (j=0; j<plugin.length; j++)
			{
				pid = plugin[j].getAttribute("id");
				for (k=0; k<numPlugins; k++)
				{
					plug = uiPlugin[k].documentElement;
					if (plug != null)
					{
						//if (plug != null)
						if (pid == plug.getAttribute("id"))
						{
							pfl = rootmenu.getElementsByTagName("Profile")[i];
							p++;
							switch(plugin[j].parentNode.nodeName)
							{
							case "Input":
								input = pfl.getElementsByTagName("Input")[0];
								//if (input.parentNode.parentNode.nodName == "PlugIns")
								input.appendChild(plug.cloneNode(true));
								break;
							case "Output":
								output = pfl.getElementsByTagName("Output")[0];
								output.appendChild(plug.cloneNode(true));
								break;
							case "Process":
								datapaths = pfl.getElementsByTagName("DataPaths")[0];
								path = datapaths.getElementsByTagName("Path")[0];
								process = path.getElementsByTagName("Process")[0];
								//plg = process.getElementsByTagName("Plugin")[0];
								//plg.appendChild(plug.cloneNode(true));
								process.appendChild(plug.cloneNode(true));
								break;
							}
						}
					}
				}
			}
			if (profile.documentElement != null)
			{
				statusBar("Restoring profile "+i);
				setPluginValues(profile.documentElement);
				addDecoders2Criteria(i);
			}
		}
	}
	//setTimeout("getFeedback();", 100);
	//getFeedback();
	setTimeouts--;
	loadRootMenu(rootmenu.documentElement.childNodes);
}

function addFeedback()
{
	var fb = selectNodes(rootmenu, "//*[@type='feedback']");
	for (var i=0; i<fb.length; i++)
	{
		var fbn = uiFeedback[0].documentElement.cloneNode(true);
		fb[i].appendChild(fbn);
	}
	setTimeouts--;
}

function addPlugins2Profile(pfl)
{
	var i, j, k, p=0;
	var plugin = new Array();
	var pid, ret = true;

	plugin = dwconfigdfn.getElementsByTagName("PlugIn");
	for (j=0; j<plugin.length; j++)
	{
		pid = plugin[j].getAttribute("id");
		for (k=0; k<numPlugins; k++)
		{
			plug = uiPlugin[k].documentElement;
			if (plug != null)
			{
				if (pid == plug.getAttribute("id"))
				{
					//pfl = rootmenu.getElementsByTagName("Profile")[i];
					//p++;
					//routing = pfl.getElementsByTagName("Routing")[0];
					//route = routing.getElementsByTagName("Route")[0];
					//process = route.getElementsByTagName("Process")[0];
					switch(plugin[j].parentNode.nodeName)
					{
					case "Input":
						input = pfl.getElementsByTagName("Input")[0];
						p = plug.cloneNode(true);
						if (p == null) ret = false;
						input.appendChild(p);
						break;
					case "Output":
						output = pfl.getElementsByTagName("Output")[0];
						p = plug.cloneNode(true);
						if (p == null) ret = false;
						output.appendChild(p);
						break;
					case "Process":
						//process.appendChild(plug.cloneNode(true));
						break;
					}
				}
			}
		}
	}
	return ret;
}

function addPlugins2Datapath(pth)
{
	var i, j, k, p=0;
	var plugin = new Array();
	var pid, name;
	var newel, newtxt, node;
	var input = null, output = null;
	var oid = 0, iid = 0, ret = true;

	plugin = dwconfigdfn.getElementsByTagName("PlugIn");
	for (j=0; j<plugin.length; j++)
	{
		pid = plugin[j].getAttribute("id");
		for (k=0; k<numPlugins; k++)
		{
			plug = uiPlugin[k].documentElement;
			if (plug != null)
			{
				//if (plug != null)
				if (pid == plug.getAttribute("id"))
				{
					//pfl = rootmenu.getElementsByTagName("Profile")[i];
					p++;
					name = plug.getAttribute("name");
					switch(plugin[j].parentNode.nodeName)
					{
					case "Input":
						if (input == null)
						{
							input = xmldocblank.createElement("Plugin");
							if (input == null) ret = false;
							input.setAttribute("type", "select");
							input.setAttribute("name", "Plugin");
							input.setAttribute("oid", 0);
							input.setAttribute("value", pid);
						}
						newel = xmldocblank.createElement("option");
						if (input == null) ret = false;
						newel.setAttribute("id", iid);	iid++;
						newel.setAttribute("name", name);
						newel.setAttribute("value", pid);
						input.appendChild(newel);
						//newtxt = xmldocblank.createTextNode("1");
						//newel.appendChild(newtxt);
						node = pth.getElementsByTagName("Input")[0];
						node.appendChild(input);
						break;
					case "Output":
						if (output == null)
						{
							output = xmldocblank.createElement("Plugin");
							if (output == null) ret = false;
							output.setAttribute("type", "select");
							output.setAttribute("name", "Plugin");
							output.setAttribute("oid", 0);
							output.setAttribute("value", pid);
						}
						newel = xmldocblank.createElement("option");
						if (newel == null) ret = false;
						newel.setAttribute("id", oid);  oid++;
						newel.setAttribute("name", name);
						newel.setAttribute("value", pid);
						output.appendChild(newel);
						//newtxt = xmldocblank.createTextNode("1");
						//newel.appendChild(newtxt);
						node = pth.getElementsByTagName("Output")[0];
						node.appendChild(output);
						break;
					case "Process":
						newel = plug.cloneNode(true);
						if (newel == null) ret = false;
						process = pth.getElementsByTagName("Process")[0];
						//plg = process.getElementsByTagName("Plugin")[0];
						//plg.appendChild(newel);
						process.appendChild(newel);
						break;
					}
				}
			}
		}
	}
	return ret;
}

function setPluginDefaults(plug)
{
	var p = plug.getElementsByTagName("PlugIn");
	var id = p[0].getAttribute("id");
	var d = selectNodes(dwconfigdfn, "//PlugIn[@id='"+id+"']");
	setElementDefault(p, d);
}

function setFeedbackDefaults(feedback)
{
	var p = feedback.getElementsByTagName("Feedback");
	var id = p[0].getAttribute("id");
	var d = selectNodes(dwconfigdfn, "//Feedback[@id='"+id+"']");
	setElementDefault(p, d);
	setTimeouts--;
}

function setElementDefault(pel, del)
{
	//progressBarStepIt2();
	var dval, pval, kids, dna, p, d, i, nnMatch, idMatch;
	var pid, did, ptype, dtype, opt;
	var plen = pel.length;
	var dlen = del.length;
	if ((plen > 0) && (dlen > 0))
	{
		if (dlen > plen)
		{
			for (i=0; i<dlen; i++)
			{
				did = del[i].getAttribute("id");
				if (did == null) break;
				if (i >= plen) {
					if (pel[0].nodeName == "Device")
					{
						dna = pel[0].cloneNode(true);
						dna.setAttribute("id", did);
						did = del[i].getAttribute("desc");
						if (did != null) {
							dna.setAttribute("name", did);
							dna.setAttribute("desc", did);
						}
						pel[0].parentNode.appendChild(dna);
					}
				}
				else
				{
					if (pel[i].getAttribute("type") == "add") break;
					pid = pel[i].getAttribute("id");
					if (pid == null) pel[i].setAttribute("id", did);
					did = del[i].getAttribute("desc");
					if (did != null) {
						pel[i].setAttribute("name", did);
						pel[i].setAttribute("desc", did);
					}
				}
			}
			plen = pel.length;
		}
		for (p=0; p<plen; p++)
		{
			if (pel[p].nodeType != 1) continue;
			if (pel[p].getAttribute("type") == "add") continue;
			pid = pel[p].getAttribute("id");
			nnMatch = -1;
			idMatch = -1;
			did = null;
			for (d=0; d<dlen; d++)
			{
				if (del[d].nodeName == pel[p].nodeName)
				{
					nnMatch = d;
					did = del[d].getAttribute("id");
					if (did == pid)
					{
						idMatch = d;
						break;
					}
				}
			}
			if (nnMatch >= 0)
			{
				if (idMatch < 0)
				{
					d = 1;
					ptype = pel[p].parentNode.getAttribute("type");
					if (ptype == "fixed")
					{
						pval = pel[p].parentNode.getAttribute("value");
						if (pid == pval) d = 0;
					}
					if (d > 0)
					{
						pel[p].parentNode.removeChild(pel[p]);
						p--; plen--;
						continue;
					}
				}
				if (d == dlen) d = nnMatch;
				dval = del[d].getAttribute("desc");
				if (dval != null)
				{
					pel[p].setAttribute("desc", dval);
				}
				dval = del[d].getAttribute("default");
				if (dval != null)
				{
					pval = pel[p].getAttribute("value");
					if (pval != null)
					{
						pel[p].setAttribute("value", dval);
						ptype = pel[p].getAttribute("type");
						switch(ptype)
						{
						case "select":
							opt = pel[p].getElementsByTagName("option");
							for (i=0; i<opt.length; i++)
							{
								if (opt[i].getAttribute("value") == dval)
								{
									pel[p].setAttribute("oid", opt[i].getAttribute("id"));
									break;
								}
							}
							break;
						}
					}
					else
					if (pel[p].childNodes.length > 0)
					if (pel[p].childNodes[0].nodeType == 3)
						pel[p].childNodes[0].nodeValue = dval;
				}
				dtype = del[d].getAttribute("type");
				if (dtype != null)
				switch(dtype)
				{
				case "fixed":
					dval = del[d].getAttribute("value");
					if (dval != null)
						pel[p].setAttribute("value", dval);
					break;
				case "integer":
					dval = del[d].getAttribute("min");
					if (dval != null)
						pel[p].setAttribute("min", dval);
					dval = del[d].getAttribute("max");
					if (dval != null)
						pel[p].setAttribute("max", dval);
					break;
				}
			}
			else
				continue;
			var kids = pel[p].childNodes.length;
			if (kids > 0)
			{
				setElementDefault(pel[p].childNodes, del[d].childNodes);
			}
		}
	}
}

function setElementValue(pel, del)
{
	//progressBarStepIt2();
	var dval, pval, kids, dna, p, d, i, nnMatch, idMatch;
	var pid, did, ptype, dtype, opt;
	var plen = pel.length;
	var dlen = del.length;
	if ((plen > 0) && (dlen > 0))
	{
		for (p=0; p<plen; p++)
		{
			if (pel[p].nodeType != 1) continue;
			pid = pel[p].getAttribute("id");
			nnMatch = -1;
			idMatch = -1;
			did = null;
			for (d=0; d<dlen; d++)
			{
				if (del[d].nodeName == pel[p].nodeName)
				{
					nnMatch = d;
					did = del[d].getAttribute("id");
					if (did == pid)
					{
						idMatch = d;
						break;
					}
				}
			}
			if (nnMatch >= 0)
			{
				if (d == dlen) d = nnMatch;
				ptype = pel[p].getAttribute("type");
				if (ptype != null)
				switch(ptype)
				{
				case "fixed":
					break;
				case "bool":
				case "integer":
					if (pel[p].childNodes[0].length > 0)
					if (pel[p].childNodes[0].nodeType == 3)
					{
						if (del[d].childNodes.length > 0)
						if (del[d].childNodes[0].nodeType == 3)
						{
							pel[p].childNodes[0].nodeValue = del[d].childNodes[0].nodeValue;
						}
					}
					break;
				case "select":
					if (del[d].childNodes.length > 0)
					if (del[d].childNodes[0].nodeType == 3)
					{
						dval = del[d].childNodes[0].nodeValue;
						pel[p].setAttribute("value", dval);
						opt = pel[p].getElementsByTagName("option");
						for (i=0; i<opt.length; i++)
						{
							if (opt[i].getAttribute("value") == dval)
							{
								pel[p].setAttribute("oid", opt[i].getAttribute("id"));
								break;
							}
						}
					}
					break;
				}
			}
			else
				continue;
			if ((pel[p].childNodes.length > 0) && (del[d].childNodes.length > 0))
			{
				setElementValue(pel[p].childNodes, del[d].childNodes);
			}
		}
	}
}

function setPluginValues(prfl)
{
	var pname = prfl.getAttribute("name");
	if (pname == null) return;
	var p = selectNodes(rootmenu, "//Profile[@name='"+pname+"']");
	if (p.length == 0) return;
	var d = selectNodes(prfl, "PlugIns/Input");
	var p0 = selectNodes(p[0], "Input");
	setElementValue(p0, d);
	p0 = selectNodes(p[0], "Output");
	var d0 = selectNodes(prfl, "Plugins/Output");
	setElementValue(p0, d0);
}

function setLogValues()
{
	statusBar("Setting Log values...");
	var i, len, v, id;
	var logsrc, logdest;

	logsrc = selectNodes(dwconfig, "//LogSize")[0];
	if (logsrc == null)
	{
		logsrc = selectNodes(dwconfigdfn, "//LogSize");
		v = logsrc[0].getAttribute("default");
	}
	else 
		v = logsrc.childNodes[0].nodeValue;
	logdest = selectNodes(rootmenu, "//LogSize")[0];
	logdest.setAttribute("value", v);
	len = logdest.childNodes.length;
	for (i=0; i<len; i++)
	{
		if (logdest.childNodes[i].getAttribute("value") == v)
		{
			id = logdest.childNodes[i].getAttribute("id");
			logdest.setAttribute("oid", id);
			break;
		}
	}

	logsrc = selectNodes(dwconfig, "//LogPath")[0];
	if (logsrc == null)
	{
		logsrc = selectNodes(dwconfigdfn, "//LogPath")[0];
		v = logsrc.getAttribute("default");
	}
	else
		v = logsrc.childNodes[0].nodeValue;
	logdest = selectNodes(rootmenu, "//LogPath")[0];
	logdest.childNodes[0].nodeValue = v;

	logsrc = selectNodes(dwconfig, "//TempPath")[0];
	if (logsrc == null)
	{
		logsrc = selectNodes(dwconfigdfn, "//TempPath")[0];
		v = logsrc.getAttribute("default");
	}
	else
		v = logsrc.childNodes[0].nodeValue;
	
	logdest = selectNodes(rootmenu, "//TempPath")[0];
	logdest.childNodes[0].nodeValue = v;

	logsrc = selectNodes(dwconfig, "//LogLevel")[0];
	if (logsrc == null)
	{
		logsrc = selectNodes(dwconfigdfn, "//LogLevel")[0];
		v = logsrc.getAttribute("default");
	}
	else
		v = logsrc.childNodes[0].nodeValue;
	logdest = selectNodes(rootmenu, "//LogLevel")[0];
	logdest.setAttribute("value", v);
	l = logdest.childNodes.length;
	for (i=0; i<l; i++)
	{
		if (logdest.childNodes[i].getAttribute("value") == v)
		{
			id = logdest.childNodes[i].getAttribute("id");
			logdest.setAttribute("oid", id);
			break;
		}
	}
	statusBar("");
}

function setActiveProfile()
{
	statusBar("Setting Active Profile...");
	var apsrc = selectNodes(dwconfig, "//Profiles")[0];
	var apdest = selectNodes(rootmenu, "//ActiveProfile")[0];
	var len = apsrc.childNodes.length;
	var name, filename;
	for (var i=0; i<len; i++)
	{
		var opt = xmldocblank.createElement("option");
		opt.setAttribute("id", i);
		name = apsrc.childNodes[i].getAttribute("name");
		filename = apsrc.childNodes[i].getAttribute("filename");
		opt.setAttribute("name", name);
		opt.setAttribute("value", filename);
		apdest.appendChild(opt);
		if (apsrc.childNodes[i].getAttribute("active") > 0)
		{
			apdest.setAttribute("oid", i);
			apdest.setAttribute("value", filename);
		}
	}
}

function setActiveProfileSwitching()
{
	var aps0 = selectNodes(rootmenu, "//AutoProfileSwitching");
	var dwaps0 = selectNodes(dwconfig, "//AutoProfileSwitching");
	var aps = aps0[0];
	var dwaps = dwaps0[0];
	//aps.childNodes[0].nodeValue = dwaps.childNodes[0].nodeValue;
	var val = dwaps.childNodes[0].nodeValue;
	aps.setAttribute("value", val);
	if (val == "0")
		aps.setAttribute("oid", "1");
	else
		aps.setAttribute("oid", "0");
}

function setDeviceInfo()
{
	var val, node;
	var platform = selectNodes(dwconfigdfn, "//Platform")[0];
	if (platform != null)
	{
		if (platform.childNodes.length > 0)
		{
			val = platform.childNodes[0].nodeValue;
			node = selectNodes(rootmenu, "//Platform");
			if (node != null)
				node[0].setAttribute("name", "Platform: "+val);
		}
	}
	var model = selectNodes(dwconfigdfn, "//Model")[0];
	if (model != null)
	{
		if (model.childNodes.length > 0)
		{
			val = model.childNodes[0].nodeValue;
			node = selectNodes(rootmenu, "//Model");
			if (node != null)
				node[0].setAttribute("name", "Model: "+val);
		}
	}
}

function isIEMobile()
{
	var browser = navigator.appName;
	if (browser.indexOf("IE") >= 0)
		if (browser.indexOf("Mobile") >= 0)
			return true;
	return false;
}

function addPluginVersionInfo()
{
	updateDWVersion();
	var version = selectNodes(dwconfigdfn, "//*[@version]");
	var len = version.length;
	if (len == 0) return;
	var about = rootmenu.getElementsByTagName("About")[0];
	var node, name, ver, text;
	node = xmldocblank.createElement("Blank");
	node.setAttribute("name", "");
	about.appendChild(node);
	for (var i=0; i< len; i++)
	{
		node = xmldocblank.createElement("Version");
		name = version[i].getAttribute("desc");
		if (name == null) continue;
		node.setAttribute("name", name);
		ver = version[i].getAttribute("version").trim();
		txt = xmldocblank.createTextNode(ver);
		node.appendChild(txt);
		about.appendChild(node);
	}
	node = xmldocblank.createElement("Blank");
	node.setAttribute("name", "");
	about.appendChild(node);
}

function addDecoders2Criteria(idx)
{
	var prfl = rootmenu.getElementsByTagName("Profile")[idx];
	addDecoders2ProfileCriteria(prfl);
}

function addDecoders2ProfileCriteria(prfl)
{
	var newdevice, desc, decoderlist, newdecoder, tn;
	try
	{
		//var prfl = rootmenu.getElementsByTagName("Profile")[idx];
		var rule0 = selectNodes(prfl, "DataPaths/Path[@id='Route0']/Process/PlugIn[@id='ADFPLUGIN']/RuleSet/Rule[@name='Rule0']")[0];
		if (rule0 == null) return;
		// now generate the device list
		var devicelist = selectNodes(prfl, "Input/PlugIn/Device");
		for (i=0; i<devicelist.length; i++)
		{
			newdevice = rule0.getElementsByTagName("Device")[0].cloneNode(true);
			newdevice.setAttribute("name", devicelist[i].getAttribute("name"));
			newdevice.setAttribute("id", devicelist[i].getAttribute("id"));
			desc = devicelist[i].getAttribute("desc");
			if (desc != null) newdevice.setAttribute("desc", desc);
			decoderlist = devicelist[i].getElementsByTagName("Decoder");
			for (j=0; j<decoderlist.length; j++)
			{
				newdecoder = xmldocblank.createElement("Decoder");	//newdevice.getElementsByTagName("Decoder")[0].cloneNode(true);
				newdecoder.setAttribute("name", decoderlist[j].getAttribute("name"));
				newdecoder.setAttribute("id", decoderlist[j].getAttribute("id"));
				newdecoder.setAttribute("type", "bool");
				tn = xmldocblank.createTextNode("0");
				newdecoder.appendChild(tn);	//.text
				//if (j == 0)
				//	newdevice.getElementsByTagName("Decoders")[0].replaceChild(newdecoder, newdevice.getElementsByTagName("Decoder")[0]);
				//else
					newdevice.getElementsByTagName("Decoders")[0].appendChild(newdecoder);
			}
			if (i == 0)
				rule0.getElementsByTagName("Devices")[0].replaceChild(newdevice, rule0.getElementsByTagName("Device")[0]);
			else
				rule0.getElementsByTagName("Devices")[0].appendChild(newdevice);
		}
		// now generate the decoder list
		//menu[menulevel][idx].parentNode.insertBefore(rule0, menu[menulevel][idx]);
	}
	catch(e)
	{
		alert("Unexpected error adding decoder list to ADF Criteria.\r\n\r\nDescription is...\r\n\r\n"+e.description);
	}
}

function addDecoders2DatapathCriteria(path)
{
	var newdevice, desc, decoderlist, newdecoder, tn;
	try
	{
		//var prfl = rootmenu.getElementsByTagName("Profile")[idx];
		var rule0 = selectNodes(path, "Process/PlugIn[@id='ADFPLUGIN']/RuleSet/Rule[@name='Rule0']")[0];
		if (rule0 == null) return false;
		// now generate the device list
		//var devicelist = selectNodes(prfl, "Input/PlugIn/Device");
		var devicelist = selectNodes(menu[0][0], xpathRoot + "/Input/PlugIn/Device");
		for (i=0; i<devicelist.length; i++)
		{
			newdevice = rule0.getElementsByTagName("Device")[0].cloneNode(true);
			newdevice.setAttribute("name", devicelist[i].getAttribute("name"));
			newdevice.setAttribute("id", devicelist[i].getAttribute("id"));
			desc = devicelist[i].getAttribute("desc");
			if (desc != null) newdevice.setAttribute("desc", desc);
			decoderlist = devicelist[i].getElementsByTagName("Decoder");
			for (j=0; j<decoderlist.length; j++)
			{
				newdecoder = xmldocblank.createElement("Decoder");	//newdevice.getElementsByTagName("Decoder")[0].cloneNode(true);
				newdecoder.setAttribute("name", decoderlist[j].getAttribute("name"));
				newdecoder.setAttribute("id", decoderlist[j].getAttribute("id"));
				newdecoder.setAttribute("type", "bool");
				tn = xmldocblank.createTextNode("0");
				newdecoder.appendChild(tn);	//.text
				//if (j == 0)
				//	newdevice.getElementsByTagName("Decoders")[0].replaceChild(newdecoder, newdevice.getElementsByTagName("Decoder")[0]);
				//else
					newdevice.getElementsByTagName("Decoders")[0].appendChild(newdecoder);
			}
			if (i == 0)
				rule0.getElementsByTagName("Devices")[0].replaceChild(newdevice, rule0.getElementsByTagName("Device")[0]);
			else
				rule0.getElementsByTagName("Devices")[0].appendChild(newdevice);
		}
		// now generate the decoder list
		//menu[menulevel][idx].parentNode.insertBefore(rule0, menu[menulevel][idx]);
	}
	catch(e)
	{
		alert("Unexpected error adding decoder list to ADF Criteria.\r\n\r\nDescription is...\r\n\r\n"+e.description);
		return false;
	}
	return true;
}

function updateDWVersion()
{
	var dw = selectNodes(dwconfigdfn.documentElement, "/DWConfigDfn/DataWedge");
	if (dw == null) return;
	var dwver = dw[0].getAttribute("version");
	if (dwver == null) return;
	//var about = rootmenu.getElementsByTagName("About")[0];
	//var abver = about.getElementsByTagName("Version")[0];
	var abver = selectNodes(rootmenu, "/DWUI/Advanced/About/Version");
	abver[0].setAttribute("name", "v"+dwver);
	
}

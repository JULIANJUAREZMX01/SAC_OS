// menu functions

// node types
var nodeType = {
	Element: 1,
	Attribute: 2,
	Text: 3,
	Comment: 8,
	Document: 9
}

// global variables
var _ticked = "\u221a";  //"images/chkbox_ticked.bmp";
var _blank = "&nbsp;"; 	//"images/chkbox_blank.bmp";
//var trail = new Array();
//var traillevel = 0;
var menu = new Array();
var menuname = new Array();
var menupage = new Array();
var xpath;
var xpathRoot;
var menulevel = 0;
var menuhtml;
var mainmenu = new dwmenu();
var currentProfileName;
var shortcut = "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
var ds, de;
var keytrap = false;
var changed = false;
var processing = false;

try { document.onkeydown = keyCheck; } catch(e){}

function loadRootMenu(xml)
{
	menuLoaded = true;
	setTimeout("statusBar('');", 100);
	ds = new Date();
	xpath = new Array();
	menulevel = 0;
	menuname[menulevel] = "DataWedge";
	menu[menulevel] = xml;
	menupage[menulevel] = 0;
	keytrap = true;
	if (dwuiView == viewType.basic)
		onSelect(1);
	else
		onSelect(0);
	//updateMenu();
}

function keyCheck(ev)
{
	if (!keytrap) return true;
	var keyId;
	if (window.event) //IE
	  keyId = event.keyCode;
	else if (ev.which) // Netscape/Firefox/Opera
	  keyId = ev.which;
	switch (keyId)
	{
	case 37:  // arrow left
	  break;
	case 38:  // arrow up
	  break;
	case 39:  // arrow right
	  break;
	case 40:  // arrow down
	  break;
	}
	var keychar = String.fromCharCode(keyId);
	var numcheck = /\d/;
	if (numcheck.test(keychar))
		onSelect(keychar-1);
}

function saveProfile(profileName, idx)
{
	var kt = keytrap;  keytrap = false;
	var pnode = selectNodes(menu[0][0], "//Profile[@name='"+profileName+"']");
	var filename = "/config/profiles/" + pnode[0].getAttribute("filename") + ".xml";
	var str = createProfileString(pnode[0].getAttribute("name"), menu[menulevel][0].parentNode);
	var ret = puturl(filename, str);
	if (ret != null) {
		writeDWConfig();
		writeMenu();
	}
	else
		alert("Error saving profile. DataWedge may not be running.");
	statusBar("");
	keytrap = kt;
}

function saveDefaultProfile()
{
	var kt = keytrap;  keytrap = false;
	var pnode = selectNodes(menu[0][0], "//Profile[@name='Profile0']");
	if (pnode.length == 0)
		pnode = selectNodes(menu[0][0], "//Profile[@filename='Default']");
	var filename = "/config/profiles/" + pnode[0].getAttribute("filename") + ".xml";
	var str = createProfileString(pnode[0].getAttribute("name"), pnode[0].parentNode);
	var ret = puturl(filename, str);
	if (ret != null) {
		writeDWConfig();
		writeMenu();
	}
	else
		alert("Error saving profile. DataWedge may not be running.");
	statusBar("");
	keytrap = kt;
}

function deleteProfile(filename)
{
	var ret = deleteurl("/config/profiles/" + filename + ".xml");
	if (ret != null) {
		// need to remove profile from DWConfig.xml and save it
		var dwcps = selectNodes(dwconfig, "//Profiles");
		node = selectNodes(dwconfig, "//Profile[@filename='" + filename + "']");
		if (dwcps.length > 0) {
			if (node.length > 0) {
				dwcps[0].removeChild(node[0]);
			}
		}
		writeDWConfig();
		writeMenu();
	}
	else
		alert("Error deleting profile. DataWedge may not be running.");
	statusBar("");
}

function saveSettings()
{
	var kt = keytrap;  keytrap = false;
	writeDWConfig();
	writeMenu();
	statusBar("");
	keytrap = kt;
}

function onSelect(idx)
{
	var p = processing; processing = true;
	onSelect2(idx);
	processing = p;
}

function onSelect2(idx)
{
	if (!keytrap) return;
	// check for Exit
	if (idx == 999)
	{
		return;
	}
	// check for Back
	var ret;
	if ((idx == 666) || (idx == -1) || (idx == 777))
	{
		if (menulevel < 2)
		{
			ret = confirm("Are you sure you want to exit?")
			if (ret)
				if (isIEMobile())
				{
					//alert("Please close IE Mobile manually.");
					geturl("/dwui/index.html?kill=foregroundwindow");
					return;
				}
				else
				{
					window.close();
					return;
				}
			return;
		}
		if (menupage[menulevel] > 0)
		{
			menupage[menulevel]--;
			if (idx != 777) updateMenu();
			return;
		}
		// make sure we can go Back, i.e. we are not already at the root level
		if (menulevel > 0)
		{
			if (dwuiView == viewType.basic)
			if (menulevel > 1)
			if (menu[menulevel-2].length > 1)
			{
				switch(menu[menulevel-2][1].nodeName)
				{
					case "Basic":
						ret = confirm("Save changes?");
						if (!ping()) { alert("Error contacting server.  DataWedge may not be running."); return; }
						if (ret)
						{
							statusBar("Saving changes, please wait...");
							setTimeout("saveDefaultProfile();", 50);
						}
						else
							reloadMenu();
						break;
				}
			}
			//switch(menu[menulevel-1][0].nodeName)
			//{
			//}
			//if (menu[menulevel-1][0].nodeName == "Profile")
			//{
			//}
			if (dwuiView == viewType.advanced)
			switch(menu[menulevel][0].parentNode.nodeName)
			{
				case "Profile":
					profileName = menu[menulevel][0].parentNode.getAttribute("name");
					ret = confirm("Save changes to " + profileName);
					if (!ping()) { alert("Error contacting server.  DataWedge may not be running."); return; }
					if (ret)
					{
						//var filename = "/config/profiles/" + profileName + ".xml";
						//var str = createProfileString(profileName, menu[menulevel][0].parentNode);
						//puturl(filename, str);
						//writeMenu();
						//writeDWConfig();
						statusBar("Saving changes, please wait...");
						setTimeout("saveProfile('"+profileName+"', "+idx+");", 50);
					}
					else
						reloadMenu();
					break;
				case "Settings":
					ret = confirm("Save changes to Settings?");
					if (!ping()) { alert("Error contacting server.  DataWedge may not be running."); return; }
					if (ret)
					{
						statusBar("Saving changes, please wait...");
						setTimeout("saveSettings();", 50);
					}
					else
						reloadMenu();
					break;
				//case "Log":
				//case "ActiveProfile":
				//	writeDWConfig();
			}
			menu[menulevel] = null;
			menulevel--;	xpath.pop();
			if (idx != 777)
			if (menu[menulevel][0].attributes.length > 0) 
				if (menu[menulevel][0].getAttribute("skip") == "0")
				{
					setTimeout("onSelect('666');", 50);
					return;
				}
			if (idx != 777) updateMenu();
		}
		return;
	}
	// check for more!
	if (idx == 8)
	{
		if (menu[menulevel].length > (menupage[menulevel]*8+idx+1))
		{
			menupage[menulevel]++;
			updateMenu();
			return;
		}
	}
	idx = menupage[menulevel]*8 + idx;
	// check for out of bounds
	if (idx >= menu[menulevel].length) return;

	switch(menu[menulevel][idx].nodeName)
	{
	case "Profile":
		currentProfileName = menu[menulevel][idx].getAttribute("name");
		xpathRoot = "/DWUI/Advanced/Profiles/Profile[@name='" + currentProfileName + "']";
		break;
	case "Rename":
	case "Edit":
		displayRename(idx);
		return;
	case "option":
		// we're displaying and select/option so lets update the tick marks only, not the whole menu
		var pid = menu[menulevel][idx].parentNode.getAttribute("oid");
		if ((pid >= menupage[menulevel]*8) && (pid < menupage[menulevel]*8+9))
			document.getElementById("img"+(pid-menupage[menulevel]*8)).innerHTML = _blank;
		var val = menu[menulevel][idx].getAttribute("value");
		var oid = menu[menulevel][idx].getAttribute("id");
		document.getElementById("img"+(oid-menupage[menulevel]*8)).innerHTML = _ticked;
		//menu[menulevel][idx].parentNode.setAttribute("value", val);
		menu[menulevel][idx].parentNode.getAttributeNode("value").nodeValue = val;
		menu[menulevel][idx].parentNode.getAttributeNode("oid").nodeValue = oid;
		return;
	case "Action":
		if (menu[menulevel][idx].parentNode.getAttribute("type") == "add")
		{
			var ln = menu[menulevel][idx].parentNode.parentNode.childNodes.length - 1;
			//menu[menulevel][idx].parentNode.parentNode.insertBefore(menu[menulevel][idx].childNodes[0], menu[menulevel][idx].parentNode.parentNode.childNodes[ln]);
			var action = menu[menulevel][idx].cloneNode(true);
			menu[menulevel][idx].parentNode.parentNode.insertBefore(action, menu[menulevel][idx].parentNode.parentNode.childNodes[ln]);
			menu[menulevel] = null;
			menulevel--;	xpath.pop();
			updateMenu();
			return;
		}
		break;
	case "Plugin":
		if (menu[menulevel][idx].parentNode.getAttribute("type") == "add")
		{
			var p = menu[menulevel][idx].parentNode.parentNode.childNodes;
			var ln = menu[menulevel][idx].parentNode.parentNode.childNodes.length - 1;
			for (i=0; i<ln; i++)
			{
				if (p[i].getAttribute("id") == menu[menulevel][idx].getAttribute("id"))
				{
					alert("Plugin already in use.");
					return;
				}
			}
			//menu[menulevel][idx].parentNode.parentNode.insertBefore(menu[menulevel][idx].childNodes[0], menu[menulevel][idx].parentNode.parentNode.childNodes[ln]);
			var action = menu[menulevel][idx].cloneNode(true);
			menu[menulevel][idx].parentNode.parentNode.insertBefore(action, menu[menulevel][idx].parentNode.parentNode.childNodes[ln]);
			menu[menulevel] = null;
			menulevel--;	xpath.pop();
			updateMenu();
			return;
		}
		break;
	}
	if (menu[menulevel][idx].attributes.getNamedItem("type"))
	{
		switch(menu[menulevel][idx].getAttribute("type"))
		{
		case "bool":
			if (menu[menulevel][idx].firstChild.nodeValue == "1")
			{
				menu[menulevel][idx].firstChild.nodeValue = "0";
				document.getElementById("img"+(idx-menupage[menulevel]*8)).innerHTML = _blank;
			}
			else
			{
				menu[menulevel][idx].firstChild.nodeValue = "1";
				document.getElementById("img"+(idx-menupage[menulevel]*8)).innerHTML = _ticked;
				if (menu[menulevel][idx].parentNode.getAttribute("type") == "mono")
				{
					var s = menu[menulevel][idx].parentNode.previousSibling;
					while (s != null)
					{
						s.firstChild.firstChild.nodeValue = "0";
						s = s.previousSibling;
					}
					s = menu[menulevel][idx].parentNode.nextSibling;
					while (s != null)
					{
						s.firstChild.firstChild.nodeValue = "0";
						s = s.nextSibling;
					}
				}
			}
			if (menu[menulevel][idx].nodeName == "Enabled")
			{
				if (menu[menulevel][idx].parentNode.attributes.getNamedItem("enabled"))
					menu[menulevel][idx].parentNode.setAttribute("enabled", menu[menulevel][idx].firstChild.nodeValue);
				if (menu[menulevel][idx].parentNode.nodeName == "Decoder")
					if (menu[menulevel][idx].firstChild.nodeValue == 0)
						menu[menulevel][idx].parentNode.parentNode.getElementsByTagName("EnableAll")[0].firstChild.nodeValue = 0;
					else
						menu[menulevel][idx].parentNode.parentNode.getElementsByTagName("DisableAll")[0].firstChild.nodeValue = 0;
			}
			return;
			break;
		case "delete":
			if (!confirm("Are you sure you want to delete this?")) return;
			var node = menu[menulevel][idx].parentNode;
			var pname = node.getAttribute("name");
			if (node.nodeName == "Profile")
			{
				if (!ping()) { alert("Error contacting server.  DataWedge may not be running."); return; }
				node.parentNode.removeChild(node);
				//deleteurl("/config/profiles/" + pname + ".xml");
				// need to remove profile from DWConfig.xml and save it
				//var dwcps = selectNodes(dwconfig, "//Profiles");
				//node = selectNodes(dwconfig, "//Profile[@name='" + pname + "']");
				//if (dwcps.length > 0) {
				//	if (node.length > 0) {
				//		dwcps[0].removeChild(node[0]);
				//	}
				//}
				//writeDWConfig();
				statusBar("Saving changes, please wait...");
				setTimeout("deleteProfile('"+node.getAttribute("filename")+"')", 50);
			}
			else
				node.parentNode.removeChild(node);
			//setTimeout("onSelect(666);", 10);
			menu[menulevel] = null;
			menulevel--;	xpath.pop();
			updateMenu();
			return;
			break;
		case "add":
			switch(menu[menulevel][idx].nodeName)
			{	
			case "Rule":
				displayRuleInput(idx, generateRuleName());
				return;
			case "Mapping":
				addKeymap(idx);
				return;
			}
			break;
		case "action":
			moveNode(menu[menulevel][idx].parentNode, menu[menulevel][idx].nodeName);
			menu[menulevel] = null;
			menulevel--;	xpath.pop();
			menu[menulevel] = null;
			menulevel--;	xpath.pop();
			updateMenu();
			return;
			break;
		case "function":
			//alert(menu[menulevel][idx].getAttribute("function") + "(" + idx + ");");
			setTimeout(menu[menulevel][idx].getAttribute("function") + "(" + idx + ");", 50);
			return;
			break;
		}
	}
	menu[menulevel+1] = menu[menulevel][idx].childNodes;
	// check if we have selected a value or a sub-menu
	if (menu[menulevel+1].length == 0)
	{
		if (menu[menulevel][idx].attributes.getNamedItem("type"))
		switch(menu[menulevel][idx].getAttribute("type"))
		{
		case "add":
			switch(menu[menulevel][idx].nodeName)
			{
			case "Profile":
				displayProfileInput(idx, generateProfileName());
				return;
			case "Path":
				displayDatapathInput(idx, generateDatapathName());
				return;
			case "Application":
				if (menu[menulevel][idx].childNodes.length == 0)
					displayProfileAppInput(idx, "");
				else
					displayProfileAppInput(idx, menu[menulevel][idx].firstChild.nodeValue);
				return;
			case "Rule":
				displayRuleInput(idx, generateRuleName());
				return;
			case "Mapping":
				alert("keymap2");
				return;
			}
		case "string":
			if (menu[menulevel][idx].childNodes.length == 0)
				displayStringInput(idx, "");
			else
				displayStringInput(idx, menu[menulevel][idx].firstChild.nodeValue);
			return;
		case "file":
			if (menu[menulevel][idx].childNodes.length == 0)
				displayFileInput(idx, "");
			else
				displayFileInput(idx, menu[menulevel][idx].firstChild.nodeValue);
			return;
		case "profile":
			displayProfileInput(idx, generateProfileName());
			return;
		case "datapath":
			displayDatapathInput(idx, generateDatapathName());
			return;
		case "profileapp":
			if (menu[menulevel][idx].childNodes.length == 0)
				displayProfileAppInput(idx, "");
			else
				displayProfileAppInput(idx, menu[menulevel][idx].firstChild.nodeValue);
			return;
		}
	}
	else
	{
		// check if the next menu level exists, and if not don't do anything
		if (menu[menulevel+1].length == 0) return;
		if (menu[menulevel+1][0].nodeName == "Redirect")
		{
			var xp = menu[menulevel+1][0].getAttribute("xpath");
			menu[menulevel+1] = selectNodes(menu[0][0], xp);
			if (menu[menulevel][idx].attributes.getNamedItem("name"))
				menuname[menulevel+1] = menu[menulevel][idx].getAttribute("name");
			else
				menuname[menulevel+1] = menu[menulevel][idx].nodeName;
			menulevel++;
			menupage[menulevel] = 0;
			updateMenu();
			return;
		}
		else
		{
			menuname[menulevel+1] = menu[menulevel][idx].nodeName;
			if (menu[menulevel][idx].attributes.length > 0)
			{
				if (menu[menulevel][idx].attributes.getNamedItem("name"))
					menuname[menulevel+1] = menu[menulevel][idx].getAttribute("name");
			}
			if (menu[menulevel][idx].attributes.getNamedItem("type"))
			switch(menu[menulevel][idx].getAttribute("type"))
			{
			case "integer":
				var val = menu[menulevel][idx].firstChild.nodeValue;	//.text;
				var min = menu[menulevel][idx].getAttribute("min");
				var max = menu[menulevel][idx].getAttribute("max");
				displayIntegerInput(idx, val, min, max);
				return;
			case "profileapp":
				if (menu[menulevel][idx].childNodes.length == 0)
					displayProfileAppInput(idx, "");
				else
					displayProfileAppInput(idx, menu[menulevel][idx].firstChild.nodeValue);
				return;
			case "string":
				if (menu[menulevel][idx].childNodes.length == 0)
					displayStringInput(idx, "");
				else
					displayStringInput(idx, menu[menulevel][idx].firstChild.nodeValue);
				return;
			case "file":
				if (menu[menulevel][idx].childNodes.length == 0)
					displayFileInput(idx, "");
				else
					displayFileInput(idx, menu[menulevel][idx].firstChild.nodeValue);
				return;
			}
			if (menu[menulevel+1].length > 0)
			{
				xpath.push("[" + idx + "]/" + menu[menulevel][idx].nodeName);
				menulevel++;
				menupage[menulevel] = 0;
				if (menu[menulevel].length == 1)
				{
					if (menu[menulevel][0].attributes.length > 0)
						if (menu[menulevel][0].getAttribute("skip") == "0")
						{
							setTimeout("onSelect(0);", 50);
							return;
						}
				}
			}
		}
	}
	updateMenu();
}

function addKeymap(idx)
{
	var map = menu[menulevel][idx].childNodes[0].cloneNode(true);
	var ln = menu[menulevel][idx].parentNode.childNodes.length - 1;
	menu[menulevel][idx].parentNode.insertBefore(map, menu[menulevel][idx].parentNode.childNodes[ln]);
	updateMenu();
}

function chkIntegerInput(idx, value, min, max, orig)
{
	if (value.validInteger())
	{
		value = parseInt(value, 10);
		if (value != NaN)
		{
			if (value > 1E+15) { alert("Value is too big."); return false; }
			var minok = false;
			var maxok = false;
			if (min == null) 
				minok = true;
			else 
				if (value >= min) 
					minok = true;
			if (max == null) 
				maxok = true;
			else 
				if (value <= max) 
					maxok = true;
			if (minok && maxok) {
				//menu[menulevel + 1][0].nodeValue = value;
				menu[menulevel][idx].firstChild.nodeValue = value;
				updateMenu();
				return false;	//true;
			}
		}
	}
	if (max == null)
		alert("Value must be greater than "+min);
	else if (min == null)
		alert("Value must be less than "+max);
	else
		alert("Value must be between "+min+" and "+max);
	document.getElementById("intinput").myint.value = orig;
	document.getElementById("intinput").myint.select();
	return false;
}

function displayIntegerInput(idx, value, min, max)
{
	updateMenuBar("");

	var html;
	html =
		"<div class=\"heading\">" + menuname[menulevel+1] + "</div> \
		<form name=\"intinput\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkIntegerInput("+idx+", this.myint.value, "+min+", "+max+", "+value+");\"> \
		<input class=\"txt\" name=\"myint\" type=\"text\" value=\""+value+"\"> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkIntegerInput("+idx+", myint.value, "+min+", "+max+", "+value+");\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"intinput\").myint.select();", 100);
}

function chkStringInput(idx, value, orig)
{
	//if ((value >= min) && (value <= max))
	//{
		//menu[menulevel+1][0].text = value;
		if (menu[menulevel][idx].childNodes.length == 0)
		{
			var tn = xmldocblank.createTextNode(value);
			menu[menulevel][idx].appendChild(tn);
		}
		else
			menu[menulevel][idx].firstChild.nodeValue = value;
		updateMenu();
		return false;	//true;
	//}
	//alert("Value must be between "+min+" and "+max);
	//document.getElementById("strinput").mystr.value = unescape(orig);
	//document.getElementById("strinput").mystr.select();
	//return false;
}

function displayStringInput(idx, value)
{
	updateMenuBar("");

	var html;
	html =
		"<div class=\"heading\">" + menu[menulevel][idx].getAttribute("name") + "</div> \
		<form id=\"strinput\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkStringInput("+idx+", this.mystr.value, '"+escape(value)+"');\"> \
		<input class=\"txt\" name=\"mystr\" type=\"text\" value='"+value+"'/> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkStringInput("+idx+", mystr.value, '"+escape(value)+"');\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"strinput\").mystr.select();", 100);
}

function chkFileInput(idx, value, orig){
	if (value.length > 0) {
		var ret = value.validFilename(); //fnCheckFilename(value);
		if (!ret) 
			alert(value + " contains invalid characters!");
		else 
			if (value.length > MAX_PATH) 
				alert("The folder name is too long.\r\nPlease enter a shorter folder name.");
			else {
				//menu[menulevel+1][0].text = value;
				if (menu[menulevel][idx].childNodes.length == 0) {
					var tn = xmldocblank.createTextNode(value);
					menu[menulevel][idx].appendChild(tn);
				}
				else 
					menu[menulevel][idx].firstChild.nodeValue = value;
				updateMenu();
				return false; //true;
			}
	}
	else alert("Zero length input is invalid.\r\nPlease enter a valid folder name.");
	//alert("Value must be between "+min+" and "+max);
	//document.getElementById("fileinput").fname.value = unescape(orig);
	//document.getElementById("fileinput").fname.select();
	return false;
}

function displayFileInput(idx, value)
{
	updateMenuBar("");

	var html;
	html =
		"<div class=\"heading\">" + menu[menulevel][idx].getAttribute("name") + "</div> \
		<form id=\"fileinput\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkFileInput("+idx+", fname.value, '"+escape(value)+"');\"> \
		<input class=\"txt\" name=\"fname\" type=\"text\" value='"+value+"'/> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkFileInput("+idx+", fname.value, '"+escape(value)+"');\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"fileinput\").fname.select();", 100);
}

function chkRename(idx, name, orig)
{
	name = name.trim();
	if (name.length == 0)
	{
		alert("Invalid entry.  Please try adding some characters.");
		return false;
	}
	var chk = false, dup = true;
	var errmsg = " contains invalid characters!";
	switch(menu[menulevel][idx].parentNode.nodeName)
	{
		case "Profile":
			if (name.length > MAX_PROFILENAME)
				errmsg = " is too long. Please shorten.";
			else
			chk = name.validProfilename();		//fnCheckString(value);
			if (chk) 
				if (name == menu[menulevel][idx].parentNode.getAttribute("filename"))
					dup = false;
				else
					dup = chk4DuplicateProfileName(name);
			break;
		case "Path":
			chk = name.validString();		//fnCheckString(value);
			if (chk)
				dup = chk4DuplicateDatapathName(name);
			break;
		case "Rule":
			chk = name.validString();		//fnCheckString(value);
			if (chk)
				dup = chk4DuplicateRuleName(name);
			break;
		case "Application":
			var re=/(.)+\.exe$/i;
			if (re.test(name))
				chk = name.validFilename();
			else
				errmsg = " is not a valid application.";
			dup = false;
			if (name.toLowerCase() != orig.toLowerCase())
			{
				dup = chk4DuplicateApplication(name); //false;
				if (dup) 
					return false;
			}
			break;
	}
	if (!chk)
		alert(name + errmsg);
	else
	{
		if (dup) {
			alert(name + " is already taken!");
			return false;
		}
		menu[menulevel][idx].parentNode.setAttribute("name", name);
		switch (menu[menulevel][idx].parentNode.nodeName) {
			case "Application":
				menu[menulevel][idx].parentNode.setAttribute("value", name);
				break;
		}
		menuname[menulevel] = name;
		updateMenu();
		return false;	//true;
	}
	//document.getElementById("rename").rname.value = unescape(orig);
	//document.getElementById("rename").rname.select();
	return false;
}

function displayRename(idx)	//, value)
{
	var name = menu[menulevel][idx].parentNode.getAttribute("name");
	updateMenuBar("");

	var html;
	html =
		"<div class=\"heading\">" + name + "</div> \
		<form id=\"rename\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkRename("+idx+", rname.value, '"+escape(name)+"');\"> \
		<input class=\"txt\" name=\"rname\" type=\"text\" value='"+name+"'/> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkRename("+idx+", rname.value, '"+escape(name)+"');\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"rename\").rname.select();", 100);
}

function generateProfileName()
{
	var i = 1, j;
	var pname, sname, pfname;
	var profile = new Array();
	profile = menu[0][0].getElementsByTagName("Profile");
	while(1)
	{
		sname = "Profile"+i;
		for (j=0; j<profile.length; j++)
		{
			pname = profile[j].getAttribute("name");
			if (pname.toLowerCase() == sname.toLowerCase()) break;
			pfname = profile[j].getAttribute("filename");
			if (pfname != null)
			if (pfname.toLowerCase() == sname.toLowerCase()) break;
		}
		if (j == profile.length)
			break;
		i++;
	}
	return sname;
}

function generateDatapathName()
{
	var i = 1, j;
	var pname, sname;
	var profile = new Array();
	profile = menu[0][0].getElementsByTagName("Path");
	while(1)
	{
		sname = "Route"+i;
		for (j=0; j<profile.length; j++)
		{
			pname = profile[j].getAttribute("name");
			if (pname.toLowerCase() == sname.toLowerCase())
			{
				break;
			}
		}
		if (j == profile.length)
			break;
		i++;
	}
	return sname;
}

function generateRuleName()
{
	var i = 1, j;
	var attr, suggest;
	var nodelist = new Array();
	nodelist = menu[0][0].getElementsByTagName("Rule");
	while(1)
	{
		suggest = "Rule"+i;
		for (j=0; j<nodelist.length; j++)
		{
			attr = nodelist[j].getAttribute("name");
			if (attr.toLowerCase() == suggest.toLowerCase())
			{
				break;
			}
		}
		if (j == nodelist.length)
			break;
		i++;
	}
	return suggest;
}

// Function will return true if legal, false if not.
// It will also return false unless the string contains at least one character.
// URI reserved chars = ";" | "/" | "?" | ":" | "@" | "&" | "=" | "+" | "$" | ","
// URI unreserved chars = "-" | "_" | "." | "!" | "~" | "*" | "'" | "(" | ")"
// URI excluded chars = "<" | ">" | "#" | "%" | <">
// URI unwise chars = "{" | "}" | "|" | "\" | "^" | "[" | "]" | "`"
String.prototype.validString = function()
{
	var re=/^[A-Za-z0-9!£\(\)_~ \-\.]+$/;
    return re.test(this);
}

String.prototype.validProfilename = function()
{
	var re=/^[A-Za-z0-9!£\(\)_~ \-]+$/;
    return re.test(this);
}

String.prototype.validFilename = function()
{
	var re=/^[A-Za-z0-9!£\(\)_~ \-\.\\]+$/;
    return re.test(this);
}

String.prototype.validInteger = function()
{
	var re=/^[0-9]+$/;
    return re.test(this);
}

String.prototype.consecutiveDots = function()
{
	var re=/\.{2,}/;
	return re.test(this);
}

String.prototype.trim = function()
{
    //return this.replace(/^\s+|\s+$/g,"");
	return this.replace(/^[\s\s]*/, '').replace(/[\s\s]*$/, '');
}

String.prototype.hardspace = function()
{
	if (this.length == 0)
		return "&nbsp;";
	else
		return this.replace(/ /g, '&nbsp;');
}

function chk4DuplicateProfileName(name)
{
	var j;
	var pname, pfilename;
	var profile = new Array();
	profile = menu[0][0].getElementsByTagName("Profile");
	for (j=0; j<profile.length; j++)
	{
		pname = profile[j].getAttribute("name");
		if (pname.toLowerCase() == name.toLowerCase()) return true;
		pfilename = profile[j].getAttribute("filename");
		if (pfilename != null)
			if (pfilename.toLowerCase() == name.toLowerCase()) return true;
	}
	return false;
}

function chk4DuplicateDatapathName(name)
{
	var j;
	var pname;
	var profile = new Array();
	profile = menu[0][0].getElementsByTagName("Path");
	for (j=0; j<profile.length; j++)
	{
		pname = profile[j].getAttribute("name");
		if (pname.toLowerCase() == name.toLowerCase()) return true;
	}
	return false;
}

function chk4DuplicateRuleName(name)
{
	var j;
	var attrname;
	var nodelist = new Array();
	nodelist = menu[0][0].getElementsByTagName("Rule");
	for (j=0; j<nodelist.length; j++)
	{
		attrname = nodelist[j].getAttribute("name");
		if (attrname.toLowerCase() == name.toLowerCase()) return true;
	}
	return false;
}

var creatingProfile = false;
function chkProfileInput(name, sname)
{
	if (creatingProfile) return false;
	name = name.trim();
	if (name.length == 0) 
		alert("Invalid entry.  Please try adding some characters.");
	else 
	if (name.length > MAX_PROFILENAME)
		alert("Profile name is too long, please shorten.");
	else
	if ((name.toLowerCase() == "default") || (name.toLowerCase() == "profile0"))
		alert(name + " is reserved.  Please try another.");
	else
	{
		var ret = name.validProfilename(); //fnCheckString(name);
		if (!ret) 
			alert(name + " contains invalid characters!");
		else {
			ret = !chk4DuplicateProfileName(name);
			if (!ret) 
				alert(name + " is already taken!");
			else
			{
				if (!ping()) {
					alert("Error contacting server.  DataWedge may not be running.");
					//return false;
				}
				else {
					creatingProfile = true;
					statusBar("Creating profile, please wait!")
					setTimeout("precreateNewProfile('" + name + "');", 100);
					//createNewProfile(name);
					//updateMenu();
				}
			}
		}
	}
	return false;
}

function chkDatapathInput(name, sname)
{
	name = name.trim();
	if (name.length == 0) 
		alert("Invalid entry.  Please try adding some characters.");
	else {
		var ret = name.validString(); //fnCheckString(name);
		if (!ret) 
			alert(name + " contains invalid characters!");
		else {
			ret = !chk4DuplicateDatapathName(name);
			if (!ret) 
				alert(name + " is already taken!");
		}
		if (!ret) {
			//document.getElementById("datapathinput").pname.value = unescape(sname);
			//document.getElementById("datapathinput").pname.select();
		}
		else {
			createNewDatapath(name);
			updateMenu();
		}
	}
	return false;	//ret;
}

function chkRuleInput(idx, name, sname)
{
	name = name.trim();
	if (name.length == 0) 
		alert("Invalid entry.  Please try adding some characters.");
	else {
		var ret = name.validString(); //fnCheckString(name);
		if (!ret) 
			alert(name + " contains invalid characters!");
		else {
			ret = !chk4DuplicateRuleName(name);
			if (!ret) 
				alert(name + " is already taken!");
		}
		if (!ret) {
		//document.getElementById("ruleinput").rname.value = unescape(sname);
		//document.getElementById("ruleinput").rname.select();
		}
		else {
			createNewRule(idx, name);
			updateMenu();
		}
	}
	return false;	//ret;
}

function precreateNewProfile(name)
{
	updateBody("<div class=\"heading\">New profile: "+name+"</div><br/>");
	setTimeout("createNewProfile('"+name+"');", 10);
}

function createNewProfile(name)
{
	var ret, errors = false;
	try {
		var prfltemp = uiProfileTemplate.documentElement.cloneNode(true);
		
		prfltemp.setAttribute("name", name);
		var filename = encodeURI(name);
		prfltemp.setAttribute("filename", filename);
		ret = addPlugins2Profile(prfltemp);
		if (!ret) errors = true;
		
		ret = createDefaultDatapath(prfltemp);
		if (!ret) errors = true;
		
		var ren = xmldocblank.createElement("Rename");
		prfltemp.appendChild(ren);
		var del = xmldocblank.createElement("Delete");
		del.setAttribute("type", "delete");
		prfltemp.appendChild(del);

		var an = selectNodes(menu[0][0].firstChild, "Profile[@type='add']");
		menu[0][0].firstChild.insertBefore(prfltemp, an[0]);
		numProfiles++;
		
		// need to add profile to DWconfig.xml
		var dwprfls = selectNodes(dwconfig, "//Profiles");
		var pfl = xmldocblank.createElement("Profile");
		
		pfl.setAttribute("name", name);
		pfl.setAttribute("filename", filename);
		pfl.setAttribute("active", "1");
		dwprfls[0].appendChild(pfl);
	}
	catch(e){
		alert("Unexpected error.  Unable to create profile.\r\n\r\n"+e.description);
		errors = true;
	}	

	if (!errors)
	{
		filename = "/config/profiles/" + filename + ".xml";
		var str = createProfileString(name, menu[menulevel][0].parentNode);
		ret = puturl(filename, str);
		if (ret != null) {
			writeDWConfig();
			writeMenu();
		}
		else {
			alert("Error writing profile. DataWedge may not be running.\r\n\r\n");
			// need to delete the profile from the menu tree
		}
	}
	
	statusBar("");
	updateMenu();
	return true;
}

function createDefaultDatapath(prfl)
{
	try
	{
		var pathtemp = uiDatapathTemplate.documentElement.cloneNode(true);
		pathtemp.setAttribute("name", "Route0");
		pathtemp.setAttribute("id", "Route0");
		var ret = addPlugins2Datapath(pathtemp);
		if (!ret) return false;
		var del = xmldocblank.createElement("Delete");
		del.setAttribute("type", "delete");
		pathtemp.appendChild(del);
		var pn = selectNodes(prfl, "//Path[@id='Route0']")[0];
		pn.parentNode.replaceChild(pathtemp, pn);
		addDecoders2ProfileCriteria(prfl);
	}
	catch(e)
	{
		alert("Error creating default route.\r\n\r\n"+e.description);
		return false;
	}
	return true;
}

function createNewDatapath(name)
{
	var errors = false;
	try
	{
		var pathtemp = uiDatapathTemplate.documentElement.cloneNode(true);
		pathtemp.setAttribute("name", name);
		pathtemp.setAttribute("id", name);
		var ret = addPlugins2Datapath(pathtemp);
		if (!ret) errors = true;
		ret = addDecoders2DatapathCriteria(pathtemp);
		if (!ret) errors = true;
		var del = xmldocblank.createElement("Delete");
		del.setAttribute("type", "delete");
		pathtemp.appendChild(del);
		var pn = menu[menulevel][0].parentNode;
		var cn = menu[menulevel].length-1;
		pn.insertBefore(pathtemp, menu[menulevel][cn]);
	}
	catch(e)
	{
		errors = true;
		alert(e.description);
	}
	if (errors)
		alert("Unexpected error.  Unable to create route.\r\n\r\n");
}

function createNewRule(idx, name)
{
	var newdevice, desc, decoderlist, newdecoder, tn;
	try
	{
		var ruleclone = menu[menulevel][idx].cloneNode(true);
		ruleclone.setAttribute("name", name);
		ruleclone.setAttribute("id", name);
		ruleclone.removeAttribute("type");
		// now generate the device list
		var devicelist = selectNodes(menu[0][0], xpathRoot + "/Input//Device");
		for (i=0; i<devicelist.length; i++)
		{
			newdevice = menu[menulevel][idx].getElementsByTagName("Device")[0].cloneNode(true);
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
				ruleclone.getElementsByTagName("Devices")[0].replaceChild(newdevice, ruleclone.getElementsByTagName("Device")[0]);
			else
				ruleclone.getElementsByTagName("Devices")[0].appendChild(newdevice);
		}
		// now generate the decoder list
		menu[menulevel][idx].parentNode.insertBefore(ruleclone, menu[menulevel][idx]);
	}
	catch(e)
	{
		alert("Unexpected error.  Unable to create rule.\r\n\r\n"+e.description);
	}
}

function displayProfileInput(idx, name)
{
	creatingProfile = false;
	updateMenuBar(" > " + menu[menulevel][idx].getAttribute("name"));

	var html;
	html =
		"<div class=\"heading\">New profile name:</div> \
		<form id=\"profileinput\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkProfileInput(this.pname.value, '"+escape(name)+"');\"> \
		<input class=\"txt\" name=\"pname\" type=\"text\" value='"+name+"'> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkProfileInput(pname.value, '"+escape(name)+"');\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"profileinput\").pname.select();", 100);
	//setTimeout("alert(document.getElementById(\"profileinput\"));", 100);
}

function displayDatapathInput(idx, name)
{
	updateMenuBar(" > " + menu[menulevel][idx].getAttribute("name"));

	var html;
	html =
		"<div class=\"heading\">New route name:</div> \
		<form id=\"datapathinput\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkDatapathInput(this.pname.value, '"+escape(name)+"');\"> \
		<input class=\"txt\" name=\"pname\" type=\"text\" value='"+name+"'> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkDatapathInput(pname.value, '"+escape(name)+"');\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"datapathinput\").pname.select();", 100);
}

function chk4DuplicateApplication(name)
{
	var apps = selectNodes(menu[0][0], "//Application");
	var val;
	if (apps.length > 0)
	{
		for (i=0; i<apps.length; i++)
		{
			val = apps[i].getAttribute("value");
			if (val == null) continue;
			if (val.toLowerCase() == name.toLowerCase())
			{
				var pfl = apps[i].parentNode.parentNode.getAttribute("name");
				alert(name+" is already assigned to "+pfl);
				return true;
			}
		}
	}
	return false;
}

function chkProfileAppInput(idx, name, sname)
{
	name = name.trim();
	var i;
	//if (name.indexOf(".exe") < 1)
	var re=/(.)+\.exe$/i;
	if (!re.test(name))
	{
		alert("Invalid application name.");
		//document.getElementById("profileappinput").pname.value = unescape(sname);
		//document.getElementById("profileappinput").pname.select();
		return false;
	}
	var ret = name.validString();		//fnCheckString(name);
	if (!ret)
	{
		alert(name+" contains invalid characters!");
		return false;
	}
	//var apps = selectNodes(menu[0][0], "//Application");
	//if (apps.length > 0)
	//{
	//	for (i=0; i<apps.length; i++)
	//	{
	//		if (apps[i].getAttribute("value") == name)
	//		{
	//			var pfl = apps[i].parentNode.parentNode.getAttribute("name");
	//			alert(name+" is already assigned to "+pfl);
	//			return false;
	//		}
	//	}
	//}
	if (chk4DuplicateApplication(name)) return false;

	//menu[menulevel+1][0].text = name;
	var n = xmldocblank.createElement("Application");
	n.setAttribute("value", name);
	n.setAttribute("name", name);
	var edit = xmldocblank.createElement("Edit");
	edit.setAttribute("type", "edit");
	n.appendChild(edit);
	var del = xmldocblank.createElement("Delete");
	del.setAttribute("type", "delete");
	n.appendChild(del);
	menu[menulevel][0].parentNode.insertBefore(n, menu[menulevel][menu[menulevel].length-1]);
	//menu[menulevel][0].parentNode.appendChild(n);
	updateMenu();
	return false;	//true;
}

function displayProfileAppInput(idx, name)
{
	updateMenuBar(" > " + menu[menulevel][idx].nodeName);

	var html;
	html =
		"<div class=\"heading\">Application (.exe) name:</div> \
		<form id=\"profileappinput\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkProfileAppInput("+idx+", this.pname.value, '"+escape(name)+"');\"> \
		<input class=\"txt\" name=\"pname\" type=\"text\" value='"+escape(name)+"'> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkProfileAppInput("+idx+", pname.value, '"+escape(name)+"');\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"profileappinput\").pname.select();", 100);
}

function displayRuleInput(idx, name)
{
	updateMenuBar(" > " + menu[menulevel][idx].nodeName);

	var html;
	html =
		"<div class=\"heading\">Rule name:</div> \
		<form id=\"ruleinput\" action=\"\" method=\"GET\" \
		onsubmit=\"return chkRuleInput("+idx+", this.rname.value, '"+escape(name)+"');\"> \
		<input class=\"txt\" name=\"rname\" type=\"text\" value='"+name+"'> \
		<p>Press ENTER to save or tap Cancel below.</p> \
		<input class=\"btn\" name=\"sav\" type=\"button\" value=\"Save\" onclick=\"chkRuleInput("+idx+", rname.value, '"+escape(name)+"');\" /> \
		<input class=\"btn\" name=\"cancel\" type=\"button\" value=\"Cancel\" onclick=\"updateMenu();\" /> \
		</form>";
	//html += "<script>document.form.int.setfocus();</script>";
	document.getElementById("centerpanel").innerHTML = html;
	keytrap = false;
	setTimeout("document.getElementById(\"ruleinput\").rname.select();", 100);
}

function gotoMenuLevel(idx)
{
	if (!keytrap) return;
	if (processing) return;
	//alert(idx + " - " + menulevel);
	while (menupage[menulevel] > 0)
	{
		onSelect(777);
	}
	if (idx == menulevel)  updateMenu();
	while (idx < (menulevel-1))
	{
		onSelect(777);
	}
	if (idx < menulevel) onSelect(666);
}

function updateMenuBar(txt)
{
	//var bar = "";
	//for (i=0; i<=menulevel; i++)
	//{
	//	if (i>0) bar += " > ";
	//	bar += "<a href='#' onclick='gotoMenuLevel("+i+");'>" + menuname[i] + "</a>";
	//}
	var i = 0;
	var bar = menuname[i++];
	while (i <= menulevel)
	{
		if (i > 1) bar += " > "; else bar += ": ";
		bar += "<a href='#' onclick='gotoMenuLevel("+i+");'>" + menuname[i] + "</a>";
		i++;
	}
	bar += txt;
	document.getElementById("toppanel").innerHTML = bar;
	document.getElementById("centerpanel").innerHTML = "";
}

// doesn't work in IEMobile :(
function getWidth(text)
{
	var width = 0;
	try {
		var spanElement = document.createElement("span");
		spanElement.style.whiteSpace = "nowrap";
		spanElement.innerHTML = text;
		document.body.appendChild(spanElement);
		width = spanElement.offsetWidth;
		document.body.removeChild(spanElement);
		return width;
	}
	catch(e) {
		alert(e.description);
	}
	return width;
}

// doesn't work either in IEMobile :(
function getWidth2(text)
{
	var width = 0;
	var se = document.getElementById("sizer");
	se.innerHTML = text;
	try{
		width = se.offsetWidth;
	}
	catch(e) { alert(e.description); }
	se.innerHTML = "";
	return width;
}

var charsize = new Array(4,4,6,10,8,14,8.1,3,5,5,8,10,4,5,4,5,8,8,8,8,8,8,8,8,8,8,5,5,9,10,10,7,13,8,8,9,10,8,7,9,9,4,6,8,7,10,9,10,8,10,9,8,8,9,8,14,8,8,8,5,5,5,10,8,8,7,8,7,8,7,4,8,8,2,4,7,2,12,8,8,8,8,5,6,5,8,8,10,8,8,6,7,5,7,10,14)
function getStringWidth(txt)
{
	var idx, width = 0;
	for (var i=0; i<txt.length; i++)
	{
		idx = txt.charCodeAt(i);
		if (idx < 32 || idx > 128)
			width += 8;
		else
			width += charsize[idx - 32];
	}
	return width;
}

String.prototype.fitToWidth = function(px)
{
	var idx, width, sum = 0;
	var str = unescape(this);
	for (var i=0; i<str.length; i++)
	{
		idx = str.charCodeAt(i);
		if (idx < 32 || idx > 128)
			width = 8;	// 8 is the average character width for font-size:14px
		else
			width = charsize[idx - 32];
		if (sum + width > px) return this.substring(0, i-1) + "..";
		sum += width;
	}
	return this;
}

function rowWidth(percent)
{
	// 16 is to allow for the width of the scroll bar
	// 44/57 is the ratio of the <li> indent in One Column view mode in IEMobile
	if (isIEMobile()) return ((screen.width - 17) * 40 / 57) * percent;
	//  clientWidth should return the offsetWidth less the scrollbar width (or close enough)
	return (document.body.clientWidth * percent) - 16;
}

function updateMenu()
{
	keytrap = true;
	//alert(location.href);
	updateMenuBar("");

	var node, val, view;
	var sctxt, txt, sub;
	var img = " ";
	var more = false;
	var hide;
	mainmenu.clear();
	var len = menu[menulevel].length;
	var anfang = menupage[menulevel]*8;
	var ende;
	if ((len - anfang) > 9) { ende = anfang+8; more = true;}
	else { ende = len;}
	for (i=anfang; i<ende; i++)
	{
		node = menu[menulevel][i];
		if (node.nodeType == nodeType.Text) continue;
		if (node.nodeType == nodeType.Comment) continue;
		sub = "...";
		if (node.hasChildNodes())
			if (node.firstChild.nodeType == nodeType.Text)
				sub = node.firstChild.nodeValue;
		hide = false;
		view = null;
		sctxt = shortcut.charAt(i-anfang) + ".";
		txt = node.nodeName;
		img = _blank;
		if (node.attributes.length > 0)
		{
			if (node.attributes.getNamedItem("name"))
				txt = node.getAttribute("name");
			if (txt.length == 0) txt = " ";
			if (node.attributes.getNamedItem("type"))
			{
				switch(node.getAttribute("type"))
				{
				case "bool":
					sub = " ";
					if (node.firstChild.nodeValue == "1")	//.text
						img = _ticked;
					break;
				case "integer":
					//sub = node.firstChild.nodeValue;	//"&nbsp;";	.text
					//if (sub.length == 0) sub = "...";
					break;
				case "file":
				case "string":
					//sub = "...";
					//if (node.childNodes.length > 0) {
					//	val = node.firstChild.nodeValue; //.text
					//	if (val.length > 0) 
					//		sub = val;
					//}
					break;
				case "select":
					var opt = node.childNodes;
					var oid = node.getAttribute("oid");
					var len = opt.length;
					for (var j=0; j<len; j++)
					{
						if (opt[j].getAttribute("id") == oid)
						{
							sub = opt[j].getAttribute("name");
							//sub = sub.substring(0,4);
							break;
						}
					}
					break;
				case "function":
					sub = " ";
					break;
				case "fixed":
					break;
				case "hidden":
					continue;
					break;
				}
			}
			if (node.parentNode.attributes.getNamedItem("type"))
			{
				switch(node.parentNode.getAttribute("type"))
				{
				case "select":
					if (node.nodeName == "option")
					{
						if (node.parentNode.getAttribute("value") == node.getAttribute("value"))
							img = _ticked;
					}
					break;
				case "displayonly":
					sctxt = "&nbsp;";
					break;
				case "integer":
					break;
				case "fixed":
					if (node.parentNode.getAttribute("value") != node.getAttribute("id"))
						hide = true;
					break;
				case "hidden":
					continue;
					break;
				}
			}
			else
			if (node.attributes.getNamedItem("enabled"))
			{
				switch(node.getAttribute("enabled"))
				{
				case "1":
					img = _ticked;
				}
			}
			if (node.hasChildNodes())
			{
				if (node.firstChild.nodeName == "Enabled")
				  if (node.firstChild.firstChild.nodeValue == "1")
						img = _ticked;
			}
		}
		else
		if (node.hasChildNodes())
		if (node.childNodes[0].nodeType == nodeType.Text)
		{
		  txt = node.childNodes[0].nodeValue;
		  sub = " ";
		}
		if (node.childNodes.length == 0)
			sub = " ";
		//if ((sub.length > 0) || (node.attributes.length > 0))
		if ((node.nodeName == "Action") && (node.parentNode.nodeName == "Action")) sub = " ";
		//if ((node.nodeName == "Mapping") && (node.parentNode.nodeName == "Mapping")) sub = " ";
		if ((node.nodeName == "Mapping") && (node.getAttribute("type") == null))
			sub = node.childNodes[0].childNodes[0].nodeValue +":"+ node.childNodes[1].childNodes[0].nodeValue;
		if (!hide)
		mainmenu.add("onSelect("+(i-anfang)+");", img, sctxt, txt.fitToWidth(rowWidth(0.65)).hardspace(), sub.fitToWidth(rowWidth(0.20)).hardspace());
	}
	if (more)
		mainmenu.add("onSelect(8);", "&nbsp;", "9.", "More", "...");
	if (menulevel > 1)
	{
		//mainmenu.add("onSelect(666);", "images/chkbox_blank.bmp", "0. ", "Back", "");
		mainmenu.add("onSelect(666);", "&nbsp;", "0.", "Back", "&nbsp;");
	}
	else
		mainmenu.add("onSelect(-1);", "&nbsp;", "0.", "Exit", "&nbsp;");
	document.getElementById("centerpanel").innerHTML = mainmenu.html();
	//this.centerpanel.innerHTML = mainmenu.html();
	//de = new Date();
	//statusBar(de.getTime()-ds.getTime());
}

function updateBody(txt)
{
	document.getElementById("centerpanel").innerHTML = txt;
}

function dwmenu()
{
	var _html = new Array();

	this.clear = clear;
	this.add = add;
	this.html = html;

	function clear()
	{
		_html = new Array();
	}

	function add(func, img, sc, txt1, txt2)
	{
		var len = _html.length;
		var c1 = "c1";
		//if (img != "&nbsp;") c1 = "c1t";
		_html.push(
			//"<table id=\"t"+_html.length+"\" cellpadding=\"0\" cellspacing=\"0\"> \
			//"<tr class=\"r"+_html.length % 2+"\"> \
			//<td style=\"background-color: White;\"><img src=\""+img+"\"></td> \
			//<td><a href=\"#\" onclick=\""+func+"\">"+sc+"</a></td> \
			//<td width=100%> \
			//<a href=\"#\" onclick=\""+func+"\"> \
			//<div>"+txt1+"</div></a></td> \
			//<td><a href=\"#\" onclick=\""+func+"\">"+txt2+"</a></td> \
			//</tr>");	//</table>");
			//
		"<ul class='r"+len%2+"'> \
		<li id='img"+len+"' class='"+c1+"'>"+img+"</li> \
		<li id='c2' class='c2'>"+sc+"</li> \
		<li id='c3' class='c3'><a name='' onclick='"+func+"'>"+txt1+"</a></li> \
		<li id='c4' class='c4'>"+txt2+"</li>\
		</ul>");
	}
	
	function html()
	{
		var htm = "";
		var len = _html.length;
		for (i=0; i<len; i++)
		{
			//htm += _html[i];
			htm = _html.pop() + htm;
		}
		delete _html;
		//return "<table id=\"t"+len+"\" cellpadding=\"0\" cellspacing=\"0\">" + htm + "</table>";
		return htm;
	}
}



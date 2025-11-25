var duration = 5 // Specify duration of progress bar in seconds
var _progressWidth = 42;	// Display width of progress bar.

var _progressBar = "|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||"
var _progressEnd = 42;
var _progressAt = 0;


// Create and display the progress dialog.
// end: The number of steps to completion
function progressBarCreate(end) {
	// Initialize state variables
	_progressEnd = end;
	_progressAt = 0;

	document.getElementById("centerpanel").innerHTML = "";
	progressBarUpdate();	// Initialize bar
}

// Hide the progress layer
function progressBarDestroy() {
	document.getElementById("centerpanel").innerHTML = "";
}

// Increment the progress dialog one step
function progressBarStepIt() {
	_progressAt++;
	if(_progressAt > _progressEnd) _progressAt = _progressAt % _progressEnd;
	progressBarUpdate();
}

// Update the progress dialog with the current state
function progressBarUpdate() {
	var n = (_progressWidth / _progressEnd) * _progressAt;
	var temp = _progressBar.substring(0, n);
	document.getElementById("centerpanel").innerHTML = temp;
}

// Demonstrate a use of the progress dialog.
function progressBarDemo() {
	progressBarCreate(10);
	window.setTimeout("Click()", 100);
}

function progressBarClick() {
	if(_progressAt >= _progressEnd) {
		progressBarDestroy();
		return;
	}
	progressBarStepIt();
	window.setTimeout("progressBarClick()", (duration-1)*1000/10);
}

function callJS(jsStr) { //v2.0
  return eval(jsStr)
}

var _pbString = "";
function progressBarStepIt2()
{
	_pbString += "|";
	document.getElementById("centerpanel").innerHTML = _pbString;
	if (_pbString.length > 41) _pbString = "";
}
"use strict";

/*function saveResults() {
	var fs = require('fs');
	var path = 'output.json';
	var info = [{"iterations":numTimesToExecute},
				{"sites":sites},
				{"timestamps":timestamps}];
	var content = JSON.stringify(info,null,0);
	fs.write(path,content,'w');
}*/

/*var addressArray = [
		'file:///home/odroid/bbench-3.0/sites/amazon/www.amazon.com/index.html',
		'file:///home/odroid/bbench-3.0/sites/bbc/www.bbc.co.uk/index.html', 
		'file:///home/odroid/bbench-3.0/sites/cnn/www.cnn.com/index.html', 
		'file:///home/odroid/bbench-3.0/sites/craigslist/newyork.craigslist.org/index.html', 
		'file:///home/odroid/bbench-3.0/sites/ebay/www.ebay.com/index.html', 
		'file:///home/odroid/bbench-3.0/sites/espn/espn.go.com/index.html', 
		'file:///home/odroid/bbench-3.0/sites/google/www.google.com/index.html', 
		'file:///home/odroid/bbench-3.0/sites/msn/www.msn.com/index.html', 
		'file:///home/odroid/bbench-3.0/sites/slashdot/slashdot.org/index.html', 
		'file:///home/odroid/bbench-3.0/sites/twitter/twitter.com/index.html', 
		'file:///home/odroid/bbench-3.0/sites/youtube/www.youtube.com/index.html']; */

var sites = [
	'amazon',
	'bbc', 
	'cnn',
	'craigslist', 
	'ebay',
	'espn', 
	'google',
	'msn', 
	'slashdot',
	'twitter', 
	'youtube'];

var timestamps = [];
var indices = [];
var numTimesToExecute = 1;
var loadpage = function (i, max){
	if (i === max) {
		phantom.exit();
		return;
	}
	var page = require('webpage').create(),
		system = require('system'),
		t, address;
	page.viewportSize = { width: 1920, height: 1080 };
	page.onError = function (msg,trace) {
		console.log(msg);
		trace.forEach(function(item) {
			console.log(' ',item.file,':',item.line);
		});
	};
	var addressArray = [
		'http://was42@tucunare.cs.pitt.edu:8080/amazon/www.amazon.com/',
		'http://was42@tucunare.cs.pitt.edu:8080/bbc/www.bbc.co.uk/', 
		'http://was42@tucunare.cs.pitt.edu:8080/cnn/www.cnn.com/', 
		'http://was42@tucunare.cs.pitt.edu:8080/craigslist/newyork.craigslist.org/', 
		'http://was42@tucunare.cs.pitt.edu:8080/ebay/www.ebay.com/', 
		'http://was42@tucunare.cs.pitt.edu:8080/espn/espn.go.com/', 
		'http://was42@tucunare.cs.pitt.edu:8080/google/www.google.com/', 
		'http://was42@tucunare.cs.pitt.edu:8080/msn/www.msn.com/', 
		'http://was42@tucunare.cs.pitt.edu:8080/slashdot/slashdot.org/', 
		'http://was42@tucunare.cs.pitt.edu:8080/twitter/twitter.com/', 
		'http://was42@tucunare.cs.pitt.edu:8080/youtube/www.youtube.com/'];
	var index = i%addressArray.length;//Math.floor(Math.random() * addressArray.length);
	indices.push(index);
	var address = addressArray[index];
	t = Date.now();
	timestamps.push(t);
	console.log('Loading ' + address);
	page.onLoadFinished = function (status) {
		if (status === 'success') {
			page.evaluate(function() {
				document.body.bgColor = 'white';
			});
			page.render('pics/' + sites[index] + '.jpeg');
			var time = Date.now();
			timestamps.push(time);
			t = time - t;
		}
	}
	page.open(address, function(status) {
		if (status !== 'success') {
			console.log('FAIL to load the address: '+address);
			phantom.exit();
		} else {
		}
		setTimeout(function () {
			console.log('sleeping...');
			loadpage(i+1, max)
		},5000);
	});
};

loadpage(3, numTimesToExecute*sites.length);
//saveResults();

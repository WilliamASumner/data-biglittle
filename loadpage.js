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
		'was42@tucunare.cs.pitt.edu:8080/amazon/',
		'was42@tucunare.cs.pitt.edu:8080/bbc/', 
		'was42@tucunare.cs.pitt.edu:8080/cnn/', 
		'was42@tucunare.cs.pitt.edu:8080/craigslist/', 
		'was42@tucunare.cs.pitt.edu:8080/ebay/', 
		'was42@tucunare.cs.pitt.edu:8080/espn/', 
		'was42@tucunare.cs.pitt.edu:8080/google/', 
		'was42@tucunare.cs.pitt.edu:8080/msn/', 
		'was42@tucunare.cs.pitt.edu:8080/slashdot/', 
		'was42@tucunare.cs.pitt.edu:8080/twitter/', 
		'was42@tucunare.cs.pitt.edu:8080/youtube/'];
	var nameArray = [
		'amazon', 'bbc', 
		'cnn', 'craigslist', 
		'ebay', 'espn', 
		'google', 'msn', 
		'slashdot', 'twitter', 
		'youtube'];

	var address = addressArray[Math.floor(Math.random() * addressArray.length)];
	//var address = addressArray[i % addressArray.length];
	t = Date.now();
	page.onLoadFinished = function () {
		page.render('pics/' + nameArray[i] + '.jpeg');
	}
	page.open(address, function(status) {
		if (status !== 'success') {
			console.log('FAIL to load the address');
			phantom.exit();
		} else {
			console.log('status: ' + status);
			//page.render("pics/" + nameArray[i] + '.jpeg',{format:'jpeg',quality:'100'});
			t = Date.now() - t;
			console.log('Loading ' + address);
			console.log('Loading time ' + t + ' msec');
		}

		loadpage(i+1, max)
	});
};

loadpage(0, 20);

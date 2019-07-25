var loadpage = function (i, max){
if (i === max) {
    phantom.exit();
    return;
}
var page = require('webpage').create(),
    system = require('system'),
    t, address;
var addressArray = ['http://www.amazon.com', 'http://www.cnn.com', 
                    'http://www.espn.com', 'http://www.youtube.com', 
                    'http://www.google.com', 'http://www.msn.com',                     
                    'http://www.slashdot.com', 'http://www.163.com'];    
var address = addressArray[Math.floor(Math.random() * addressArray.length)];
//var address = addressArray[i % addressArray.length];
t = Date.now();
page.open(address, function(status) {
    if (status !== 'success') {
        console.log('FAIL to load the address');
    } else {
        t = Date.now() - t;
        console.log('Loading ' + address);
        console.log('Loading time ' + t + ' msec');

    }

    loadpage(i+1, max)
});
};

loadpage(0, 2000);

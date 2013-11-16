var http = require('http');
var url = require('url');
var sys = require('sys');
var exec = require('child_process').exec;

function myexec(cmd, callback) {
	console.log("EXEC: " + cmd);
	exec(cmd, function(err, stdout, stderr) {
		if (err) {
			console.log("ERROR: " + err);
			return;
		}
		if (stdout) {
			console.log("=== stdout ===");
			console.log(stdout);
		}
		if (stderr) {
			console.log("=== stderr ===");
			console.log(stderr);
		}
		if (typeof callback === "function")
			callback();
	});
}

function newindex() {
	var git_dir = '/home/mirror/newindex';
	myexec("GIT_DIR=" + git_dir + "/.git GIT_WORK_TREE=" + git_dir + " git pull -q", function() {
		myexec("/home/mirror/newindex/genindex.py");
	});
}

var old_umask = process.umask(0000);
var sockfile = '/tmp/webhooks.sock';
require('fs').unlink(sockfile, main);

function main() {
	http.createServer(function(req, res) {
		var paths = req.url.split('/');
		var action = paths[paths.length - 1];
		console.log(action);
		switch (action) {
			case "newindex":
				newindex();
				res.writeHead(200);
				break;
			default:
				res.writeHead(404);
				break;
		}
		res.end();
	}).listen(sockfile, function() {
		process.umask(old_umask);
	});
}

// modules for creating a server
const http = require('http'); 
const fs = require('fs');
const path = require('path');
const querystring = require('querystring');
const cheerio = require('cheerio');
const fetch = require('node-fetch');
const Lyricist = require('lyricist/node6');
const lyricist = new Lyricist('9VF8J-loBbWDz-6g7fktj7tp34pMrHH4VWZ3PrWEwhFn_ngsgkE0A1K8POw2ja92');

// localhost:9005
const hostname = '127.0.0.1';
const port = 9005;

// Create server
const httpServer = http.createServer(function (req, res) {
  switch(req.method) {

    // handle GET requests
    case 'GET':
      console.log("received a GET for: " + req.url);
      
      if(req.url === '/' || req.url === '/extractData.html') {
        getExtractData(req, res);
      
      } else if(req.url === '/displayData.html') {
        getDisplayData(req, res);
        
      } else if(req.url === '/getArtistInfo') {
        getArtistInfo(req, res);
      
      // request for css files
      } else if (req.url.match(/.css$/)) {
        var pathName = path.join(__dirname, req.url);
        var fileStream = fs.createReadStream(pathName, "UTF-8");
        res.writeHead(200, {"Content-Type": "text/css"});
        fileStream.pipe(res);
      
        // request for javascript files
      } else if (req.url.match(/.js$/)) {
        var pathName = path.join(__dirname, req.url);
        var fileStream = fs.createReadStream(pathName, "UTF-8");
        res.writeHead(200, {"Content-Type": "text/javascript"});
        fileStream.pipe(res);
      } else {
        get404(req, res);
      }
      break;

    // Handle post requests
    case 'POST':
      console.log("received a POST for: " + req.url);
      if(req.url === '/getArtistInfo') {
        var reqBody = '';
        req.on('data', function(data) {
          reqBody += data;
        });
        
        req.on('end', function() {
          getArtistInfo(req, res, reqBody);
        });
      }
      break;

    // Other requests
    default:
      get405(req, res);
      break;
  } 
});

httpServer.listen(port, hostname, () => {
  console.log('Server started on port', port);
})

function getExtractData(req, res) {
  console.log("returning extractData.html");
  fs.readFile('client/extractData.html', function(err, html) {
    if(err) {
      throw err;
    }
    res.statusCode = 200;
    res.setHeader('Content-type', 'text/html');
    res.write(html);
    res.end();
  });
}

function getDisplayData(req, res) {
  console.log("returning displayData.html");
  fs.readFile('client/displayData.html', function(err, html) {
    if(err) {
      throw err;
    }
    res.statusCode = 200;
    res.setHeader('Content-type', 'text/html');
    res.write(html);
    res.end();
  });
}

async function getArtistInfo(req, res, reqBody) {
  JSONstring = querystring.parse(reqBody);
  console.log(JSONstring);
  
  const songs = await lyricist.songsByArtist(2, { page: 2, perPage: 50 });
  console.log(songs);
  
  // redirect to extractData.html
  fs.readFile('client/extractData.html', function(err, html) {
    if(err) {
      throw err;
    }
    res.statusCode = 302;
    res.setHeader('Content-type', 'text/html');
    res.write(html);
    res.end();
  });
}

function get404(req, res) {
  fs.readFile('client/404.html', function(err, html) {
    if(err) {
      throw err;
    }
    res.statusCode = 404;
    res.setHeader('Content-type', 'text/html');
    res.write(html);
    res.end();
  });
}

function get405(req, res) {
  fs.readFile('client/405.html', function(err, html) {
    if(err) {
      throw err;
    }
    res.statusCode = 405;
    res.setHeader('Content-type', 'text/html');
    res.write(html);
    res.end();
  });
}

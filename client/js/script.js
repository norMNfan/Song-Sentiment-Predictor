"use strict";

function predictSong(){
	var artist = document.getElementById("artist_name").value;
	var song = document.getElementById("song").value;
	
	var url = '/predictSong';
	var message = "artist=" + artist + "&song=" + song;
	message = message.split(" ").join("+")
	
	var xhttp = new XMLHttpRequest();
	
	xhttp.onreadystatechange = function(){
		if (this.readyState == 4 && this.status == 200) {
			
			$(document.getElementById("results")).html(this.response);
		}
	}
	
	xhttp.open("POST", url, true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send(message);
}


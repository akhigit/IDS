$(function() {
	$('button').click(function(){
		var netmask = $('#netmask').val();
		document.getElementById("scanner-running-h1").innerHTML =
			"Portscanner running"
			$.ajax({
				url: '/scan_post',
				data: $('form').serialize(),
				type: 'POST',
				success: function(response){
					console.log(response.task_id);
					var task_id = response.task_id
					if (task_id != "null") {
						checkTask(response.task_id, 1)
					}
				},
				error: function(error){
					console.log(error);
				}
			});
	});
});

function refresh() {
	  document.getElementById("alert-box").innerHTML =
						"<h1 style='color: red;font-size:200%'>"+""+"</h1>"
		document.getElementById("scanner-running-h1").innerHTML =
						"Portscanner not running"
		d3.select("svg").remove();
		render()
}

function checkTask(taskId, to_recurse) {
	if (to_recurse == 0) {
		if (taskId != 1) {
			refresh()
		}
		return
	}
	console.log('Checking Celery task '+taskId)
	$.ajax({
		url: '/task/' + taskId,
		type: 'GET',
		success: function (response){
			if(response.state === 'PENDING') {
	      setTimeout(function() {
	        checkTask(taskId, 1)
	      }, 1000)
	    } else if(response.state === 'FAILURE') {
	      alert('Failure occurred')
	    } else if(response.state === 'SUCCESS') {
				document.getElementById("alert-box").innerHTML =
				"<h1 style='color: red;font-size:200%'>"+"Deep Scan Finished"+"</h1>"
	      setTimeout(function() {
	        checkTask(taskId, 0)
	      }, 5000)
	    }
		},
		error: function(error){
			console.log(error);
		}
	});
}

function scan_host(host) {
	document.getElementById("scanner-running-h1").innerHTML = "Portscanner running"
	$.ajax({
		url: '/scan_host/' + host,
		type: 'GET',
		success: function (response){
			var task_id = response.task_id
			if (task_id !== "null" || task_id != -1) {
				checkTask(task_id, 1)
			} else {
				console.log('Calling scan_host again')
				setTimeout(function() {
					scan_host(host)
				}, 3000)
			}
		},
		error: function(error){
			console.log(error);
		}
	});
}

function process_anomaly(endpoints) {
	$.ajax({
		url: '/process_anomaly/' + endpoints,
		type: 'GET',
		success: function (response) {
			if (response.is_refresh_req == 1) {
				setTimeout(function() {
					refresh()
				}, 5000)
			}
			console.log(response)
		},
		error: function(error) {
			console.log(error);
		}
	});
}

function block_device(deviceip) {
	$.ajax({
		url: '/block_device/' + deviceip,
		type: 'GET',
		success: function (response) {
			if (response.is_refresh_req == 1) {
				setTimeout(function() {
					refresh()
				}, 5000)
			}
			console.log(response)
		},
		error: function(error) {
			console.log(error);
		}
	});
}

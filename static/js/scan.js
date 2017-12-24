$(function(){
	$('button').click(function(){
		var netmask = $('#netmask').val();
		$.ajax({
			url: '/scan_post',
			data: $('form').serialize(),
			type: 'POST',
			success: function(response){
				console.log(response.task_id);
				var task_id = response.task_id
				//document.getElementById("scanner-running-h1").innerHTML = "Portscanner running"
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
		document.getElementById("scanner-running-h1").innerHTML = "Portscanner not running"
		d3.select("svg").remove();
		render()
}

function checkTask(taskId, to_recurse) {
	if (to_recurse == 0) {
		refresh()
		return
	}
	console.log('Checking Celery task '+taskId)
	document.getElementById("scanner-running-h1").innerHTML = "Portscanner running"
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

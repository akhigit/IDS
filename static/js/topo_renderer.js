function render() {

var width = 960,
    height = 500;

var force = d3.layout.force()
		.size([width, height])
    .charge(-50)
    .linkStrength(0.5)
    .linkDistance(140)

d3.json("static/json_dictionary.json", function(error, graph) {
  force
      .nodes(graph.nodes)
      .links(graph.links)
			.start();

	 var svg = d3.select("body").append("svg")
    	.attr("width", width)
    	.attr("height", height)
			.attr("align", "center");

    var link = svg.selectAll(".link")
			.data(graph.links)
    	.enter().append("line")
    	.attr("class", "link")
			.style("stroke", "black")
    	.style("stroke-width", 6)
			.style("opacity", 1.0);

    var node_drag = d3.behavior.drag()
        .on("dragstart", dragstart)
        .on("drag", dragmove)
        .on("dragend", dragend);

    function dragstart(d, i) {
        force.stop() // stops the force auto positioning before you start dragging
    }

    function dragmove(d, i) {
        d.px += d3.event.dx;
        d.py += d3.event.dy;
        d.x += d3.event.dx;
        d.y += d3.event.dy;
        tick(); // this is the key to make it work together with updating both px,py,x,y on d !
    }

    function dragend(d, i) {
        d.fixed = true; // of course set the node to fixed so the force doesn't include the node in its auto positioning stuff
        tick();
        force.resume();
    }

	var node = svg.selectAll("g.node")
		.data(graph.nodes)
		.enter().append("svg:g").append("circle")
		.attr("class", "node")
		.attr("r", 15)
		.attr("name", function(d) {
			return d.name;
		})
		.attr("PortService", function(d) {
			return d.PortServices;
		})
		.style("fill", function(d) {
            if (d.group === 1) {
                return "#271192";
                };
            if (d.group === 2) {
                return "#FF2B1A";
                };
            if (d.group === 3) {
                return "#32cd32";
                };
            })
		.call(node_drag);

  force.on('tick', tick);

	function tick() {

	link.attr("x1", function(d) { return d.source.x + width/5; })
		  .attr("y1", function(d) { return d.source.y - height/3; })
		  .attr("x2", function(d) { return d.target.x + width/5; })
		  .attr("y2", function(d) { return d.target.y - height/3; });


  node.attr("cx", function(d) { return d.x + width/5; })
 			.attr("cy", function(d) { return d.y - height/3; });
    //node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
	};

	var servicesBox = d3.select(document.getElementById("services-info"))
			.append("text");

	function checkForEmptyServices(node) {

		/*
		* Takes in the D3 HTML object in the format:
		* <circle class="node" r="7" name="64:5A:04:87:30:0E portService="netbiOSssn"
		* fill = "aliceblue" cx="277.707" cy="207.75" style="fill:#537897;"></circle>
		* returns a string of text.
		*/

		var mac = node.__data__.Id
		var ports = node.__data__.PortServices
		var ip = node.__data__.IP
		var os_version = node.__data__.OSMatch

		// var os = node._data_.OSMatch

		if (ports.length === 0) {
			return "host MAC: " + mac + " " + "<p>" + "host IP: " + ip + "<p> Ports Open: None</p>";
		} else {
			console.log(ports);
			return "host MAC: " + mac + " " + "<p>" + "host IP: " + ip + "<p> Ports Open: " + "<b>" + ports.join(', ') + "<b></p>";
		}
	};

	function checkForEmptyOSMatches(node) {

		/*
		* Takes in the D3 HTML object in the format:
		* <circle class="node" r="7" name="64:5A:04:87:30:0E portService="netbiOSssn"
		* fill = "aliceblue" cx="277.707" cy="207.75" style="fill:#537897;"></circle>
		* returns a string of text.
		*/

		var name = node.__data__.name
		var os_version = node.__data__.OSMatch
		// var os = node._data_.OSMatch

		if (os_version === "") {
			return "<p>OS Version unavailable.</p>";
		} else {
			return "<p>" + os_version + "</p>";
		}
	};


	var tooltip = d3.select("body")
		.append("div")
		.style("position", "absolute")
		.style("z-index", "10")
		.style("visibility", "hidden")


	d3.selectAll(".node")
		// .append("svg:circle")
		.attr("fill", "aliceblue")
		.attr("r", 15)
		.attr("cx", 50)
		.attr("cy", 50)


		.on("mouseover", function(){
			tooltip.html(checkForEmptyOSMatches(this))
			servicesBox.append("text").html(checkForEmptyServices(this))
			return tooltip.style("visibility", "visible");}
			)

		.on("mousemove", function(){
			return tooltip.style("top", (event.pageY-10)+"px")
			.style("left",(event.pageX+10)+"px")
			.style("max-width","200px")
			.style("max-height","300px")
			.style("background-color", "rgba(163, 224, 255, 0.9)")
			.style("padding", "10px")
			.style("border-style", "solid")
			.style("border-color", "fff")
			.style("border-width", "1px")
			.style("border-radius", ".3em")
			.style("text-align", "center");})
		.on("mouseout", function(){
			return tooltip.style("visibility", "hidden"),
			servicesBox.html(" ")
		})


});
}

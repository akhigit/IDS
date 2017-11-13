var bbox, radii, svg, target;

svg = d3.select('svg');
bbox = svg[0][0].getBoundingClientRect();

radii = [12, 24, 32, 48, 60, 80, 120, 210];

target = svg.append('g')
    .attr('transform', "translate(" + (bbox.width / 2) + "," + (bbox.height / 2) + ")");

target.selectAll('circle')
    .data(radii)
  .enter().append('circle')
    .attr('r', function(d) {return d;});

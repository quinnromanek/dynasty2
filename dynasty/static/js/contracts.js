var svg = d3.select("#contracts");

var barheight = 40;
var barpadding = 5;

function moneyFormat(salary) {
	if(salary >= 1000000) {
		return "$" + (salary/1000000).toFixed(1) + "M";
	}else{
		return "$" + (salary/1000).toFixed(0) + ",000";
	}

}
var time_margin = {top: 20, right: 30, bottom: 30, left: 40};
var bar_margin = {top:20, right:30, bottom:30, left:40}
var bar_height = 50;

function drawChart(data, year) {

	var color = d3.scale.category10();
	var width = $(".tab-pane.active").width() - time_margin.left - time_margin.right;
	var height = barheight * data.length ;
	var x = d3.scale.linear()
		.domain([0, d3.max([5, d3.max(data, function(d) { return d.years + d.playerOption + d.teamOption })])])
		.range([0, width])
	var ticks = x.domain()[1] - x.domain()[0] + 1;

	var years = d3.scale.ordinal()
		.domain(x.ticks(ticks))
		.range(d3.map(x.ticks(ticks), function(d) { return d+ year; }))

	var timeScale = d3.svg.axis()
		.scale(x)
		.ticks(x.domain()[1] - x.domain()[0] + 1)	
		.orient("bottom");

	svg.attr("width", width + time_margin.left + time_margin.right);
	svg.attr("height", height + time_margin.top + time_margin.bottom + bar_height + bar_margin.top + bar_margin.bottom);

	var chart = svg.append("g")
		.attr("transform", "translate(" + time_margin.left + "," + (time_margin.top + bar_height + bar_margin.top + bar_margin.bottom) + ")");

	chart.append("g")
		.attr("class", "x axis")
		.attr("transform", "translate(0, " + height + ")")
		.call(timeScale)

	var bar = chart.selectAll(".bar")
		.data(data)
	.enter().append("g")
		.attr("class", "bar")
		.attr("transform", function(d, i) { return "translate(0," + i * barheight + ")";});

	bar.append("rect")
		.attr("class", "option")
		.attr("stroke", function(d, i) {
			if(d.playerOption > 0) {
				return "red";
			}else if (d.teamOption > 0){
				return "green";
			}else{
				return "none";
			}
		})
		.attr("width", function(d) { return x(d.years + d.teamOption + d.playerOption); })
		.attr("height", barheight - barpadding);
		

	bar.append("rect")
		.attr("class", "years")
		.style("fill", function(d,i ) { return color(i); } ) 
		.style("stroke", function(d,i ) { return color(i); } ) 
		.attr("width", function(d) { return x(d.years); })
		.attr("height", barheight - barpadding);

	bar.append("text")
		.attr("x", function(d) { return x(d.years) - 3})
		.attr("y", barheight/2)
		.attr("dy", ".35em")
		.text(function(d) { return d.name + " " + moneyFormat(d.salary); });

	bar.append("text")

}
function drawSalary(data) {

	var color = d3.scale.category10();
	var width = $(".tab-pane.active").width() - bar_margin.left - time_margin.right;
	var salaryBar = svg.append("g")
		.attr("transform", "translate(" + bar_margin.left + "," + bar_margin.top + ")")

	var total = 0;
	data = data.map(function(d) {
		o = {total: total, salary: d.salary}
		total += d.salary;
		return o;
	})
	
	var x = d3.scale.linear()
		.domain([0, 65])
		.range([0, width]);
	var format = d3.format(".2g")
	var cap = d3.svg.axis()
		.scale(x)
		.orient("bottom")
		.tickFormat(function(d) { return "$" + format(d) + "M";});

	salaryBar.append("g")
		.attr("transform", "translate(0, " + bar_height + ")")
		.attr("class", "axis")
		.call(cap);

	var chunks = salaryBar.selectAll(".chunk")
		.data(data)
	.enter().append("g")
		.attr("class", "chunk");

	chunks.append("rect")
		.attr("height", bar_height)
		.attr("x", function(d) { return x(d.total/1000000); })
		.attr("width", function(d) { return x((d.salary)/1000000); })
		.style("fill", function(d, i) { return color(i); });

	salaryBar.append("rect")
		.attr("height", bar_height)
		.attr("width", function(d) { return x(60); })
		.style("fill", "none")
		.style("stroke", "black")
		.style("stroke-width", "2px");

}
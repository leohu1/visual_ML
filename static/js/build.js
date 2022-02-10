var time = 0;
var args = {
	{
		args | safe
	}
};
(function() {
	var listDiv = document.getElementById("list"),

	showConnectionInfo = function(s) {
		listDiv.innerHTML = s;
		listDiv.style.display = "block";
	},
	hideConnectionInfo = function() {
		listDiv.style.display = "none";
	},
	connections = [],
	updateConnections = function(conn, remove) {
		if (!remove) connections.push(conn);
		else {
			var idx = -1;
			for (var i = 0; i < connections.length; i++) {
				if (connections[i] == conn) {
					idx = i;
					break;
				}
			}
			if (idx != -1) connections.splice(idx, 1);
		}
		if (connections.length > 0) {
			var s = "<span><strong>Connections</strong></span><br/><br/><table><tr><th>Scope</th><th>Source</th><th>Target</th></tr>";
			for (var j = 0; j < connections.length; j++) {
				s = s + "<tr><td>" + connections[j].scope + "</td>" + "<td>" + connections[j].sourceId + "</td><td>" + connections[j].targetId + "</td></tr>";
			}
			showConnectionInfo(s);
		} else hideConnectionInfo();
		if ($(".args_child").length > 0) {
			var d = [];
			var select = $(".select");
			for (var i = 0; i < select.length; i++) {
				d.push({
					"id": select[i].id,
					"value": select[i].value
				})
			}

			var a = [];
			var args = $(".args_child");
			for (var i = 0; i < args.length; i++) {
				a.push({
					"id": args[i].id,
					"value": args[i].value,
					"parent": $(args[i]).parent()[0].id
				})
			}

			var c = [];
			for (var i = 0; i < connections.length; i++) {
				c.push({
					"source": connections[i].sourceId,
					"target": connections[i].targetId
				});
			}

			o = {
				"connections": c,
				"args": a,
				"data": d
			};
			console.log(o);
			$.post("/build", o)
		};
	};

jsPlumb.ready(function() {

	instance = jsPlumb.getInstance({
		DragOptions: {
			cursor: 'pointer',
			zIndex: 2000
		},
		PaintStyle: {
			stroke: '#666'
		},
		EndpointHoverStyle: {
			fill: "orange"
		},
		HoverPaintStyle: {
			stroke: "orange"
		},
		EndpointStyle: {
			width: 5,
			height: 5,
			stroke: '#666'
		},
		Endpoint: "Dot",
		Anchors: ["TopCenter", "BottomCenter"],
		Container: "canvas",
		ConnectionOverlays: [["Arrow", {
			location: 0.5,
			id: "arrow",
			length: 10,
			foldback: 0.6
		}]],
		ConnectionsDetachable: true
	});

	// suspend drawing and initialise.
	instance.batch(function() {

		// bind to connection/connectionDetached events, and update the list of connections on screen.
		instance.bind("connection",
		function(info, originalEvent) {
			updateConnections(info.connection);
		});
		instance.bind("connectionDetached",
		function(info, originalEvent) {
			updateConnections(info.connection, true);
		});

		instance.bind("connectionMoved",
		function(info, originalEvent) {
			//  only remove here, because a 'connection' event is also fired.
			// in a future release of jsplumb this extra connection event will not
			// be fired.
			updateConnections(info.connection, true);
		});

		instance.bind("click",
		function(conn, originalEvent) {
			instance.deleteConnection(conn);
		});

		// configure some drop options for use by all endpoints.
		var DropOptions = {
			tolerance: "touch",
			hoverClass: "dropHover",
			activeClass: "dragActive"
		};

		var color = "#316b31";
		InputPoint = {
			endpoint: ["Dot", {
				radius: 8
			}],
			anchor: "TopCenter",
			paintStyle: {
				fill: color
			},
			scope: "green",
			connectorStyle: {
				stroke: color,
				strokeWidth: 2
			},
			connector: ["StateMachine", {
				curviness: 63
			}],
			maxConnections: -1,
			isTarget: true,
			dropOptions: DropOptions,
		};
		OutputPoint = {
			endpoint: ["Dot", {
				radius: 8
			}],
			anchor: "BottomCenter",
			paintStyle: {
				fill: color
			},
			isSource: true,
			scope: "green",
			connectorStyle: {
				stroke: color,
				strokeWidth: 2
			},
			connector: ["StateMachine", {
				curviness: 63
			}],
			maxConnections: -1,
			dropOptions: DropOptions,
		};

		instance.draggable(jsPlumb.getSelector(".drag-drops .window"), {
			grid: [50, 50]
		});
		instance.addEndpoint(jsPlumb.getSelector(".drag-drops .input "), OutputPoint);

		instance.on(jsPlumb.getSelector(".drag-drops .hide"), "click",
		function(e) {
			instance.toggleVisible(this.getAttribute("rel"));
			jsPlumbUtil.consume(e);
		});

		instance.on(document.getElementById("build"), "click",
		function(e) {
			if ($(".args_child").length > 0) {
				var d = [];
				var select = $(".select");
				for (var i = 0; i < select.length; i++) {
					d.push({
						"id": select[i].id,
						"value": select[i].value
					})
				}

				var a = [];
				var args = $(".args_child");
				for (var i = 0; i < args.length; i++) {
					//console.log(args[i].id);
					//console.log(args[i].value);
					a.push({
						"id": args[i].id,
						"value": args[i].value,
						"parent": $(args[i]).parent()[0].id
					})
				}

				var c = [];
				for (var i = 0; i < connections.length; i++) {
					c.push({
						"source": connections[i].sourceId,
						"target": connections[i].targetId
					});
				}

				o = {
					"connections": c,
					"args": a,
					"data": d
				};
				console.log(o);
				if (c.length > 0) {
					$.post("/build", o,
					//function(){
					//        location.assign("/train")
					//}
					);
				} else {
					alert("No Connections");
				}
			}
		});

		instance.on(document.getElementById("add"), "click",
		function(e) {
			time = time + 1 $("#canvas").append("<div class='window connect' id='connect_" + time + "'><select id='select_" + time + "' class='select'><option value='None' selected></option>{% for item in layers %}<option value='{{item}}'>{{item}}</option>{% endfor %}</select><button id='delete_" + time + "' class='delete btn'><i class='fa fa-remove'></i></button><br><a data-target='#args_" + time + "' data-toggle='collapse'><i class='fa fa-angle-down'></i>Args</a><br><dir class='args collapse bg-light border border-dark rounded' id='args_" + time + "' style='padding-left: 0px;'></dir></div>") instance.draggable(document.getElementById("connect_" + time), {
				grid: [50, 50]
			});
			instance.addEndpoint(document.getElementById("connect_" + time), InputPoint);
			instance.addEndpoint(document.getElementById("connect_" + time), OutputPoint);
			$(document).ready(function() {
				$("#select_" + time).change(function() {
					$("#" + "args_" + (this.id || "")[(this.id || "").length - 1]).empty().append(args[this.value]);
				});
			});
			instance.on(document.getElementById("delete_" + time), "click",
			function(e) {
				console.log("i");
				console.log(this.id);
				console.log(instance.getEndpoints("connect_" + this.id[this.id.length - 1]));
				var p = instance.getEndpoints("connect_" + this.id[this.id.length - 1]);
				for (var i = 0; i < p.length; i++) {
					instance.deleteEndpoint(p[i]);
				}
				$("#connect_" + this.id[this.id.length - 1]).remove();
			});
			if ($(".args_child").length > 0) {
				var d = [];
				var select = $(".select");
				for (var i = 0; i < select.length; i++) {
					d.push({
						"id": select[i].id,
						"value": select[i].value
					})
				}

				var a = [];
				var args = $(".args_child");
				for (var i = 0; i < args.length; i++) {
					//console.log(args[i].id);
					//console.log(args[i].value);
					a.push({
						"id": args[i].id,
						"value": args[i].value,
						"parent": $(args[i]).parent()[0].id
					})
				}

				var c = [];
				for (var i = 0; i < connections.length; i++) {
					c.push({
						"source": connections[i].sourceId,
						"target": connections[i].targetId
					});
				}

				o = {
					"connections": c,
					"args": a,
					"data": d
				};
				console.log(o);
				$.post("/build", o)
			}
		});

		jsPlumb.fire("jsPlumbDemoLoaded", instance);

	});
})
})();
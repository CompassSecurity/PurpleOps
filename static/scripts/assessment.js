// Onload
$(function () {
	// The cookie extension oddly somtimes force shows the ID column, so force it hidden
	$('#assessmentTable').bootstrapTable('hideColumn', 'id')
	// Delay table showing until page is loaded to prevent jumping
	$('#assessmentTable').show()
})

var row = null
var rowData = null

// Pop modal when adding a new raw testcase and clear old data
$('#newTestcase').click(function() {
	$("#newTestcaseForm").trigger('reset')
	$('#newTestcaseModal').modal('show')
});

// Wrapper for formatting server responses into table rows
function formatRow(response) {
	return {
		add: response.add,
		id: response.id,
		mitreid: response.mitreid,
		name: response.name,
		tactic: response.tactic,
		state: response.state,
		visible: response.visible,
		tags: response.tags.join(","),
		uuid: response.uuid,
		start: response.starttime != "None" ? response.starttime : "",
		modified: response.modifytime,
		preventscore: response.preventedrating !== null ? response.preventedrating : "",
		detectscore: response.detectionrating !== null ? response.detectionrating : "",
		testcasescore: response.testcasescore,
		outcome: response.outcome,
		actions: "",
	}
}

// AJAX new testcase POST and table append
$("#newTestcaseForm").submit(function(e){
	e.preventDefault();
	fetch(e.target.action, {
		method: 'POST',
		body: new URLSearchParams(new FormData(e.target))
	}).then((response) => {
		return response.json();
	}).then((body) => {
		$('#assessmentTable').bootstrapTable('append', [formatRow(body)])
		$('#newTestcaseModal').modal('hide')
	})
});

// AJAX new testcase from template POST and table append
$('#testcaseTemplatesButton').click(function() {
	var csrf_token = $('meta[name="csrf-token"]').attr('content');
	$.ajax({
		url: `/assessment/${window.location.href.split("/").slice(-1)[0]}/import/template`,
		type: 'POST',
		headers: {
			'X-CSRFToken': csrf_token
		},
		data: JSON.stringify({
			ids: $('#testcaseTemplateTable').bootstrapTable('getSelections').map(row => row.id)
		}),
		dataType: 'json',
		contentType: "application/json; charset=utf-8",
		success: function(result) {
			result.forEach(result => {
				$('#assessmentTable').bootstrapTable('append', [formatRow(result)])
				showToast('Testcase Added');
			})
			// clear selection after import
			$('#testcaseTemplateTable').bootstrapTable('uncheckAll');
			$('#testcaseTemplatesModal').modal('hide')
		}
	});
});

// AJAX new testcases from navigator template POST and table append
$("#navigatorTemplateForm").submit(function(e){
	e.preventDefault();
	fetch(e.target.action, {
		method: 'POST',
		body: new FormData(e.target)
	}).then((response) => {
		return response.json();
	}).then((body) => {
		body.forEach(result => {
			$('#assessmentTable').bootstrapTable('append', [formatRow(result)])
		})
		$('#testcaseNavigatorModal').modal('hide')
	})
});

// AJAX new testcases from campaign template POST and table append
$("#campaignTemplateForm").submit(function(e){
	e.preventDefault();
	fetch(e.target.action, {
		method: 'POST',
		body: new FormData(e.target)
	}).then((response) => {
		return response.json();
	}).then((body) => {
		body.forEach(result => {
			$('#assessmentTable').bootstrapTable('append', [formatRow(result)])
		})
		$('#testcaseCampaignModal').modal('hide')
	})
});

// Toggle visibility of testcase AJAX
function visibleTest(event) {
	var csrf_token = $('meta[name="csrf-token"]').attr('content');
	event.stopPropagation();
	row = $(event.target).closest("tr")
	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
	$.ajax({
		url: `/testcase/${rowData.id}/toggle-visibility`,
		type: 'POST',
		headers: {
			'X-CSRFToken': csrf_token
		},
		success: function(body) {
			$('#assessmentTable').bootstrapTable('updateByUniqueId', {
				id: body.id,
				row: formatRow(body),
				replace: true
			})
		}
	});
};

// Testcase clone AJAX POST and row update
function cloneTest(event) {
	var csrf_token = $('meta[name="csrf-token"]').attr('content');
	event.stopPropagation();
	row = $(event.target).closest("tr")
	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
	$.ajax({
		url: `/testcase/${rowData.id}/clone`,
		type: 'POST',
		headers: {
			'X-CSRFToken': csrf_token
		},
		success: function(body) {
			$('#assessmentTable').bootstrapTable('insertRow', {
				index: row.data("index") + 1,
				row: formatRow(body)
			})
			showToast('Testcase Cloned');
		}
	});
};

function deleteTestcaseModal(event) {
	// Globally store the clicked row for AJAX operations
	row = $(event.target).closest("tr")
	rowData = $('#assessmentTable').bootstrapTable('getData')[row.data("index")]
	$('#deleteTestcaseForm').attr('action', `/testcase/${rowData.id}/delete`) 
	$('#deleteTestcaseWarning').text(`Really Delete ${rowData.name}?`)
	$('#deleteTestcaseModal').modal('show')
}

// AJAX DELETE testcase call and remove from table
$('#deleteTestcaseButton').click(function() {
	var csrf_token = $('meta[name="csrf-token"]').attr('content');
	$.ajax({
		url: `/testcase/${rowData.id}/delete`,
		type: 'POST',
		headers: {
			'X-CSRFToken': csrf_token
		},
		success: function(result) {
			$('#assessmentTable').bootstrapTable('removeByUniqueId', rowData.id)
			$('#deleteTestcaseModal').modal('hide')
			showToast('Testcase Deleted');
		}
	});
});

// Table formatters
function nameFormatter(name, row) {
	return `<a href="/testcase/${row.id}">${name}</a>`
}

function visibleFormatter(name) {
	return (name == "True" || name == true) ? "✅" : "❌"
}

function tagFormatter(tags) {
	html = []
	tags.split(",").forEach(tag => {
		html.push(`<span class='badge rounded-pill' style="background:${tag.split("|")[1]}; cursor:pointer">${tag.split("|")[0]}</span>`)
	})
	return html.join("&nbsp;")
}

function actionFormatter() {
	return `
		<div class="btn-group btn-group-sm" role="group">
			<button type="button" class="btn btn-info py-0" onclick="visibleTest(event)" title="Toggle Visiblity">
				<i class="bi-eye">&zwnj;</i>
			</button>
			<button type="button" class="btn btn-warning py-0" onclick="cloneTest(event)" title="Clone">
				<i class="bi-files">&zwnj;</i>
			</button>
			<button type="button" class="btn btn-danger py-0" onclick="deleteTestcaseModal(event)" title="Delete">
				<i class="bi-trash-fill">&zwnj;</i>
			</button>
		</div>
	`
}

function timeFormatter(utc) {
	if (!utc.length) {
		return utc
	}
	
	offset = new Date().getTimezoneOffset()
	local = new Date(utc);
	local.setMinutes(local.getMinutes() - offset);
	return local.toISOString().slice(0,16)
}

function bgFormatter(value) {
	bg = ""
	text = ""
	if (["Waiting Red","0"].includes(value)) {
		bg = "danger"
	} else if (["Running", "25","50","75"].includes(value)) {
		bg = "warning"
	} else if (["100"].includes(value)) {
		bg = "success"
	} else if (["Waiting Blue"].includes(value)){
		bg = "info"	
	} else if (["Complete", "Aborted"].includes(value)) {
		bg = "primary"
		text = "light"
	} else if (["Ready"].includes(value)){
		bg = "secondary"	
	} else if (["Pending"].includes(value)) {
		bg = "light"
	} else if (["False", false, "0.0", "0.5"].includes(value)) {
		bg = "dark"
		text = "light"
	}
	css = {background: `var(--bs-${bg})`}
	if (text.length) {
		css["color"] = `var(--bs-${text})`
	}
	return {css: css}
}

// Show # selected testcases
$('#assessmentTable').on( 'check.bs.table uncheck.bs.table check-all.bs.table uncheck-all.bs.table', function (e) {
	selectedIds = $("#assessmentTable").bootstrapTable('getSelections').map(i => i.id)
	if (selectedIds.length > 0) {
		$("#selected-count").show()
		$("#selected-count").text(`(${selectedIds.length} selected)`)
	}
	else {
		$("#selected-count").hide()
	}
} );

// upload variables to session storage
$("#variablesForm").submit(function(e){
	e.preventDefault();
	const fileUpload = document.getElementById('variablesFile');

	if (fileUpload.files.length === 0) {
		alert("Please select a JSON file.")
		return;
	}

	const file = fileUpload.files[0];

	const reader = new FileReader();

	reader.onload = function(event) {
		try {
			const jsonData = JSON.parse(event.target.result);
      // Valid JSON, proceed with storing data

			if (typeof jsonData !== 'object' || jsonData === null) {
				alert("Invalid JSON format.")
				return;
			}

      assessmentid = document.getElementById('assessmentid').textContent;

      //clear session storage with items from this assessment
      clearSessionStorageByKeyPrefix(assessmentid)

      for (const key in jsonData) {
      	if (jsonData.hasOwnProperty(key)) {
      		sessionStorage.setItem(assessmentid+"_"+key, jsonData[key]);
      	}
      }

      alert("JSON data uploaded and stored in session storage.")
      $('#variablesModal').modal('hide')
  } catch (error) {
  	alert("Error parsing JSON: " + error.message)
  }
};

reader.onerror = function(error) {
	alert("Error reading file: " + error.message)
};

reader.readAsText(file);

});

function clearSessionStorageByKeyPrefix(prefix) {
  const keysToRemove = [];

  for (let key in sessionStorage) {
    if (key.startsWith(prefix)) {
      keysToRemove.push(key);
    }
  }

  keysToRemove.forEach(key => sessionStorage.removeItem(key));
}
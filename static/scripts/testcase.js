// When the new source/target etc. button is clicked, add a new row
$('.multiNew').click(function(event) {
	type = event.target.id.replace("NewButton", "") // Hacky
	newRow = {
		id: `tmp-${Date.now()}`, // Rows need unique IDs, so give it the time
		name: "",
		delete: ""
	}
	type == "tags" ? newRow.colour = "" : newRow.description = ""
	$(`#${type}Table`).bootstrapTable("append", [newRow])
})

// When the source/target etc. table/modal is saved, post updates and refresh table
$('.multiButton').click(function(event) {
	var csrf_token = $('meta[name="csrf-token"]').attr('content');
	type = event.target.id.replace("multi", "").replace("Button", "").toLowerCase() + "s" // Hacky
	$.ajax({
		url: `${$("#assessment-crumb-button").attr("href")}/multi/${type}`,
		type: 'POST',
		headers: {
			'X-CSRFToken': csrf_token
		},
		data: JSON.stringify({
			data: $(`#${type}Table`).bootstrapTable("getData")
		}),
		dataType: 'json',
		contentType: "application/json; charset=utf-8",
		success: function(result) {
			// The model doesn't have a delete field but the table requires it
			result.map(row => row.delete = "")
			$(`#${type}Table`).bootstrapTable("load", result)
			$(event.target).closest(".modal").modal("hide")

			// Selectpicker plugin doesn't support populating a dropdown with
			// values and names seperately so we need to populate the HTML
			// manually and force it to refresh
			selectedIDs = $(`#${type}`).val()
			$(".dynopt-" + type).remove();
			result.forEach(function(i) {
				selected = selectedIDs.includes(i.id) ? "selected" : ""
				pill = type == "tags" ? `data-content="<span class='badge rounded-pill' style='background:${i.colour}'>${i.name}</span>"` : ""
				$(`#${type}`).append(`<option ${selected} class="dynopt-${type}" value="${i.id}" ${pill}>${i.name}</option>`);
			})
			$(`#${type}`).selectpicker('destroy');
			$(`#${type}`).selectpicker();
		}
	});
})

// If "manage" is selected in a multi dropdown, remove the selection and pop manage modal
$('.selectpicker').change(function(event) {
	type = event.target.id
	if ($(`#${type}`).val().includes("Manage")) {
		$(event.target).selectpicker('val', $(`#${type}`).val().filter(item => item !== "Manage"))
		$(event.target).selectpicker('toggle');
		$(`#multi${type[0].toUpperCase() + type.slice(1, -1)}Modal`).modal('show')
	}
})

// When source/target etc. names/descriptions are changed, update table value ready for POST
$('.multiTable').on('change', '.multi', function(event) {
	$(event.delegateTarget).bootstrapTable("updateCellByUniqueId", {
		id: $(event.target).closest("tr").data("uniqueid"),
		field: event.target.name,
		value: event.target.value
	})
});

// When a source/target etc. is deleted, nuke the row from the table
function deleteMultiRow(event) {
    // Get the table ID
    tableId = $(event.target).closest("table")[0].id;

    // Get the uniqueId of the row
    var uniqueId = $(event.target).closest("tr").data("uniqueid");

    // Only remove the row if uniqueId starts with "tmp-"
    if (uniqueId && uniqueId.startsWith("tmp-")) {
        // Remove the row using bootstrapTable's removeByUniqueId method
        $(`#${tableId}`).bootstrapTable("removeByUniqueId", uniqueId);
    }
}

// Multi modal formatters
function nameFormatter(val) {
	return `<input type="text" name="name" value="${val}" class="multi" placeholder="Name..."/>`
}

function descriptionFormatter(val) {
	return `<input type="text" name="description" value="${val}" class="multi" placeholder="Description..."/>`
}

function colourFormatter(val) {
	return `<input type="color" name="colour" value="${val}" class="multi"/>`
}

function deleteFormatter() {
	return `
		<button type="button" class="btn btn-danger py-0" onclick="deleteMultiRow(event)" title="Delete">
			<i class="bi-trash-fill">&zwnj;</i>
		</button>
	`
}

// Dynamic <textarea> height (no native HTML/CSS way :( )
$('#objective, #actions, #rednotes, #bluenotes').on('input', function(event) {
	event.target.style.height = 0;
	event.target.style.height = event.target.scrollHeight + 5 + 'px';
}).trigger('input')

// Dynamically update prevent fields
$('input[name="prevented"]').on('change', function() {
	current = $('input[name="prevented"]:checked').val()
	if (["No", ""].includes(current)) {
		$("#preventedrating").val(current.replace("No", "0.0"))
		$("#preventedrating-container").hide()
		$("#preventionsources-container").hide()
		$("#preventionsources").val("")
		$("#preventiontime-container").hide()
		$("#time-preventtime").val("")
	} else {
		if (["0.0", "N/A"].includes($("#preventedrating").val())) {
			$("#preventedrating").val("")
		}
		$("#preventedrating-container").hide()
		$("#preventionsources-container").show()
		$("#preventiontime-container").show()
	}
}).trigger('change')

// Dynamically update priority fields
$('input[name="priority"]').on('change', function() {
	current = $('input[name="priority"]:checked').val()
	if (["N/A"].includes(current)) {
		$("#priorityurgency").val("N/A")
		$("#urgency-container").hide()
	} else {
		if ($("#priorityurgency").val() == "N/A") {
			$("#priorityurgency").val("")
		}
		$("#urgency-container").show()
	}
}).trigger('change')

// Dynamically update alerted fields
$('input[name="alerted"]').on('change', function() {
	current = $('input[name="alerted"]:checked').val()
	if (current == "Yes") {
		$("#alert-container").show()
		$("#detectionsources-container").show()
		$('input[name="logged"]').prop('checked', false)
		$('#log-yes').prop("checked", true)
		if ($('#detectionrating').val() == "0.0") {
			$('#detectionrating').val("")
		}
	} else if (current == "No") {
		$("#alert-container").hide()
		$("#detectionsources-container").hide()
		$("#time-alerttime").val("")
		$("#detectionsources").val("")
		$("#alertseverity").val("")
	} else {
		$("#alert-container").hide()
		$("#detectionsources-container").hide()
	}
}).trigger('change')

// Dynamically update incident created fileds
$('input[name="incidentcreated"]').on('change', function() {
	current = $('input[name="incidentcreated"]:checked').val()
	if (current == "Yes") {	
		$("#incidentcreated-container").show()
	} else if (current == "No") {
		$("#incidentcreated-container").hide()
		$("#incidentseverity").val("")
		$("#time-incidenttime").val("")
	} else {
		$("#incidentcreated-container").hide()
	}
}).trigger('change')

// AJAX submit and pop toast on save success
$("#ttpform").submit(function(e) {
  e.preventDefault();

  // Create FormData object from the form
  let formData = new FormData(e.target);

  ['sources', 'targets', 'tools', 'preventionsources', 'detectionsources', 'tags'].forEach(field => {
    //check if formdata has all expected form fields. If not add it
    if (!formData.has(field)) {
      formData.append(field, ''); // Add empty fields explicitly
    }
  });

  // Convert relevant dates to UTC
  convertLocalToUtc("#time-start", formData, 'starttime');
  convertLocalToUtc("#time-end", formData, 'endtime');
  convertLocalToUtc("#time-alerttime", formData, 'alerttime');
  convertLocalToUtc("#time-preventtime", formData, 'preventtime');
  convertLocalToUtc("#time-incidenttime", formData, 'incidenttime');

  fetch(e.target.action, {
    method: 'POST',
    body: formData
  })
  .then(response => {
    if (response.status === 200) { // Use === for strict comparison
      return response.text(); // Chain .text() for text response
    } else {
      throw new Error(`Error: ${response.status}`);
    }
  })
  .then(text => {
    displayNewEvidence(new FormData(e.target));
    showToast('Testcase Saved');
    const modifyTimeInput = document.getElementById('modifytime');
    if (modifyTimeInput) {
      modifyTimeInput.value = text; // Set the response text as the new value
    }
  })
  .catch(error => {
    if (error.message.includes('409')) {
      alert("Testcase save error - Testcase was saved in the meantime");
    } else {
      alert("Testcase save error - contact admin to review log");
      console.error(error); // Log the error for debugging
    }
  });
});


// functions and calls to change DB UTC to local time, respecting DST
$(document).ready(function() {
  const fieldsToConvert = [
    "#time-start",
    "#time-end",
    "#time-alerttime",
    "#time-preventtime",
    "#time-incidenttime"
  ];

  fieldsToConvert.forEach(selector => {
    displayUtcAsLocal(selector);
  });
});

// Alter timestamps, button labels and state when hitting run button
$("#run-button").click(function(){
	clickTime = new Date();
	clickTime.setMinutes(clickTime.getMinutes() - clickTime.getTimezoneOffset());
	clickTime = clickTime.toISOString().slice(0, 16)

	if ($("#run-button").text() == "Start") {
		$("#time-start").val(clickTime)
		$("#time-end").val("")
		$("#run-button").text("Stop")
		$("#run-button").removeClass("btn-outline-success")
		$("#run-button").addClass("btn-outline-danger")
		$("#state").val("Running")
		$("#state").addClass("bg-warning")
		$("#state").removeClass("text-white")
		$("#state").addClass("text-dark")
	} else if ($("#run-button").text() == "Stop") {
		$("#time-end").val(clickTime)
		$("#run-button").text("Restart")
		$("#run-button").removeClass("btn-outline-danger")
		$("#run-button").addClass("btn-outline-warning")
		$("#state").val("Waiting Blue")
		$("#state").removeClass("bg-warning")
		$("#state").addClass("bg-info")
		$("#state").removeClass("text-dark")
		$("#state").addClass("text-white")
	} else if ($("#run-button").text() == "Restart") {
		$("#time-start").val("")
		$("#time-end").val("")
		$("#run-button").text("Start")
		$("#run-button").removeClass("btn-outline-danger")
		$("#run-button").removeClass("btn-outline-warning")
		$("#run-button").addClass("btn-outline-success")
		$("#state").val("Pending")
		$("#state").removeClass("bg-primary")
		$("#state").removeClass("text-white")
	} 
});

// Delete evidence AJAX handler
$(document).on("click", ".evidence-delete", function(event) {
	var csrf_token = $('meta[name="csrf-token"]').attr('content');
	target = event.target.tagName == "I" ? event.target.parentNode : event.target
	colour = $(target).attr("class").includes("evidence-red") ? "red" : "blue"
	url = $(target).next("a").attr("href").split("?")[0]
	url = url.replace("/evidence/", `/evidence/${colour}/`)

	$.ajax({
		url: url,
		type: 'DELETE',
		headers: {
			'X-CSRFToken': csrf_token
		},
		success: function(result) {
			$(target).parent().remove()
		}
	});
});

// AJAX inject new evidence HTML on testcase save
function displayNewEvidence(form) {
	["red", "blue"].forEach(colour => {
		form.getAll(`${colour}files`).forEach(file => {
			if (file.name == "") {
				return
			}
			testcaseId = window.location.pathname.split("/").slice(-1)[0]
			html = `
				<li class="list-group-item">
					<button type="button" class="btn btn-outline-danger btn-sm me-2 evidence-delete evidence-${colour}">
						<i class="bi-trash small">&zwnj;</i>
					</button>
					<a href="/testcase/${testcaseId}/evidence/${file.name}?download=true" class="btn btn-outline-primary btn-sm me-2">
						<i class="bi-download small">&zwnj;</i>
					</a>`
			if (file.name.toLowerCase().endsWith(".png") || 
				file.name.toLowerCase().endsWith(".jpg") ||
				file.name.toLowerCase().endsWith(".jpeg")) {
					html += `
						<a href="/testcase/${testcaseId}/evidence/${file.name}" target="_blank">
							<img class="img-fluid img-thumbnail" style="max-width: 80%" src="/testcase/${testcaseId}/evidence/${file.name}"/>
						</a>
						<input style="margin-left: 6em; width:80%;" class="form-control form-control-sm" type="text" placeholder="Caption..." value="" id="${colour.toUpperCase()}${file.name}" name="${colour.toUpperCase()}${file.name}"/>
					`
				} else {
					html += `<span class="name small">${ file.name }</span>`
				}
			$(`#evidence-${colour}`).append(html)
			$(`#${colour}files`).val("")
		}) 
	})
}

//add copy code button to testcaseKB
function copyCodeBlocks() {
  const testcaseKBModalDIV = document.getElementById('testcaseKBModal');
  const codeBlocks = testcaseKBModalDIV.querySelectorAll('code');

  codeBlocks.forEach(codeBlock => {
    const copyButton = document.createElement('button');
    copyButton.classList.add("btn", "btn-secondary", "bi-code");

    // Add click event listener to the button
    copyButton.addEventListener('click', () => {
      const text = codeBlock.textContent;
      navigator.clipboard.writeText(text)
        .then(() => {
        	showToast('Code Copied')
        })
        .catch(err => {
        	alert('Failed to copy code: '+ err)
        });
    });

    // Append the button directly within the loop
    codeBlock.parentNode.insertBefore(copyButton, codeBlock.nextSibling);
  });
}
//execute the function. Not sure where to put it else.
copyCodeBlocks()


//add toggle button to testcaseKB
function toggleVariablesinCodeBlocks() {

	const testcaseKBModalDIV = document.getElementById('testcaseKBModal');
  const codeBlocks = testcaseKBModalDIV.querySelectorAll('code');
  const assessmentid = document.getElementById('assessmentid').textContent;

  codeBlocks.forEach(codeBlock => {
    const toggleButton = document.createElement('button');
    toggleButton.classList.add("btn", "btn-secondary", "bi-toggles", "mx-sm-2");
    let isToggled = codeBlock.dataset.isToggled === 'true';

    toggleButton.addEventListener('click', () => {
      isToggled = !isToggled;

      if (isToggled) {
        const content = codeBlock.textContent;
        const regex = /\{\{([^}]+)\}\}/g; // Global flag for multiple matches
        codeBlock.dataset.originalTextContent = content;

        codeBlock.textContent = content.replace(regex, (match, variable) => {
          const value = sessionStorage.getItem(assessmentid + "_" + variable);
          return value !== null ? value : match;
        });
      } else if (codeBlock.dataset.originalTextContent) {
        codeBlock.textContent = codeBlock.dataset.originalTextContent;
      }
    });

    codeBlock.parentNode.insertBefore(toggleButton, codeBlock.nextSibling);
  });
}
//execute the function. Not sure where to put it else.
toggleVariablesinCodeBlocks()

// Function to convert local time to UTC respecting DST for past and future dates
function convertLocalToUtc(inputId, formData, fieldName) {
	const elementId = inputId.startsWith('#') ? inputId.slice(1) : inputId;
	const localTimeInput = document.getElementById(elementId);

  // Validate that the element exists
	if (!localTimeInput) {
    return false; // Indicate failure: element not found
  }

  const localValue = localTimeInput.value;

  // Handle empty input value
  if (!localValue) {
  	return true;
  }

  // Create Date object from the input value (JS interprets this as local time)
  const localDate = new Date(localValue);

  // Validate the created Date object
  //    isNaN(date.getTime()) is the standard way to check for an "Invalid Date"
  if (isNaN(localDate.getTime())) {
  	// console.error(`[convertLocalToUtc] Invalid date value "${localValue}" in input ${inputId}. Cannot convert.`);
    return false; // Indicate failure: invalid date
   }

  // Convert directly to UTC ISO string
  //    .toISOString() correctly handles the conversion from the local time
  //    represented by 'localDate' to its UTC equivalent string.
  //    Format: "YYYY-MM-DDTHH:mm:ss.sssZ"
  const utcIsoString = localDate.toISOString();

  // Slice to get the desired 'YYYY-MM-DDTHH:mm' format
  const utcFormattedString = utcIsoString.slice(0, 16);
  formData.set(fieldName, utcFormattedString);
   
  // console.log(`[convertLocalToUtc] Converted ${inputId} (value: "${localValue}") to UTC: ${utcFormattedString} for field "${fieldName}"`);

  return true;
}

// Pads a number with a leading zero if it's less than 10.
function pad(num) {
    return num < 10 ? '0' + num : num.toString();
  }

//Reads a UTC date/time string from an input field, converts it to the local time
function displayUtcAsLocal(inputSelector) {
	const inputElement = $(inputSelector);
	if (!inputElement.length) {
		console.warn(`[displayUtcAsLocal] Element not found for selector: ${inputSelector}`);
        return; // Exit if element doesn't exist
      }

      const utcValue = inputElement.val();

    // Only proceed if there is a value in the input
      if (utcValue) {
      // Ensure the Date constructor treats the string as UTC.
      // Append 'Z' if it's not already there. Handles ISO formats.
      	const utcDateString = utcValue.endsWith('Z') ? utcValue : utcValue + 'Z';
      	const dateObj = new Date(utcDateString);

      // Check if the date parsed correctly
      	if (!isNaN(dateObj.getTime())) {
        	// Get components in LOCAL time directly from the Date object
      		const year = dateObj.getFullYear();
        	const month = pad(dateObj.getMonth() + 1); // getMonth() is 0-indexed
        	const day = pad(dateObj.getDate());
        	const hours = pad(dateObj.getHours());
        	const minutes = pad(dateObj.getMinutes());

        	// Format for datetime-local input (YYYY-MM-DDTHH:mm)
        	const localDateTimeString = `${year}-${month}-${day}T${hours}:${minutes}`;

        	// Update the input field value with the local time string
        	inputElement.val(localDateTimeString);
        	// console.log(`[displayUtcAsLocal] Updated ${inputSelector}: UTC "${utcValue}" -> Local "${localDateTimeString}"`);

      } 
    } 
  }
function load_departments() {
  var url = "/study/get_departments/";
  if ($("#edu_org").val() == 0) {
    $("#department").empty();
    $("#department").append('<option value="0"></option>');
  } else {
    $.ajax({
      url: url + $("#edu_org").val(),
      success: process_department_response
    });
  }
}

function process_department_response(data) {
  $("#department").empty();
  $("#department").append('<option value="0"></option>');
  for (var key in data) {
      $("#department").append(`<option value="${key}">${data[key]}</option>`);
  }

}

$(document).ready(function() {
  if ($("#department").val() == null) {
    $("#department").empty();
    $("#department").append('<option value="0"></option>');
  }
  if ($("#edu_org").val() != 0) {
    load_departments();
  }
  $("#edu_org").change(load_departments);
});

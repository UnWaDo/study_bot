function load_groups() {
  var url = "/study/get_groups/";
  if ($("#department").val() == 0) {
    $("#group").empty();
    $("#group").append('<option value="0"></option>');
  } else {
    $.ajax({
      url: url + $("#department").val(),
      success: process_group_response
    });
  }
}

function process_group_response(data) {
  $("#group").empty();
  $("#group").append('<option value="0"></option>');
  for (var key in data) {
      $("#group").append(`<option value="${key}">${data[key]}</option>`);
  }

}

$(document).ready(function() {
  if ($("#group").val() == null) {
    $("#group").empty();
    $("#group").append('<option value="0"></option>');
  }
  if ($("#department").val() != 0) {
    load_groups();
  }
  $("#department").change(load_groups);
});

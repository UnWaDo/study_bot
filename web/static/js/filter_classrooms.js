function load_classrooms() {
  var url = "/study/get_classrooms/";
  if ($("#classroom_edu_org").val() == 0) {
    $("#classroom").empty();
    $("#classroom").append('<option value="0"></option>');
  } else {
    $.ajax({
      url: url + $("#classroom_edu_org").val(),
      success: process_classrooms_response
    });
  }
}

function process_classrooms_response(data) {
  $("#classroom").empty();
  $("#classroom").append('<option value="0"></option>');
  for (var key in data) {
      $("#classroom").append(`<option value="${key}">${data[key]}</option>`);
  }

}

$(document).ready(function() {
  if ($("#classroom").val() == null) {
    $("#classroom").empty();
    $("#classroom").append('<option value="0"></option>');
  }
  if ($("#classroom_edu_org").val() != 0) {
    load_classrooms();
  }
  $("#classroom_edu_org").change(load_classrooms);
});

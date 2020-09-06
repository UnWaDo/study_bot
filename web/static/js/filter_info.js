function filter_info() {
  var url = "/info/list/filter/";
  var filter = "";
  if (!$("#filterEx").prop("checked")) {
    filter += "e";
  }
  if ($("#doFilterDT").prop("checked")) {
    filter += "s";
    filter += $("#filterDT").val();
  }
  if (filter == "") {
    filter = "no"
  }
  $.ajax({
    url: url + filter,
    success: process_response
  });
}

function process_response(data) {
  $("#infoList").html(data);
}

function change_sign() {
  if ($("#infoExpander").text() == "Показать все") {
    $("#infoExpander").text("Скрыть все");
  } else {
    $("#infoExpander").text("Показать все");
  }
}

$(document).ready(function() {
  $("#filterInfo").click(filter_info);
  $("#infoExpander").click(change_sign);
});

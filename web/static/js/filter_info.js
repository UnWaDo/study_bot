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
  set_expiration_handler();
}

function change_sign() {
  if ($("#infoExpander").text() == "Показать все") {
    $("#infoExpander").text("Скрыть все");
  } else {
    $("#infoExpander").text("Показать все");
  }
}

function set_expiration_handler() {
  $(".unexpired").click(expire);
}

function expire() {
  $("#userPrompt").modal();
  var url = $(this).attr("href");
  $("#confirmExpiration").click(function () {
    $("#userPrompt").modal("hide");
    $.ajax({
      url: url,
      success: proccess_exp_response
    });
  });
}

function proccess_exp_response() {
  $("#filterInfo").trigger("click");
}

$(document).ready(function() {
  $("#filterInfo").click(filter_info);
  $("#infoExpander").click(change_sign);
  set_expiration_handler();
});

function count_symbols() {
  var text = $("#text").val();
  var string = "Осталось "+ (1000-text.length) +" из 1000";

  if ((text.length > 900) && (text.length <= 1000)) {
    $("#symbolsLeft").attr("class", "text-warning");
    $("#submit").removeAttr("disabled");
  } else if (text.length > 1000) {
    $("#symbolsLeft").attr("class", "text-danger");
    $("#submit").attr("disabled", true);
  } else {
    $("#symbolsLeft").attr("class", "text-muted");
    $("#submit").removeAttr("disabled");
  }
  $("#symbolsLeft").text(string);
}


$(document).ready(function() {
  $("#text").keyup(count_symbols);
});

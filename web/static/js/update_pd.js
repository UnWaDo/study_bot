function update_pd() {
  var url = window.location.href;
  var update_url = url + "/update_pd";
  $.ajax({
    url: update_url,
    success: process_response
  });
}

function process_response(data) {
  data = $.parseJSON(data);
  $("#surname").text(data.surname);
  $("#name").text(data.name);
  if (data.birth_date !== undefined) {
    $("#birth_date").text(data.birth_date);
  }
}

$(document).ready(function() {
  $("#update_pd").click(update_pd);
});

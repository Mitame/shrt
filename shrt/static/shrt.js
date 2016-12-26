API_BASE_URL = document.location + "api/";
let shrt_id = 0;
$(document).ready(function() {
  $("#mk").submit(function() {
    let url = $("#mk_url").val();
    let cur_shrt_id = shrt_id++;

    $.post(
      API_BASE_URL + "mk",
      $(this).serialize(),
      function(data) {
        if (data.ok) {
          console.log(data.url);
          $("td[data-shrt-id=" + cur_shrt_id + "]").text("").append(
            $("<td>").append($("<a>").attr("href", data.url).text(data.url))
          );
        } else {
          $("td[data-shrt-id=" + cur_shrt_id + "]").text(data.error);
        }
      }
    );

    $("#shrt_table").append(
      $("<tr>").append(
        $("<td>").append($("<a>").attr("href", url).text(url)),
        $("<td>").text("Requesting...").attr("data-shrt-id", cur_shrt_id)
      )
    );
    return false;
  });
});

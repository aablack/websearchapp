$(document).ready(function() {
    var search = function() {
        /** submit the form via ajax and set the callback function
         */
        $("#results").empty();
        var search_text = $("#search_text").val();
        var order = $("#order").val()
        if (search_text != "") {
            $("#results").append('<p>Please wait while getting search results ...</p>');
            var data = { search_text:search_text, order:order};
            var args = { type:"POST", url:"/search/", data:data, complete:results };
            $.ajax(args);
        }
        else {
            $("#results").append('<p class="error">Please enter a search term</p>');
        }
        return false;
    };

    var results = function(res, status) {
        /** Output the server response from the ajax post.
         */
        $("#results").empty();
        if (status == "success") {
            $("#results").append(res.responseText);
        }
        else {
            // the server responded with an error
            $("#results").append('<p class="error">' + res.responseText + '</p>');
        }
    };

    $("#submit").click(search);
})

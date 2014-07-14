function convert(i) {
        return ["PG", "SG", "SF", "PF", "C"][i];
}
function parseRoster(rost) {
    return ["BN", "PG", "SG", "SF", "PF", "C"].indexOf(rost);
}
$(document).ready(function()
{
    var selected = null;
    $(".mover").click(function()
    {
        var mover = this;
        console.log("yup");
        if(selected === null)
        {
            selected = $(this).parent().parent();
            clickedIsBench = $($(this).parent().parent().children("td").contents()[0]).text() === "BN";
            clickedPositions = $($(this).parent().parent().children("td").contents()[2]).text().split("|");
            clickedPosition = $($(this).parent().parent().children("td").contents()[0]).text();
            found = false;
            var check = function(i, d) {
                var rowIndex = i;
                var rowPos = $($(this).children("td").contents()[0]).text();
                var isBench = rowPos === "BN";
                var positions = $($(this).children("td").contents()[2]).text().split("|");
                var button = $(this).children('td').children("button");
                if(clickedIsBench && !isBench && $.inArray(rowPos,clickedPositions) >= 0)
                {
                    button.removeClass("btn-default");
                    button.addClass("btn-success");
                }else if(!clickedIsBench && isBench && $.inArray(clickedPosition,positions) >= 0)
                {
                    button.removeClass("btn-default");
                    button.addClass("btn-success");
                }/*else if(!clickedIsBench && !isBench && rowPos === convert(i))
                {
                    button.addClass("btn-primary");
                    button.removeClass("btn-default");
                }*/

                else if(!clickedIsBench && !isBench && $.inArray(convert(i),positions) >= 0 && $.inArray(rowPos, clickedPositions) >= 0)
                {
                    button.removeClass("btn-default");
                    button.addClass("btn-success");
                }else{
                    button.attr("disabled", "disabled");
                }
            };
            $("#players").children("tbody").children('tr').each(check);
            $(this).removeAttr("disabled");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-success");

        }else{
            var clicked = $(this).parent().parent();
            var position = clicked.children().first().text();
            var idFinder = /player(\d+)/;

            var data = JSON.stringify({
                "objects":[
                    {"roster":parseRoster(clicked.children().eq(0).text()), "resource_uri":"/service/beta/player/"+idFinder.exec(selected.attr("id"))[1]+"/"},
                    {"roster":parseRoster(selected.children().eq(0).text()), "resource_uri":"/service/beta/player/"+idFinder.exec(clicked.attr("id"))[1]+"/"},
                ]
            });
            
            $.ajax({
                url:"/service/beta/player/",
                type:"PATCH",
                contentType:"application/json",
                data:data,
                dataType:"json",
                processData:"false",
                complete: function(jqxhr, status) 
                {
                    if(jqxhr.status === 202)
                    {
                        clicked.children().eq(0).text(selected.children().first().text());
                        selected.children().eq(0).text(position);
                        var placeholder = $("<tr><td></td></tr>");
                        selected.after(placeholder);
                        
                        clicked.after(selected);
                        placeholder.replaceWith(clicked); 

                        // Success Message
                        console.log("Players properly swapped.");
                    }else{
                        // Failure Message
                        console.log("Error: players were not switched.");
                    }

                    selected = null;
                    var buttons = $("#players").children("tbody").children("tr").children("td").children("button")
                    buttons.removeAttr("disabled");
                    buttons.removeClass("btn-success");
                    buttons.addClass("btn-default");

                }
            });

            

           
        }
    });
});